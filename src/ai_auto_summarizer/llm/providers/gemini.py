"""Gemini LLM provider implementation."""

import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar
from google import genai
from pydantic import BaseModel

from ..base import LLM

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

def _convert_pydantic_to_gemini_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """Convert a Pydantic model to a Gemini-compatible schema."""
    schema = model.model_json_schema()
    
    # Convert the schema to Gemini's format
    gemini_schema = {
        "type": "object",
        "properties": {},
        "required": schema.get("required", [])
    }
    
    for field_name, field_schema in schema.get("properties", {}).items():
        field_type = field_schema.get("type")
        if field_type == "array":
            items = field_schema.get("items", {})
            if isinstance(items, dict) and "type" in items:
                gemini_schema["properties"][field_name] = {
                    "type": "array",
                    "items": {"type": items["type"]},
                    "maxItems": 10  # Limit array length to prevent overflows
                }
            elif isinstance(items, dict) and "$ref" in items:
                # Handle nested Pydantic models in arrays
                ref_type = items["$ref"].split("/")[-1]
                if ref_type in schema.get("$defs", {}):
                    nested_schema = schema["$defs"][ref_type]
                    gemini_schema["properties"][field_name] = {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                k: {"type": v.get("type", "string")}
                                for k, v in nested_schema.get("properties", {}).items()
                            }
                        },
                        "maxItems": 5  # Limit nested arrays
                    }
        elif field_type == "string":
            if "enum" in field_schema:
                gemini_schema["properties"][field_name] = {
                    "type": "string",
                    "enum": field_schema["enum"]
                }
            else:
                gemini_schema["properties"][field_name] = {
                    "type": "string",
                    "maxLength": 1000  # Limit string length
                }
        elif field_type == "integer":
            gemini_schema["properties"][field_name] = {
                "type": "number",
                "format": "int64"
            }
        elif field_type == "number":
            gemini_schema["properties"][field_name] = {
                "type": "number",
                "format": "double"
            }
        else:
            gemini_schema["properties"][field_name] = {
                "type": field_type or "string"
            }
            
    return gemini_schema

def _try_fix_json(text: str) -> str:
    """Attempt to fix truncated JSON by completing missing brackets and quotes."""
    try:
        # Try parsing as is first
        json.loads(text)
        return text
    except json.JSONDecodeError as e:
        # Get the position where the error occurred
        error_pos = e.pos if hasattr(e, 'pos') else None
        error_msg = str(e)

        if error_pos:
            # Find the last complete object before the error
            text_before_error = text[:error_pos]
            
            # Check for various truncation patterns
            patterns = [
                '"description": "',
                '"name": "',
                '"summary": "'
            ]
            
            for pattern in patterns:
                last_field_start = text_before_error.rfind(pattern)
                if last_field_start != -1:
                    # Find the last complete object before this field
                    last_complete = text_before_error[:last_field_start].rfind('"}')
                    if last_complete != -1:
                        # Keep everything up to the start of the truncated field
                        truncated = text[:last_field_start + len(pattern)] + "..."
                        
                        # Count unclosed objects and arrays
                        opens = truncated.count('{') + truncated.count('[')
                        closes = truncated.count('}') + truncated.count(']')
                        
                        # Close the current string and object
                        truncated += '"}'
                        
                        # If we're in an array of objects, close the array
                        if '"topics": [' in truncated and truncated.count('[') > truncated.count(']'):
                            truncated += ']'
                            
                        # Close any remaining open objects
                        remaining_closes = opens - closes - 1
                        if remaining_closes > 0:
                            truncated += '}' * remaining_closes
                            
                        try:
                            # Verify the fixed JSON is valid
                            json.loads(truncated)
                            return truncated
                        except:
                            continue

        # If specific fixes didn't work, try general recovery
        if "EOF" in error_msg or "Unterminated string" in error_msg:
            # Count opening and closing brackets/braces
            opens = text.count('{') + text.count('[')
            closes = text.count('}') + text.count(']')
            
            # If we have unclosed quotes, close them
            if text.count('"') % 2 == 1:
                text += '"'
            
            # Add missing closing brackets/braces
            if opens > closes:
                text += '}' * (opens - closes)
            
            try:
                json.loads(text)
                return text
            except:
                pass

        # If all recovery attempts failed, raise the original error
        raise

class GeminiLLM(LLM):
    """Gemini implementation of the LLM interface."""
    
    def __init__(self, config: Dict[str, Any], settings: Dict[str, Any]):
        """
        Initialize the Gemini LLM provider.
        
        Args:
            config: Configuration dictionary containing API key and model settings
            settings: Additional settings for the provider
        """
        super().__init__(config, settings)
        
        # Configure Gemini client
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("Gemini API key not found in config")
            
        try:
            # Initialize the client
            self.client = genai.Client(api_key=api_key)
            
            # Get model configuration
            self.model_name = config.get('model', 'gemini-pro')
            self.max_length = config.get('max_length', 2048)  # Increased max length
            self.temperature = config.get('temperature', 0.7)
            self.top_p = config.get('top_p', 0.8)
            
            # Initialize async client
            self.async_client = self.client.aio
            
            logger.info(f"Initialized Gemini client with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {str(e)}")
            raise ValueError(f"Failed to initialize Gemini client: {str(e)}")
        
    async def generate(
        self,
        prompt: str,
        response_format: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Any:
        """
        Generate a response using the Gemini model.
        
        Args:
            prompt: The input prompt
            response_format: Optional Pydantic model for structured output
            **kwargs: Additional arguments passed to the model
            
        Returns:
            Generated response, either as text or structured data
        """
        try:
            # Configure generation parameters
            config = {
                'temperature': self.temperature,
                'top_p': self.top_p,
                'max_output_tokens': self.max_length,
                'stop_sequences': ['}}}']  # Stop before potential overflow
            }
            
            # Add schema configuration if a Pydantic model is provided
            if response_format and issubclass(response_format, BaseModel):
                schema = _convert_pydantic_to_gemini_schema(response_format)
                config.update({
                    'response_mime_type': 'application/json',
                    'response_schema': schema
                })
                logger.debug(f"Using schema: {schema}")
            
            # Generate response using async client
            response = await self.async_client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
            
            # If a response format is specified, parse the JSON response
            if response_format:
                try:
                    # Try to fix any truncated JSON
                    fixed_json = _try_fix_json(response.text)
                    # Parse the response text as JSON and validate with Pydantic
                    return response_format.model_validate_json(fixed_json)
                except Exception as e:
                    logger.error(f"Error parsing Gemini response: {str(e)}")
                    logger.error(f"Raw response: {response.text}")
                    raise
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {str(e)}")
            raise
            
    async def chat(
        self,
        messages: list[Dict[str, str]],
        response_format: Optional[Type[T]] = None,
        **kwargs: Any
    ) -> Any:
        """
        Have a chat conversation using the Gemini model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            response_format: Optional Pydantic model for structured output
            **kwargs: Additional arguments passed to the model
            
        Returns:
            Generated response, either as text or structured data
        """
        try:
            # Configure generation parameters
            config = {
                'temperature': self.temperature,
                'top_p': self.top_p,
                'max_output_tokens': self.max_length,
                'stop_sequences': ['}}}']  # Stop before potential overflow
            }
            
            # Add schema configuration if a Pydantic model is provided
            if response_format and issubclass(response_format, BaseModel):
                schema = _convert_pydantic_to_gemini_schema(response_format)
                config.update({
                    'response_mime_type': 'application/json',
                    'response_schema': schema
                })
                logger.debug(f"Using schema for chat: {schema}")
            
            # Create a chat session using async client
            chat = await self.async_client.chats.create(model=self.model_name)
            
            # Process each message in the conversation
            for message in messages:
                role = message['role']
                content = message['content']
                
                if role == 'user':
                    response = await chat.send_message(
                        content=content,
                        config=config
                    )
                
            if not response.text:
                raise ValueError("Empty response from Gemini chat")
            
            # If a response format is specified, parse the JSON response
            if response_format:
                try:
                    # Try to fix any truncated JSON
                    fixed_json = _try_fix_json(response.text)
                    # Parse the response text as JSON and validate with Pydantic
                    return response_format.model_validate_json(fixed_json)
                except Exception as e:
                    logger.error(f"Error parsing Gemini chat response: {str(e)}")
                    logger.error(f"Raw response: {response.text}")
                    raise
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in Gemini chat: {str(e)}")
            raise 
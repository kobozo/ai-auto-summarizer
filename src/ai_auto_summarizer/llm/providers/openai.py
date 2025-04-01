"""OpenAI LLM provider implementation."""

import json
import logging
from typing import Any, Dict, Optional, Union

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ai_auto_summarizer.llm.base import LLM

logger = logging.getLogger(__name__)

# Default schema for summarization
DEFAULT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A concise summary of the content"
        }
    },
    "required": ["summary"]
}

class OpenAILLM(LLM):
    """OpenAI implementation of the LLM interface."""
    
    def __init__(self, config: Dict[str, Any], settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the OpenAI LLM provider.
        
        Args:
            config: Dictionary containing OpenAI-specific configuration:
                - model: Model to use (e.g., "gpt-4-turbo")
                - max_length: Maximum length of generated text
            settings: Optional dictionary containing OpenAI settings:
                - api_key: OpenAI API key
        """
        super().__init__(config, settings)
        
        # Get API key from settings or config
        api_key = self.settings.get('api_key') or self.config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4-turbo')
        self.max_length = self.config.get('max_length', 500)
        
    async def generate(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate structured JSON output using OpenAI's chat completion API.
        
        Args:
            prompt: The prompt to send to the model
            schema: JSON schema that defines the structure of the expected output.
                   If None, uses the default summarization schema.
            **kwargs: Additional parameters to pass to the API
                - temperature: Controls randomness (0.0 to 2.0)
                - top_p: Controls diversity via nucleus sampling
                - max_tokens: Maximum tokens to generate
                
        Returns:
            Generated response as a JSON object matching the provided schema
            
        Raises:
            Exception: If there's an error during generation
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            return await self._complete(messages, schema or DEFAULT_SCHEMA, **kwargs)
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise
            
    async def chat(self, messages: list[Dict[str, str]], schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Have a chat conversation using OpenAI's chat completion API with JSON output.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            schema: JSON schema that defines the structure of the expected output.
                   If None, uses the default summarization schema.
            **kwargs: Additional parameters to pass to the API
                - temperature: Controls randomness (0.0 to 2.0)
                - top_p: Controls diversity via nucleus sampling
                - max_tokens: Maximum tokens to generate
                
        Returns:
            Generated response as a JSON object matching the provided schema
            
        Raises:
            Exception: If there's an error during chat
        """
        try:
            return await self._complete(messages, schema or DEFAULT_SCHEMA, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in chat with OpenAI: {str(e)}")
            raise
            
    async def _complete(self, messages: list[Dict[str, str]], schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Internal method to make a chat completion request with JSON mode."""
        try:
            # Add system message for JSON mode if not present
            if not any(msg.get("role") == "system" for msg in messages):
                messages.insert(0, {
                    "role": "system",
                    "content": "You are a powerful text analysis system specializing in concise summarization. Focus on identifying key points while preserving critical information and overall context."
                })
            
            # Prepare the API call parameters
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_length),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 1.0),
                "response_format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "strict": True,
                        **schema
                    }
                }
            }
            
            # Make the API call
            response: ChatCompletion = await self.client.chat.completions.create(**params)
            
            # Extract and parse the JSON response
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                if content:
                    return json.loads(content)
                
            return {"summary": ""}  # Default empty response matching schema
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            raise 
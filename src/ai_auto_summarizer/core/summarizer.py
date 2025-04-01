"""Core functionality for summarizing content using LLMs."""

import logging
from typing import Any, Dict, List, Optional

from ..llm import LLMRegistry
from ..llm.prompts import create_content_analysis_prompt
from ..models import ContentSummary

logger = logging.getLogger(__name__)

class Summarizer:
    """Handles summarization of content using configured LLM provider."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the summarizer with configuration.
        
        Args:
            config: Application configuration containing LLM settings
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        
        # Initialize LLM provider
        provider_type = self.llm_config.get('provider')
        if not provider_type:
            raise ValueError("LLM provider not specified in config")
            
        self.llm = LLMRegistry.create_provider(
            provider_type,
            self.llm_config,
            {}  # No additional settings needed as API key is in config
        )
        
    async def process_content(self, content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of content items, generating summaries for those with transcripts.
        
        Args:
            content_items: List of content items from sources
            
        Returns:
            List of content items with added summaries where available
        """
        processed_items = []
        
        for item in content_items:
            if transcript := item.get('transcript'):
                try:
                    summary_response = await self._summarize_transcript(
                        transcript=transcript,
                        title=item.get('title', ''),
                        description=item.get('description', ''),
                        duration=item.get('duration')
                    )
                    # Update item with all summary fields
                    item.update(summary_response.model_dump(exclude_none=True))
                    logger.info(f"Generated summary for content: {item.get('title', 'Untitled')}")
                except Exception as e:
                    logger.error(f"Error summarizing content {item.get('id')}: {str(e)}")
                    item['summary'] = ''
            else:
                item['summary'] = ''
                
            processed_items.append(item)
            
        return processed_items
        
    async def _summarize_transcript(
        self,
        transcript: str,
        title: str = '',
        description: str = '',
        duration: Optional[float] = None
    ) -> ContentSummary:
        """
        Generate a summary for a transcript using the configured LLM.
        
        Args:
            transcript: The transcript text to summarize
            title: Optional title for context
            description: Optional description for context
            duration: Optional duration in seconds
            
        Returns:
            ContentSummary object containing the structured summary
        """
        # Generate prompt using template
        prompt = create_content_analysis_prompt(
            transcript=transcript,
            title=title or None,
            description=description or None
        )
        
        try:
            # Use the Pydantic model as the response format
            response = await self.llm.generate(prompt, response_format=ContentSummary)
            
            # Add duration if available
            if duration is not None:
                response.duration_minutes = duration / 60
                
            return response
        except Exception as e:
            logger.error(f"Error in LLM generation: {str(e)}")
            raise 
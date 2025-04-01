from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

class Source(ABC):
    """Abstract base class for content sources."""
    
    def __init__(self, config: Dict[str, Any], settings: Optional[Dict[str, Any]] = None):
        """
        Initialize a source with its configuration and optional settings.
        
        Args:
            config: Dictionary containing the source-specific configuration
                (e.g., for YouTube: channel ID, name, type, etc.)
            settings: Optional dictionary containing provider-specific settings
                (e.g., for YouTube: API keys)
        """
        self.config = config
        self.settings = settings or {}
        
    @abstractmethod
    async def get_content(self, from_date: datetime) -> List[Dict[str, Any]]:
        """
        Retrieve content from the source since the given date.
        
        Args:
            from_date: Datetime object indicating when to fetch content from
            
        Returns:
            List of dictionaries containing the content items with their metadata.
            Each item should include at minimum:
                - id: Unique identifier for the content
                - title: Content title
                - description: Content description
                - published_at: Publication date
                - url: URL to the original content
                - source_type: Type of source (e.g., 'youtube', 'rss', etc.)
        """
        pass 
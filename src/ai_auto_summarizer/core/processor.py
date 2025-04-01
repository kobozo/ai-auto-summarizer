from typing import Dict, Any, List
from datetime import datetime, timedelta
import re

from ..sources import SourceRegistry, Source

class ContentProcessor:
    """Core processor for handling content from various sources."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the content processor.
        
        Args:
            config: Application configuration containing sources and API keys
        """
        self.config = config
        self.sources: List[Source] = []
        self._load_sources()
    
    def _load_sources(self) -> None:
        """Load and initialize all enabled sources from the configuration."""
        for source_type, source_configs in self.config.get('sources', {}).items():
            # Get source-specific settings based on type
            settings = self._get_source_settings(source_type)
            
            # Initialize each source of this type
            for source_config in source_configs:
                if source_config.get('enabled', True):
                    try:
                        source = SourceRegistry.create_source(
                            source_type,
                            source_config,
                            settings
                        )
                        self.sources.append(source)
                    except KeyError as e:
                        print(f"Warning: Skipping unsupported source type '{source_type}': {str(e)}")
                    except Exception as e:
                        print(f"Error initializing {source_type} source '{source_config.get('name', 'unknown')}': {str(e)}")
    
    def _get_source_settings(self, source_type: str) -> Dict[str, Any]:
        """
        Get settings for a specific source type.
        
        Args:
            source_type: The type of source (e.g., 'youtube')
            
        Returns:
            Dictionary containing source-specific settings
        """
        if source_type == 'youtube':
            return {
                'api_key': self.config.get('api_keys', {}).get('youtube')
            }
        
        # For other source types, return empty settings
        return {}
    
    def _parse_time_period(self, time_period: str) -> timedelta:
        """
        Parse a time period string into a timedelta.
        
        Args:
            time_period: String in format "Xd" where X is number of days
            
        Returns:
            timedelta object
            
        Raises:
            ValueError: If time_period format is invalid
        """
        match = re.match(r'^(\d+)d$', time_period)
        if not match:
            raise ValueError(f"Invalid time period format: {time_period}. Expected format: '7d', '14d', etc.")
            
        days = int(match.group(1))
        return timedelta(days=days)
    
    async def process_sources(self) -> List[Dict[str, Any]]:
        """
        Process all enabled sources to get their content.
        Each source will be queried based on its configured time_period.
        
        Returns:
            List of content items from all sources
        """
        all_content = []
        
        for source in self.sources:
            try:
                print(f"Processing source: {source.config.get('name', 'unknown')}")
                
                # Get source-specific time period or fall back to default
                time_period = source.config.get('time_period')
                if not time_period:
                    # Try to get default from source type settings
                    source_type = source.config.get('source_type', 'youtube')  # Default to youtube for backward compatibility
                    time_period = self.config.get(source_type, {}).get('time_period', '1d')
                
                # Calculate from_date based on time_period
                try:
                    delta = self._parse_time_period(time_period)
                    from_date = datetime.now() - delta
                except ValueError as e:
                    print(f"Warning: Invalid time period '{time_period}' for source {source.config.get('name')}: {str(e)}")
                    print("Falling back to 1 day")
                    from_date = datetime.now() - timedelta(days=1)
                
                content = await source.get_content(from_date)
                all_content.extend(content)
            except Exception as e:
                print(f"Error processing source {source.__class__.__name__}: {str(e)}")
        
        # Sort content by published date, newest first
        all_content.sort(key=lambda x: x['published_at'], reverse=True)
        
        return all_content 
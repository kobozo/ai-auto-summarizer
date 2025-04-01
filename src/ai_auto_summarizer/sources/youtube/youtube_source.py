from datetime import datetime
from typing import Any, Dict, List
import isodate

from ..source import Source
from .youtube_client import YouTubeClient

class YouTubeSource(Source):
    """YouTube implementation of the Source abstract class."""
    
    def __init__(self, config: Dict[str, Any], settings: Dict[str, Any]):
        """
        Initialize a YouTube source for a single channel/user.
        
        Args:
            config: Dictionary containing the source configuration including:
                - id: Channel ID or username
                - name: Display name for the channel
                - type: Either 'channel' or 'user'
                - last_checked: Last time content was fetched (can be null)
                - enabled: Whether this source is active
                - time_period: How far back to check for content
            settings: Dictionary containing YouTube specific settings including:
                - api_key: YouTube Data API key
        """
        super().__init__(config)
        if not settings.get('api_key'):
            raise ValueError("YouTube API key is required in settings")
        
        self.client = YouTubeClient(settings['api_key'])
        
    async def get_content(self, from_date: datetime) -> List[Dict[str, Any]]:
        """
        Retrieve videos and their transcripts from the YouTube channel since the given date.
        
        Args:
            from_date: Datetime object indicating when to fetch content from
            
        Returns:
            List of dictionaries containing:
                - id: Video ID
                - title: Video title
                - description: Video description
                - published_at: Publication date
                - channel_id: YouTube channel ID
                - channel_title: YouTube channel name
                - url: Full URL to the video
                - duration: Video duration in seconds
                - transcript: Video transcript if available
                - source_type: Always "youtube"
                - statistics: View count, like count, etc.
        """
        # Get videos from the channel
        videos = self.client.get_channel_videos(
            channel_id=self.config['id'],
            max_results=50,  # Adjust based on config if needed
            published_after=from_date
        )
        
        all_content = []
        for video in videos:
            # Get video duration
            duration = isodate.parse_duration(
                video['contentDetails']['duration']
            ).total_seconds()
            
            # Get transcript if available
            transcript = self.client.get_transcript(video['id'])
            
            content_item = {
                'id': video['id'],
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'published_at': video['snippet']['publishedAt'],
                'channel_id': video['snippet']['channelId'],
                'channel_title': video['snippet']['channelTitle'],
                'url': f'https://www.youtube.com/watch?v={video["id"]}',
                'duration': duration,
                'transcript': transcript,
                'source_type': 'youtube',
                'statistics': video.get('statistics', {})
            }
            
            all_content.append(content_item)
            
        return all_content 
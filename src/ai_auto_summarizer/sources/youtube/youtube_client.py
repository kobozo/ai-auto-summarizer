"""YouTube API client for fetching videos and channels."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging
import requests
import html
import re
import xml.etree.ElementTree as ET

class YouTubeClient:
    """Client for interacting with the YouTube API."""
    
    def __init__(self, api_key: str):
        """Initialize the YouTube client.
        
        Args:
            api_key: YouTube API key
        """
        if not api_key:
            raise ValueError("YouTube API key is required")
            
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.logger = logging.getLogger(__name__)
            
    def resolve_username_to_channel_id(self, username: str) -> Optional[str]:
        """Resolve a YouTube username or handle to a channel ID.
        
        Args:
            username: YouTube username (with or without @ prefix)
            
        Returns:
            Channel ID if found, None otherwise
        """
        # Remove @ prefix if present
        if username.startswith('@'):
            username = username[1:]
            
        # Try to find the channel by username
        response = self._make_request(
            "channels",
            {
                "forUsername": username,
                "part": "id",
                "maxResults": 1
            }
        )
        
        if response.get("items"):
            return response["items"][0]["id"]
        
        # If that fails, try to find using search
        search_response = self._make_request(
            "search",
            {
                "q": username,
                "type": "channel",
                "part": "id",
                "maxResults": 1
            }
        )
        
        if search_response.get("items"):
            return search_response["items"][0]["id"]["channelId"]
            
        self.logger.warning(f"Could not resolve username: {username}")
        return None
            
    def get_channel_videos(
        self, 
        channel_id: str, 
        max_results: int = 10, 
        published_after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get videos from a channel.
        
        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to return
            published_after: Only return videos published after this datetime
            
        Returns:
            List of video metadata
        """
        # Check if this is a username/handle (starts with @)
        if channel_id.startswith('@'):
            self.logger.info(f"Resolving YouTube handle: {channel_id}")
            resolved_id = self.resolve_username_to_channel_id(channel_id)
            if not resolved_id:
                self.logger.warning(f"Could not resolve YouTube handle: {channel_id}")
                return []
            channel_id = resolved_id
            self.logger.info(f"Resolved to channel ID: {channel_id}")
                
        # First, get the channel's uploads playlist ID
        channel_response = self._make_request(
            "channels",
            {
                "id": channel_id,
                "part": "contentDetails",
                "maxResults": 1
            }
        )
        
        if not channel_response.get("items"):
            self.logger.warning(f"No channel found with ID: {channel_id}")
            return []
            
        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Then get videos from that playlist
        return self.get_playlist_videos(uploads_playlist_id, max_results, published_after)
        
    def get_playlist_videos(
        self, 
        playlist_id: str, 
        max_results: int = 10, 
        published_after: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get videos from a playlist.
        
        Args:
            playlist_id: YouTube playlist ID
            max_results: Maximum number of videos to return
            published_after: Only return videos published after this datetime
            
        Returns:
            List of video metadata
        """
        params = {
            "playlistId": playlist_id,
            "part": "snippet,contentDetails",
            "maxResults": min(max_results, 50)  # API limit is 50
        }
        
        if published_after:
            # YouTube API requires UTC timezone in ISO 8601 format
            if published_after.tzinfo is None:
                api_datetime = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                api_datetime = published_after.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                
            params["publishedAfter"] = api_datetime
            self.logger.info(f"Filtering for videos published after: {api_datetime}")
            
        playlist_response = self._make_request("playlistItems", params)
        
        videos = []
        for item in playlist_response.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            
            # Get the publish date from the snippet
            snippet = item.get("snippet", {})
            published_at_str = snippet.get("publishedAt")
            
            # Skip if we can't determine publish date or if it's before the filter date
            if published_after and published_at_str:
                try:
                    # Convert to datetime for comparison
                    if published_at_str.endswith("Z"):
                        published_at_str = published_at_str.replace("Z", "+00:00")
                    
                    item_published_at = datetime.fromisoformat(published_at_str)
                    
                    # Convert item_published_at to naive datetime for comparison if needed
                    if item_published_at.tzinfo is not None and published_after.tzinfo is None:
                        item_published_at = item_published_at.replace(tzinfo=None)
                    
                    # Skip if this video was published before our filter date
                    if item_published_at < published_after:
                        self.logger.debug(f"Skipping video {video_id}, published at {item_published_at} before filter {published_after}")
                        continue
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Error parsing publish date '{published_at_str}': {e}")
            
            # Get more details about the video
            video_details = self.get_video_details(video_id)
            if video_details:
                videos.append(video_details)
                
            if len(videos) >= max_results:
                break
                
        self.logger.info(f"Found {len(videos)} videos in playlist matching criteria")
        return videos
        
    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video metadata or None if not found
        """
        video_response = self._make_request(
            "videos",
            {
                "id": video_id,
                "part": "snippet,contentDetails,statistics"
            }
        )
        
        if not video_response.get("items"):
            self.logger.warning(f"No video found with ID: {video_id}")
            return None
            
        return video_response["items"][0]
        
    def get_video_captions(self, video_id: str) -> Optional[str]:
        """Get captions for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Caption text if available, None otherwise
        """
        captions_response = self._make_request(
            "captions",
            {
                "videoId": video_id,
                "part": "snippet"
            }
        )
        
        if not captions_response.get("items"):
            self.logger.debug(f"No captions found for video: {video_id}")
            return None
            
        # Prefer manual English captions
        caption_id = None
        for caption in captions_response["items"]:
            if caption["snippet"]["language"] == "en":
                if not caption["snippet"].get("trackKind") == "ASR":
                    caption_id = caption["id"]
                    break
                    
        # If no manual English captions, try auto-generated
        if not caption_id:
            for caption in captions_response["items"]:
                if caption["snippet"]["language"] == "en":
                    caption_id = caption["id"]
                    break
                    
        if not caption_id:
            self.logger.debug(f"No English captions found for video: {video_id}")
            return None
            
        # Download the captions
        caption_response = self._make_request(
            f"captions/{caption_id}",
            {
                "tfmt": "srt"
            }
        )
        
        return caption_response.get("text")
        
    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a video using multiple fallback methods:
        1. YouTube's timedtext API
        2. yt-dlp if available
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript text if available, None otherwise
        """
        # First try using the timedtext API
        try:
            transcript = self._get_transcript_with_timedtext(video_id)
            if transcript:
                return transcript
        except Exception as e:
            self.logger.warning(f"Error getting transcript with timedtext API: {str(e)}")
            
        # Then try using yt-dlp if available
        try:
            import yt_dlp
            transcript = self._get_transcript_with_yt_dlp(video_id)
            if transcript:
                return transcript
        except ImportError:
            self.logger.debug("yt-dlp not available")
        except Exception as e:
            self.logger.warning(f"Error getting transcript with yt-dlp: {str(e)}")
            
        return None
        
    def _get_transcript_with_timedtext(self, video_id: str) -> Optional[str]:
        """Get transcript using YouTube's timedtext API."""
        # First, try to get the list of available captions
        captions_url = f"https://www.youtube.com/api/timedtext?type=list&v={video_id}"
        
        response = requests.get(captions_url)
        response.raise_for_status()
        
        # Check if we got a non-empty response
        if not response.text.strip():
            self.logger.debug(f"No captions available for video: {video_id}")
            return None
            
        # Parse the XML response to find caption tracks
        root = ET.fromstring(response.text)
        
        # Look for English captions first
        track = None
        for track_elem in root.findall('./track'):
            lang_code = track_elem.get('lang_code', '')
            if lang_code.startswith('en'):
                track = track_elem
                break
                
        # If no English captions, use the first available track
        if track is None and len(root) > 0:
            track = root.find('./track')
            
        if track is not None:
            track_name = track.get('name', '')
            lang_code = track.get('lang_code', '')
            
            # Get the actual captions
            transcript_url = f"https://www.youtube.com/api/timedtext?lang={lang_code}&v={video_id}"
            if track_name:
                transcript_url += f"&name={track_name}"
                
            response = requests.get(transcript_url)
            response.raise_for_status()
            
            # Check if we got a non-empty response
            if not response.text.strip():
                self.logger.debug(f"Empty transcript response for video: {video_id}")
                return None
                
            # Parse the XML captions
            root = ET.fromstring(response.text)
            transcript = ""
            
            for text_elem in root.findall('./text'):
                if text_elem.text:
                    transcript += html.unescape(text_elem.text) + " "
                    
            return transcript.strip() if transcript else None
            
        return None
        
    def _get_transcript_with_yt_dlp(self, video_id: str) -> Optional[str]:
        """Get transcript using yt-dlp."""
        import yt_dlp
        import tempfile
        import os
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Configure yt-dlp to download subtitles
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'outtmpl': os.path.join(temp_dir, 'subtitles'),
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            # Check for subtitle files
            subtitle_files = [
                f for f in os.listdir(temp_dir) 
                if f.endswith('.vtt') or f.endswith('.srt')
            ]
            
            if subtitle_files:
                subtitle_path = os.path.join(temp_dir, subtitle_files[0])
                return self._parse_subtitle_file(subtitle_path)
                
        except Exception as e:
            self.logger.warning(f"Error getting subtitles with yt-dlp: {str(e)}")
            
        finally:
            # Clean up temp directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
                
        return None
        
    def _parse_subtitle_file(self, file_path: str) -> str:
        """Parse subtitle file to extract text."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if file_path.endswith('.vtt'):
            # Parse WebVTT format
            # Remove header
            if content.startswith('WEBVTT'):
                content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
                
            # Remove timestamps and speaker information
            lines = []
            for line in content.split('\n'):
                # Skip timestamp lines and empty lines
                if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}', line) or line.strip() == '':
                    continue
                # Skip lines that only contain speaker names like ">> SPEAKER:"
                if re.match(r'^\s*>>\s*[A-Z\s]+:', line):
                    continue
                    
                lines.append(line)
                
            return ' '.join(lines)
            
        elif file_path.endswith('.srt'):
            # Parse SRT format
            # Remove indices and timestamps
            text_only = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
            # Remove extra newlines
            text_only = re.sub(r'\n\n+', '\n', text_only)
            
            return text_only.replace('\n', ' ')
            
        return content
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the YouTube API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response
            
        Raises:
            ValueError: If the API returns an error
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params
        params["key"] = self.api_key
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"YouTube API request failed: {str(e)}")
            if response.status_code == 403:
                self.logger.error("API key may be invalid or quota exceeded")
            raise ValueError(f"YouTube API request failed: {str(e)}") 
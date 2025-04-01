from .youtube_source import YouTubeSource
from ..registry import SourceRegistry

# Register the YouTube source implementation
SourceRegistry.register('youtube', YouTubeSource)

__all__ = ['YouTubeSource']

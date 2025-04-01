from .source import Source
from .registry import SourceRegistry

__all__ = ['Source', 'SourceRegistry']

# Import all source implementations to ensure they are registered
from . import youtube

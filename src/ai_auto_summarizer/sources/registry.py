from typing import Dict, Type

from .source import Source

class SourceRegistry:
    """Registry for mapping source types to their implementations."""
    
    _sources: Dict[str, Type[Source]] = {}
    
    @classmethod
    def register(cls, source_type: str, source_class: Type[Source]) -> None:
        """
        Register a source implementation for a given type.
        
        Args:
            source_type: String identifier for the source type (e.g., 'youtube')
            source_class: The Source class implementation
        """
        cls._sources[source_type] = source_class
    
    @classmethod
    def get_source_class(cls, source_type: str) -> Type[Source]:
        """
        Get the source implementation for a given type.
        
        Args:
            source_type: String identifier for the source type (e.g., 'youtube')
            
        Returns:
            The Source class implementation
            
        Raises:
            KeyError: If no implementation is registered for the given type
        """
        if source_type not in cls._sources:
            raise KeyError(f"No source implementation registered for type: {source_type}")
        return cls._sources[source_type]
    
    @classmethod
    def create_source(cls, source_type: str, config: dict, settings: dict) -> Source:
        """
        Create a source instance for a given type.
        
        Args:
            source_type: String identifier for the source type (e.g., 'youtube')
            config: Source-specific configuration
            settings: Provider-specific settings
            
        Returns:
            An instance of the appropriate Source implementation
            
        Raises:
            KeyError: If no implementation is registered for the given type
        """
        source_class = cls.get_source_class(source_type)
        return source_class(config, settings) 
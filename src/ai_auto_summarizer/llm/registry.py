"""Registry for LLM providers."""

from typing import Dict, Type

from ai_auto_summarizer.llm.base import LLM

class LLMRegistry:
    """Registry for mapping LLM types to their implementations."""
    
    _providers: Dict[str, Type[LLM]] = {}
    
    @classmethod
    def register(cls, provider_type: str, provider_class: Type[LLM]) -> None:
        """
        Register an LLM implementation for a given type.
        
        Args:
            provider_type: String identifier for the provider type (e.g., 'openai', 'gemini')
            provider_class: The LLM class implementation
        """
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get_provider_class(cls, provider_type: str) -> Type[LLM]:
        """
        Get the LLM implementation for a given type.
        
        Args:
            provider_type: String identifier for the provider type (e.g., 'openai', 'gemini')
            
        Returns:
            The LLM class implementation
            
        Raises:
            KeyError: If no implementation is registered for the given type
        """
        if provider_type not in cls._providers:
            raise KeyError(f"No LLM implementation registered for type: {provider_type}")
        return cls._providers[provider_type]
    
    @classmethod
    def create_provider(cls, provider_type: str, config: dict, settings: dict) -> LLM:
        """
        Create an LLM provider instance for a given type.
        
        Args:
            provider_type: String identifier for the provider type (e.g., 'openai', 'gemini')
            config: Provider-specific configuration
            settings: Provider-specific settings
            
        Returns:
            An instance of the appropriate LLM implementation
            
        Raises:
            KeyError: If no implementation is registered for the given type
        """
        provider_class = cls.get_provider_class(provider_type)
        return provider_class(config, settings) 
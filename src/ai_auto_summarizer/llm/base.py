"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class LLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any], settings: Optional[Dict[str, Any]] = None):
        """
        Initialize an LLM provider with its configuration and optional settings.
        
        Args:
            config: Dictionary containing the provider-specific configuration
                (e.g., for OpenAI: model, temperature, etc.)
            settings: Optional dictionary containing provider-specific settings
                (e.g., for OpenAI: API key)
        """
        self.config = config
        self.settings = settings or {}
        
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If there's an error during generation
        """
        pass
        
    @abstractmethod
    async def chat(self, messages: list[Dict[str, str]], **kwargs) -> str:
        """
        Have a chat conversation with the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response from the LLM
            
        Raises:
            Exception: If there's an error during chat
        """
        pass 
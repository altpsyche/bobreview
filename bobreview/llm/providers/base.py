"""
Abstract base class for LLM providers.

All LLM providers must inherit from BaseLLMProvider and implement
the required methods for making API calls.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider call."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All providers must implement:
    - call(): Make a single LLM call
    - name: Provider identifier
    - default_model: Default model for this provider
    - env_key_name: Environment variable name for API key
    """
    
    @abstractmethod
    def call(
        self,
        prompt: str,
        config: LLMProviderConfig,
        max_retries: int = 3
    ) -> str:
        """
        Make a single LLM call.
        
        Parameters:
            prompt: The prompt to send to the LLM
            config: Provider configuration (model, temperature, etc.)
            max_retries: Maximum retry attempts for rate limits
        
        Returns:
            The LLM response text
        
        Raises:
            RuntimeError: If the API call fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for display and configuration."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model to use if none specified."""
        pass
    
    @property
    @abstractmethod
    def env_key_name(self) -> str:
        """Environment variable name for the API key."""
        pass
    
    @property
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key. Override for local providers."""
        return True
    
    def get_api_key(self, config: LLMProviderConfig) -> Optional[str]:
        """
        Get API key from config or environment.
        
        Parameters:
            config: Provider configuration
        
        Returns:
            API key string or None
        """
        return config.api_key or os.getenv(self.env_key_name)
    
    def validate_config(self, config: LLMProviderConfig) -> None:
        """
        Validate configuration before making a call.
        
        Parameters:
            config: Provider configuration
        
        Raises:
            RuntimeError: If configuration is invalid
        """
        if self.requires_api_key and not self.get_api_key(config):
            raise RuntimeError(
                f"{self.name} API key not found. "
                f"Set {self.env_key_name} environment variable or use --llm-api-key"
            )

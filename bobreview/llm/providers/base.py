"""
Abstract base class for LLM providers.

All LLM providers must inherit from BaseLLMProvider and implement
the required methods for making API calls.
"""

import os
import re
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


def clean_llm_response(response: str) -> str:
    """
    Strip Markdown code fences from LLM responses.
    
    Removes Markdown-style fenced code blocks and surrounding whitespace from an LLM response.
    
    Parameters:
        response (str): Text produced by an LLM that may contain Markdown code fences (```).
    
    Returns:
        str: The input text with Markdown fenced code blocks removed or unwrapped and leading/trailing whitespace trimmed.
    """
    response = re.sub(r'^[ \t]*```[^\n]*\n?', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n?[ \t]*```\s*$', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    return response.strip()


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
        Perform a single call to the provider's LLM using the given prompt and configuration.
        
        Parameters:
            prompt (str): The prompt to send to the LLM.
            config (LLMProviderConfig): Provider configuration (model, temperature, authentication, extra params).
            max_retries (int): Maximum number of retry attempts for transient failures such as rate limits.
        
        Returns:
            The LLM response text.
        
        Raises:
            RuntimeError: If the API call fails after the configured retries.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider display name used for configuration and user interfaces.
        
        Returns:
            provider_name (str): Human-readable identifier for the LLM provider.
        """
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """
        Default model name for the provider.
        
        Returns:
            The provider's default model name.
        """
        pass
    
    @property
    @abstractmethod
    def env_key_name(self) -> str:
        """Environment variable name for the API key."""
        pass
    
    @property
    def requires_api_key(self) -> bool:
        """
        Indicates whether the provider requires an API key.
        
        Returns:
            `true` if an API key is required, `false` otherwise.
        """
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
        Validate the provided LLMProviderConfig for use with this provider.
        
        Checks that an API key is available when this provider requires one and raises a RuntimeError if not.
        
        Parameters:
            config: The LLMProviderConfig to validate.
        
        Raises:
            RuntimeError: If this provider requires an API key but none is found; the error message indicates the provider name and suggests setting the provider's environment variable or using the `--llm-api-key` flag.
        """
        if self.requires_api_key and not self.get_api_key(config):
            raise RuntimeError(
                f"{self.name} API key not found. "
                f"Set {self.env_key_name} environment variable or use --llm-api-key"
            )
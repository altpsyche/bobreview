"""
LLM provider factory.

Provides registration and retrieval of LLM providers by name.
"""

from typing import Dict, Type, List, Optional, Any

from .base import BaseLLMProvider


# Global registry of providers
_PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {}


def register_provider(name: str, provider_class: Type[BaseLLMProvider]) -> None:
    """
    Register a provider class under the given name in the global provider registry.
    
    Parameters:
        name: The registry key for the provider (e.g., "openai", "anthropic").
        provider_class: The provider class (a subclass of `BaseLLMProvider`) to register.
    
    Raises:
        ValueError: If a provider is already registered under `name`.
    """
    if name in _PROVIDERS:
        raise ValueError(f"Provider '{name}' is already registered")
    _PROVIDERS[name] = provider_class


def get_provider(name: str) -> BaseLLMProvider:
    """
    Return a registered LLM provider instance for the given provider name.
    
    Parameters:
        name (str): The registered provider name (e.g., "openai", "anthropic", "ollama").
    
    Returns:
        BaseLLMProvider: An instance of the provider class registered under `name`.
    
    Raises:
        ValueError: If no provider is registered under `name`.
    """
    if name not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown LLM provider: '{name}'. Available providers: {available}"
        )
    return _PROVIDERS[name]()


def list_providers() -> List[str]:
    """
    Return a sorted list of registered provider names.
    
    Returns:
        Sorted list of registered provider names.
    """
    return sorted(_PROVIDERS.keys())


def get_provider_info(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve basic metadata for a registered LLM provider by name.
    
    Parameters:
        name: The provider name to look up.
    
    Returns:
        A dictionary with keys "name", "default_model", "env_key_name", and "requires_api_key" containing the provider's metadata, or `None` if the provider is not registered.
    """
    if name not in _PROVIDERS:
        return None
    
    provider = _PROVIDERS[name]()
    return {
        "name": provider.name,
        "default_model": provider.default_model,
        "env_key_name": provider.env_key_name,
        "requires_api_key": provider.requires_api_key,
    }


# Register built-in providers
def _register_builtin_providers():
    """Register all built-in providers."""
    from .openai import OpenAIProvider
    from .anthropic import AnthropicProvider
    from .ollama import OllamaProvider
    
    register_provider("openai", OpenAIProvider)
    register_provider("anthropic", AnthropicProvider)
    register_provider("ollama", OllamaProvider)


# Auto-register on module import
_register_builtin_providers()
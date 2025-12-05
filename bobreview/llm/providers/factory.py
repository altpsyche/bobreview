"""
LLM provider factory.

Provides registration and retrieval of LLM providers by name.
"""

from typing import Dict, Type, List, Optional

from .base import BaseLLMProvider


# Global registry of providers
_PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {}


def register_provider(name: str, provider_class: Type[BaseLLMProvider]) -> None:
    """
    Register an LLM provider.
    
    Parameters:
        name: Provider name (e.g., 'openai', 'anthropic')
        provider_class: Provider class (not instance)
    
    Raises:
        ValueError: If provider with same name already registered
    """
    if name in _PROVIDERS:
        raise ValueError(f"Provider '{name}' is already registered")
    _PROVIDERS[name] = provider_class


def get_provider(name: str) -> BaseLLMProvider:
    """
    Get an LLM provider instance by name.
    
    Parameters:
        name: Provider name
    
    Returns:
        Provider instance
    
    Raises:
        ValueError: If provider not found
    """
    if name not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown LLM provider: '{name}'. Available providers: {available}"
        )
    return _PROVIDERS[name]()


def list_providers() -> List[str]:
    """
    List all registered provider names.
    
    Returns:
        List of provider names
    """
    return sorted(_PROVIDERS.keys())


def get_provider_info(name: str) -> Optional[Dict[str, str]]:
    """
    Get information about a provider.
    
    Parameters:
        name: Provider name
    
    Returns:
        Dict with name, default_model, env_key_name, requires_api_key
        or None if not found
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

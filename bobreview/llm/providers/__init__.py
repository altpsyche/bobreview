"""
LLM Providers package.

Provides pluggable LLM providers for BobReview:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude 3)
- Ollama (local models)

Usage:
    from bobreview.llm.providers import get_provider, list_providers
    
    provider = get_provider("openai")
    response = provider.call(prompt, config)
"""

from .base import BaseLLMProvider, LLMProviderConfig
from .factory import (
    get_provider,
    register_provider,
    list_providers,
    get_provider_info,
)

__all__ = [
    "BaseLLMProvider",
    "LLMProviderConfig",
    "get_provider",
    "register_provider",
    "list_providers",
    "get_provider_info",
]

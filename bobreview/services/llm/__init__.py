"""
LLM package for BobReview.

Provides a clean abstraction for LLM interactions:
- client: Core API client and caching
- providers: Pluggable LLM providers (OpenAI, Anthropic, Ollama)

Note: LLM generators are plugin-provided (e.g., plugins/<plugin-name>/generators/).
"""

from .client import call_llm, call_llm_chunked
from .providers import get_provider, list_providers, register_provider

__all__ = [
    'call_llm',
    'call_llm_chunked',
    'get_provider',
    'list_providers',
    'register_provider',
]

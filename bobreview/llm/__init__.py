"""
LLM package for BobReview.

Provides a clean abstraction for LLM interactions:
- client: Core API client and caching
- generators: Individual content generators
"""

from .client import call_llm, call_llm_chunked, clean_llm_response

__all__ = [
    'call_llm',
    'call_llm_chunked',
    'clean_llm_response',
]

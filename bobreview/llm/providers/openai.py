"""
OpenAI LLM provider implementation.

Supports GPT-4, GPT-4 Turbo, GPT-3.5 Turbo, and other OpenAI models.
"""

import random
import re
import time
from typing import Optional

from .base import BaseLLMProvider, LLMProviderConfig

# Check for OpenAI availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def clean_llm_response(response: str) -> str:
    """Clean LLM response by removing markdown code fences and extra formatting."""
    response = re.sub(r'^[ \t]*```[^\n]*\n?', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n?[ \t]*```\s*$', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    return response.strip()


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider.
    
    Supports models: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo, etc.
    Requires OPENAI_API_KEY environment variable or --llm-api-key.
    """
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def default_model(self) -> str:
        return "gpt-4o"
    
    @property
    def env_key_name(self) -> str:
        return "OPENAI_API_KEY"
    
    def call(
        self,
        prompt: str,
        config: LLMProviderConfig,
        max_retries: int = 3
    ) -> str:
        """
        Call OpenAI API with retry logic for rate limits.
        
        Parameters:
            prompt: The prompt to send
            config: Provider configuration
            max_retries: Maximum retry attempts
        
        Returns:
            Cleaned response text
        
        Raises:
            RuntimeError: If API unavailable, key missing, or call fails
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "OpenAI library not available. Install with: pip install 'openai>=1.0.0'"
            )
        
        self.validate_config(config)
        api_key = self.get_api_key(config)
        
        # Create client with optional custom base URL
        client_kwargs = {"api_key": api_key}
        if config.api_base:
            client_kwargs["base_url"] = config.api_base
        
        client = openai.OpenAI(**client_kwargs)
        model = config.model or self.default_model
        
        # Retry with exponential backoff
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    **config.extra_params
                )
                
                if not response.choices:
                    raise RuntimeError("No response from OpenAI")
                
                return clean_llm_response(response.choices[0].message.content)
                
            except openai.RateLimitError as e:
                if "quota" in str(e).lower():
                    raise RuntimeError(
                        "OpenAI API quota exceeded. Check billing at "
                        "https://platform.openai.com/account/billing"
                    ) from e
                
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + random.random()
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Rate limit after {max_retries} attempts") from e
                    
            except openai.APIError as e:
                raise RuntimeError(f"OpenAI API error: {e}") from e
            except Exception as e:
                raise RuntimeError(f"OpenAI error: {e}") from e

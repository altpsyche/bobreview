"""
OpenAI LLM provider implementation.

Supports GPT-4, GPT-4 Turbo, GPT-3.5 Turbo, and other OpenAI models.
"""

import random
import time
from typing import Optional

from .base import BaseLLMProvider, LLMProviderConfig, clean_llm_response

# Check for OpenAI availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider.
    
    Supports models: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo, etc.
    Requires OPENAI_API_KEY environment variable or --llm-api-key.
    """
    
    @property
    def name(self) -> str:
        """
        Provider identifier for the OpenAI implementation.
        
        Returns:
            The provider name "openai".
        """
        return "openai"
    
    @property
    def default_model(self) -> str:
        """
        Default model identifier used by the provider.
        
        Returns:
            The default model name: "gpt-4o".
        """
        return "gpt-4o"
    
    @property
    def env_key_name(self) -> str:
        """
        Name of the environment variable that stores the OpenAI API key.
        
        Returns:
            str: The environment variable name "OPENAI_API_KEY".
        """
        return "OPENAI_API_KEY"
    
    def call(
        self,
        prompt: str,
        config: LLMProviderConfig,
        max_retries: int = 3
    ) -> str:
        """
        Call the OpenAI Chat Completions API with retry and exponential backoff for rate limits.
        
        Parameters:
            prompt (str): The user prompt to send to the model.
            config (LLMProviderConfig): Provider configuration; used fields include `model` (optional), `temperature`, `max_tokens`, `extra_params`, and `api_base` (optional).
            max_retries (int): Maximum number of attempts to retry on rate-limit errors.
        
        Returns:
            str: The cleaned text content of the first chat completion choice.
        
        Raises:
            RuntimeError: If the OpenAI library is unavailable, configuration or API key validation fails, the API returns no choices, quota is exceeded, an OpenAI API error occurs, or other OpenAI-related errors occur.
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
                
                content = response.choices[0].message.content
                if content is None:
                    raise RuntimeError("No text content in OpenAI response")
                return clean_llm_response(content)
                
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
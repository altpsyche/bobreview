"""
Ollama LLM provider implementation.

Supports local Ollama models like Llama 2, Mistral, CodeLlama, etc.
No API key required - runs locally.
"""

import os
import time
from typing import Optional

from .base import BaseLLMProvider, LLMProviderConfig, clean_llm_response

# Check for httpx availability (used for Ollama API calls)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class OllamaProvider(BaseLLMProvider):
    """
    Ollama local LLM provider.
    
    Supports any model available in Ollama:
    - llama2, llama2:13b, llama2:70b
    - mistral, mistral:instruct
    - codellama, codellama:13b
    - mixtral
    - And many more...
    
    No API key required. Uses OLLAMA_API_BASE for custom endpoint
    (default: http://localhost:11434).
    """
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    @property
    def name(self) -> str:
        """
        Provider identifier for this LLM backend.
        
        Returns:
            "ollama" — the provider name.
        """
        return "ollama"
    
    @property
    def default_model(self) -> str:
        """
        Provide the provider's default model identifier.
        
        Returns:
            The model identifier "llama2".
        """
        return "llama2"
    
    @property
    def env_key_name(self) -> str:
        """
        Name of the environment variable used for the provider's API key.
        
        Usually not required for local Ollama deployments.
        
        Returns:
            env_var (str): The environment variable name `OLLAMA_API_KEY`.
        """
        return "OLLAMA_API_KEY"  # Not typically used
    
    @property
    def requires_api_key(self) -> bool:
        """Ollama runs locally and doesn't require an API key."""
        return False
    
    def _get_base_url(self, config: LLMProviderConfig) -> str:
        """
        Determine the base URL for the Ollama API by checking configuration, then environment, then the default.
        
        Parameters:
            config (LLMProviderConfig): Provider configuration that may contain an `api_base` override.
        
        Returns:
            str: The resolved base URL (from `config.api_base`, or the `OLLAMA_API_BASE` environment variable, or `DEFAULT_BASE_URL`).
        """
        return (
            config.api_base or 
            os.getenv("OLLAMA_API_BASE") or 
            self.DEFAULT_BASE_URL
        )
    
    def call(
        self,
        prompt: str,
        config: LLMProviderConfig,
        max_retries: int = 3
    ) -> str:
        """
        Generate text from a local Ollama model using the given prompt and provider configuration.
        
        Parameters:
            prompt (str): The prompt text to send to the model.
            config (LLMProviderConfig): Provider configuration (model, temperature, max_tokens, extra_params, etc.).
            max_retries (int): Maximum number of retry attempts for transient request failures.
        
        Returns:
            str: The model's response text with Markdown code fences removed.
        
        Raises:
            RuntimeError: If the httpx dependency is missing, Ollama cannot be reached, a timeout occurs after retries,
            the specified model is not found, or any other error occurs while making the request.
        """
        if not HTTPX_AVAILABLE:
            raise RuntimeError(
                "httpx library not available. Install with: pip install httpx"
            )
        
        base_url = self._get_base_url(config)
        model = config.model or self.default_model
        
        # Build request
        url = f"{base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            }
        }
        
        # Add any extra params
        if config.extra_params:
            payload["options"].update(config.extra_params)
        
        # Retry with exponential backoff
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    if "response" not in data:
                        raise RuntimeError("No response from Ollama")
                    
                    return clean_llm_response(data["response"])
                    
            except httpx.ConnectError as e:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {base_url}. "
                    "Make sure Ollama is running (ollama serve)"
                ) from e
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + 0.5
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Ollama timeout after {max_retries} attempts") from None
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise RuntimeError(
                        f"Model '{model}' not found. Pull it with: ollama pull {model}"
                    ) from e
                raise RuntimeError(f"Ollama HTTP error: {e}") from e
            except Exception as e:
                raise RuntimeError(f"Ollama error: {e}") from e
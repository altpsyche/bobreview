"""
Ollama LLM provider implementation.

Supports local Ollama models like Llama 2, Mistral, CodeLlama, etc.
No API key required - runs locally.
"""

import re
import time
from typing import Optional

from .base import BaseLLMProvider, LLMProviderConfig

# Check for httpx availability (used for Ollama API calls)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


def clean_response(response: str) -> str:
    """Clean LLM response by removing markdown code fences."""
    response = re.sub(r'^[ \t]*```[^\n]*\n?', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n?[ \t]*```\s*$', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    return response.strip()


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
        return "ollama"
    
    @property
    def default_model(self) -> str:
        return "llama2"
    
    @property
    def env_key_name(self) -> str:
        return "OLLAMA_API_KEY"  # Not typically used
    
    @property
    def requires_api_key(self) -> bool:
        """Ollama runs locally and doesn't require an API key."""
        return False
    
    def _get_base_url(self, config: LLMProviderConfig) -> str:
        """Get Ollama API base URL from config or environment."""
        import os
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
        Call Ollama API.
        
        Parameters:
            prompt: The prompt to send
            config: Provider configuration
            max_retries: Maximum retry attempts
        
        Returns:
            Cleaned response text
        
        Raises:
            RuntimeError: If Ollama is not running or call fails
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
                    
                    return clean_response(data["response"])
                    
            except httpx.ConnectError:
                raise RuntimeError(
                    f"Cannot connect to Ollama at {base_url}. "
                    "Make sure Ollama is running (ollama serve)"
                )
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + 0.5
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Ollama timeout after {max_retries} attempts")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise RuntimeError(
                        f"Model '{model}' not found. Pull it with: ollama pull {model}"
                    )
                raise RuntimeError(f"Ollama HTTP error: {e}") from e
            except Exception as e:
                raise RuntimeError(f"Ollama error: {e}") from e

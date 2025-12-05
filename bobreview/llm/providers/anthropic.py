"""
Anthropic Claude LLM provider implementation.

Supports Claude 3 Opus, Sonnet, and Haiku models.
"""

import re
import time
from typing import Optional

from .base import BaseLLMProvider, LLMProviderConfig

# Check for Anthropic availability
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def clean_response(response: str) -> str:
    """
    Remove Markdown triple-backtick code fences from an LLM response and trim surrounding whitespace.
    
    Returns:
        cleaned_response (str): The response text with code-fence markers removed and leading/trailing whitespace trimmed.
    """
    response = re.sub(r'^[ \t]*```[^\n]*\n?', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n?[ \t]*```\s*$', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    return response.strip()


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider.
    
    Supports models:
    - claude-3-opus-20240229
    - claude-3-sonnet-20240229
    - claude-3-haiku-20240307
    - claude-3-5-sonnet-20241022
    
    Requires ANTHROPIC_API_KEY environment variable or --llm-api-key.
    """
    
    @property
    def name(self) -> str:
        """
        Canonical provider identifier for the Anthropic Claude implementation.
        
        Returns:
            str: The provider identifier "anthropic".
        """
        return "anthropic"
    
    @property
    def default_model(self) -> str:
        """
        Default model identifier used when no model is provided.
        
        Returns:
            The default model identifier: "claude-3-5-sonnet-20241022".
        """
        return "claude-3-5-sonnet-20241022"
    
    @property
    def env_key_name(self) -> str:
        """
        Environment variable name used to locate the Anthropic API key.
        
        Returns:
            The environment variable name "ANTHROPIC_API_KEY".
        """
        return "ANTHROPIC_API_KEY"
    
    def call(
        self,
        prompt: str,
        config: LLMProviderConfig,
        max_retries: int = 3
    ) -> str:
        """
        Send a prompt to Anthropic Claude and return the cleaned text response.
        
        Parameters:
        	prompt (str): The prompt to send to the model.
        	config (LLMProviderConfig): Provider configuration (model, max_tokens, extra_params, api_base, etc.).
        	max_retries (int): Maximum retry attempts for rate limit errors before failing.
        
        Returns:
        	cleaned_text (str): The model's response with Markdown code fences removed and surrounding whitespace trimmed.
        
        Raises:
        	RuntimeError: If the Anthropic library is unavailable, the API key is missing/invalid, no response is returned, rate limits are exceeded after retries, or any API/transport error occurs.
        """
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "Anthropic library not available. Install with: pip install anthropic"
            )
        
        self.validate_config(config)
        api_key = self.get_api_key(config)
        
        # Create client
        client_kwargs = {"api_key": api_key}
        if config.api_base:
            client_kwargs["base_url"] = config.api_base
        
        client = anthropic.Anthropic(**client_kwargs)
        model = config.model or self.default_model
        
        # Retry with exponential backoff
        for attempt in range(max_retries):
            try:
                message = client.messages.create(
                    model=model,
                    max_tokens=config.max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    **config.extra_params
                )
                
                if not message.content:
                    raise RuntimeError("No response from Anthropic")
                
                # Extract text from content blocks
                text_content = ""
                for block in message.content:
                    if hasattr(block, 'text'):
                        text_content += block.text
                
                return clean_response(text_content)
                
            except anthropic.RateLimitError as e:
                if attempt < max_retries - 1:
                    wait = (2 ** attempt) + 0.5
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Rate limit after {max_retries} attempts") from e
                    
            except anthropic.APIError as e:
                raise RuntimeError(f"Anthropic API error: {e}") from e
            except Exception as e:
                raise RuntimeError(f"Anthropic error: {e}") from e
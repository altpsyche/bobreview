"""
LLM client for OpenAI API interactions.

Provides core functions for calling the LLM with caching,
retry logic, and response cleaning.
"""

import os
import re
import time
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import ReportConfig

from ..core.cache import get_cache
from ..core.utils import log_verbose, log_warning
from ..core.analysis import format_data_table

# Check for OpenAI availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def clean_llm_response(response: str) -> str:
    """Clean LLM response by removing markdown code fences and extra formatting."""
    # Remove markdown code fences (```html, ```, etc.)
    response = re.sub(r'^[ \t]*```[^\n]*\n?', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n?[ \t]*```\s*$', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    return response.strip()


def call_llm(
    prompt: str,
    data_table: Optional[str] = None,
    config: "Optional[ReportConfig]" = None,
    max_retries: int = 3,
) -> str:
    """
    Call OpenAI LLM with caching, dry-run support, and retry logic.
    
    Parameters:
        prompt: The user-facing prompt
        data_table: Optional tabular context
        config: Report configuration
        max_retries: Maximum retry attempts for rate limits
    
    Returns:
        Cleaned text response from the LLM
    
    Raises:
        RuntimeError: If API unavailable, key missing, or quota exceeded
        ValueError: If config is not provided
    """
    if config is None:
        raise ValueError("ReportConfig is required")
    
    # Dry run mode
    if config.dry_run:
        return "<p>Dry run mode - LLM analysis would appear here</p>"
    
    # Combine prompt with data table
    full_prompt = prompt
    if data_table:
        full_prompt = f"""{prompt}

Data Table:
{data_table}"""
    
    # Check cache first
    cache = get_cache()
    if cache:
        cached = cache.get(full_prompt, data_table or "", config.openai_model)
        if cached is not None:
            log_verbose("Using cached LLM response", config)
            return cached
    
    # Check OpenAI availability
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI library not available. Install with: pip install openai")
    
    # Get API key
    api_key = config.openai_api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY or use --openai-key")
    
    client = openai.OpenAI(api_key=api_key)
    log_verbose(f"Calling LLM API (model: {config.openai_model})", config)
    
    # Retry with exponential backoff
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens
            )
            result = clean_llm_response(response.choices[0].message.content)
            
            if cache:
                cache.set(full_prompt, data_table or "", config.openai_model, result)
            return result
            
        except openai.RateLimitError as e:
            if "quota" in str(e).lower():
                raise RuntimeError(
                    "OpenAI API quota exceeded. Check billing at "
                    "https://platform.openai.com/account/billing"
                ) from e
            
            if attempt < max_retries - 1:
                wait = (2 ** attempt) + (time.time() % 1)
                log_warning(f"Rate limit, retrying in {wait:.1f}s...", config)
                time.sleep(wait)
            else:
                raise RuntimeError(f"Rate limit after {max_retries} attempts") from e
                
        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}") from e
    
    raise RuntimeError(f"Failed after {max_retries} attempts")


def call_llm_chunked(
    prompt_base: str,
    data_points: List[Dict[str, Any]],
    config: "ReportConfig",
    chunk_size: Optional[int] = None,
) -> str:
    """Call LLM with data points in chunks and combine results."""
    if chunk_size is None:
        chunk_size = config.image_chunk_size
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    if not data_points:
        return call_llm(prompt_base, data_table=None, config=config)
    
    # Process in chunks
    results = []
    for i in range(0, len(data_points), chunk_size):
        chunk = data_points[i:i + chunk_size]
        data_table = format_data_table(chunk)
        chunk_prompt = f"""{prompt_base}

Processing samples {i+1}-{min(i+chunk_size, len(data_points))} of {len(data_points)}."""
        
        result = call_llm(chunk_prompt, data_table=data_table, config=config)
        results.append(result)
    
    # Combine if multiple chunks
    if len(results) == 1:
        return results[0]
    
    chunks_text = '\n'.join([f"Chunk {i+1}:\n{r}" for i, r in enumerate(results)])
    combine_prompt = f"""Combine these {len(results)} analyses into one coherent response:

{chunks_text}

Provide a unified analysis integrating all information."""
    return call_llm(combine_prompt, data_table=None, config=config)

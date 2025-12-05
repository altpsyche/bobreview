"""
LLM client for OpenAI API interactions.

Provides core functions for calling the LLM with caching,
retry logic, and response cleaning.
"""

import os
import re
import time
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Callable

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
        max_retries: Maximum retry attempts for rate limits (must be positive)
    
    Returns:
        Cleaned text response from the LLM
    
    Raises:
        RuntimeError: If API unavailable, key missing, or quota exceeded
        ValueError: If config is not provided or max_retries is not positive
    """
    if config is None:
        raise ValueError("ReportConfig is required")
    
    if max_retries <= 0:
        raise ValueError("max_retries must be positive")
    
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
    # Cache key includes prompt, data_table, model, temperature, and max_tokens
    # to ensure different generation parameters produce different cache entries
    cache = get_cache()
    if cache:
        cached = cache.get(
            prompt, 
            data_table or "", 
            config.openai_model,
            config.llm_temperature,
            config.llm_max_tokens
        )
        if cached is not None:
            log_verbose("Using cached LLM response", config)
            return cached
    
    # Check OpenAI availability
    # Requires openai>=1.0.0 (v1 API) for openai.OpenAI() and openai.RateLimitError
    if not OPENAI_AVAILABLE:
        raise RuntimeError(
            "OpenAI library not available. Install with: pip install 'openai>=1.0.0,<2.0.0'"
        )
    
    # Get API key
    api_key = config.openai_api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY or use --openai-key")
    
    # Use OpenAI v1 API (openai>=1.0.0)
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
            if not response.choices:
                raise RuntimeError("No response from LLM")
            result = clean_llm_response(response.choices[0].message.content)
            
            # Cache the result with all generation parameters in the key
            # to ensure cache entries are invalidated when parameters change
            if cache:
                cache.set(
                    prompt,
                    data_table or "",
                    config.openai_model,
                    config.llm_temperature,
                    config.llm_max_tokens,
                    result
                )
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


def call_llm_chunked(
    prompt_base: str,
    data_points: List[Dict[str, Any]],
    config: "ReportConfig",
    chunk_size: Optional[int] = None,
    table_formatter: Callable[[List[Dict[str, Any]]], str] = format_data_table,
) -> str:
    """
    Call LLM with data points in chunks and combine results.
    
    Uses pairwise reduction to combine chunks, avoiding token limit issues when
    there are many chunks. Chunks are combined two at a time until a single
    unified result remains.
    
    Parameters:
        prompt_base: Base prompt to use for each chunk
        data_points: List of data point dictionaries to process
        config: Report configuration
        chunk_size: Number of data points per chunk (defaults to config.llm_chunk_size)
        table_formatter: Function to format data points into a table string.
                        Defaults to format_data_table. Custom formatters can be provided
                        for different data schemas.
    
    Returns:
        Combined LLM response from all chunks
    
    Note:
        When combining many chunks, the pairwise reduction approach prevents
        exceeding token limits. However, if individual chunk results are very
        large, warnings may be logged when content size exceeds
        config.llm_combine_warning_threshold. Consider reducing chunk_size or
        adjusting the warning threshold if you encounter token limit issues.
    """
    if chunk_size is None:
        chunk_size = config.llm_chunk_size
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    if not data_points:
        return call_llm(prompt_base, data_table=None, config=config)
    
    # Process in chunks
    results = []
    for i in range(0, len(data_points), chunk_size):
        chunk = data_points[i:i + chunk_size]
        data_table = table_formatter(chunk)
        chunk_prompt = f"""{prompt_base}

Processing samples {i+1}-{min(i+chunk_size, len(data_points))} of {len(data_points)}."""
        
        result = call_llm(chunk_prompt, data_table=data_table, config=config)
        results.append(result)
    
    # Combine if multiple chunks using pairwise reduction
    if len(results) == 1:
        return results[0]
    
    # Pairwise reduction to avoid token limits
    while len(results) > 1:
        # Check for potential token limit issues
        total_length = sum(len(r) for r in results)
        if total_length > config.llm_combine_warning_threshold:
            log_warning(
                f"Large content size ({total_length:,} chars) when combining {len(results)} chunks. "
                f"This may approach token limits. Consider reducing chunk_size.",
                config
            )
        
        # Combine pairs of results
        combined = []
        for i in range(0, len(results), 2):
            if i + 1 < len(results):
                # Combine two chunks
                pair_text = f"""First Analysis:
{results[i]}

Second Analysis:
{results[i+1]}"""
                
                combine_prompt = f"""Combine these two analyses into one coherent response:

{pair_text}

Provide a unified analysis integrating all information from both analyses."""
                combined_result = call_llm(combine_prompt, data_table=None, config=config)
                combined.append(combined_result)
            else:
                # Odd number: keep the last chunk as-is
                combined.append(results[i])
        
        results = combined
    
    return results[0]

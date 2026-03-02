"""
LLM client for API interactions.

Provides core functions for calling LLM providers with caching,
retry logic, and response cleaning.
"""

import os
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ...core.config import Config

from ...core.cache import get_cache
from ...core.utils import log_verbose, log_warning, format_number

from .providers import get_provider, LLMProviderConfig


def format_data_table(
    data_points: List[Dict[str, Any]], 
    max_rows: Optional[int] = None,
    fields: Optional[List[str]] = None,
    field_labels: Optional[Dict[str, str]] = None
) -> str:
    """
    Render a list of data points as a markdown table for LLM context.
    
    Parameters:
        data_points: Sequence of data point dictionaries
        max_rows: Maximum number of rows to include
        fields: List of field names to include as columns
        field_labels: Dict mapping field names to display labels
    
    Returns:
        Markdown-formatted table or "No data available." if empty
    """
    total_samples = len(data_points)
    display_points = data_points
    if max_rows is not None:
        display_points = data_points[:max_rows]
    
    if not display_points:
        return "No data available."
    
    # Determine fields to display
    if fields is None:
        first_point = display_points[0]
        fields = [k for k in first_point.keys() if not k.startswith('_')]
    
    if not fields:
        return "No data available."
    
    # Get labels (default to field names)
    if field_labels is None:
        field_labels = {}
    labels = {field: field_labels.get(field, field.replace('_', ' ').title()) for field in fields}
    
    # Create table header
    header_row = "| Index | " + " | ".join(labels.values()) + " |\n"
    separator_row = "|" + "|".join(["-------"] * (len(fields) + 1)) + "|\n"
    table = header_row + separator_row
    
    # Add rows
    for idx, point in enumerate(display_points):
        row_values = [str(idx)]
        for field in fields:
            value = point.get(field, '')
            if isinstance(value, (int, float)):
                if isinstance(value, float) and value >= 1000:
                    value = format_number(int(value), 0)
                elif isinstance(value, int) and value >= 1000:
                    value = format_number(value, 0)
                else:
                    value = str(value)
            # Escape pipe chars so cell content can't break the table structure
            row_values.append(str(value).replace('|', '\\|'))
        table += "| " + " | ".join(row_values) + " |\n"
    
    if max_rows is not None and total_samples > max_rows:
        table += f"\n(Showing first {max_rows} of {total_samples} total samples)"
    
    return table


def call_llm(
    prompt: str,
    data_table: Optional[str] = None,
    config: "Optional[Config]" = None,
    max_retries: int = 3,
) -> str:
    """
    Invoke the configured LLM provider for a prompt, optionally including tabular context, with caching, dry-run, and retry behavior.
    
    If a data table is provided it will be appended to the prompt before calling the provider. If caching is available the function will attempt to return a cached response for the same prompt and configuration. If config.dry_run is true a static placeholder HTML is returned instead of calling the provider.
    
    Parameters:
        data_table (str, optional): Tabular context to append to the prompt.
        config (Config): Report configuration containing LLM provider, model, credentials, and related settings.
        max_retries (int): Maximum number of retry attempts delegated to the provider; must be greater than zero.
    
    Returns:
        The LLM provider's response text.
    
    Raises:
        ValueError: If `config` is not provided or `max_retries` is not positive.
    """
    if config is None:
        raise ValueError("Config is required")
    
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
    cache = get_cache()
    if cache:
        cached = cache.get(
            prompt, 
            data_table or "", 
            config.llm_model,
            config.llm_temperature,
            config.llm_max_tokens,
            config.llm_provider,
            config.llm_api_base or ""
        )
        if cached is not None:
            log_verbose("Using cached LLM response", config)
            return cached
    
    # Get provider and make call
    provider = get_provider(config.llm_provider)
    log_verbose(f"Calling LLM ({provider.name}: {config.llm_model})", config)
    
    # Build provider config
    provider_config = LLMProviderConfig(
        model=config.llm_model,
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
        api_key=config.llm_api_key,
        api_base=config.llm_api_base,
    )
    
    # Make the call
    result = provider.call(full_prompt, provider_config, max_retries)
    
    # Cache the result
    if cache:
        cache.set(
            prompt,
            data_table or "",
            config.llm_model,
            config.llm_temperature,
            config.llm_max_tokens,
            result,
            config.llm_provider,
            config.llm_api_base or ""
        )
    
    return result


MAX_CHUNKS = 50  # Safety limit to prevent runaway LLM API costs


def call_llm_chunked(
    prompt_base: str,
    data_points: List[Dict[str, Any]],
    config: "Config",
    chunk_size: Optional[int] = None,
    max_chunks: int = MAX_CHUNKS,
    table_formatter: Callable[[List[Dict[str, Any]]], str] = format_data_table,
) -> str:
    """
    Process data_points in chunks with the LLM and return a single combined response.
    
    Each chunk is formatted with table_formatter and sent to the LLM using prompt_base; individual chunk responses are then merged by repeated pairwise combination until one unified result remains.
    
    Parameters:
        prompt_base (str): Base prompt used for each chunk.
        data_points (List[Dict[str, Any]]): Data points to process.
        config (Config): Report configuration containing LLM and chunking settings.
        chunk_size (Optional[int]): Number of data points per chunk; if None, uses config.llm_chunk_size.
        table_formatter (Callable[[List[Dict[str, Any]]], str]): Function that formats a list of data points into a table string.
    
    Returns:
        str: Unified LLM response combining analyses from all chunks.
    """
    if chunk_size is None:
        chunk_size = config.llm_chunk_size

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if max_chunks <= 0:
        raise ValueError("max_chunks must be positive")

    if not data_points:
        return call_llm(prompt_base, data_table=None, config=config)

    # Safety check: cap total number of LLM API calls.
    # The pairwise combine phase adds up to (initial_chunks - 1) extra calls,
    # so total_expected = initial_chunks + (initial_chunks - 1) = 2*initial - 1.
    # Reduce initial_chunks until total_expected <= max_chunks.
    import math
    initial_chunks = math.ceil(len(data_points) / chunk_size)
    total_expected = 2 * initial_chunks - 1 if initial_chunks > 1 else 1
    if total_expected > max_chunks:
        # Solve: 2*n - 1 <= max_chunks => n <= (max_chunks + 1) / 2
        allowed_initial = max((max_chunks + 1) // 2, 1)
        log_warning(
            f"Data has {len(data_points)} points requiring {initial_chunks} chunks "
            f"({total_expected} total LLM calls including combines, limit: {max_chunks}). "
            f"Truncating to {allowed_initial} chunks ({allowed_initial * chunk_size} points).",
            config,
        )
        data_points = data_points[:allowed_initial * chunk_size]

    # Process in chunks
    results = []
    for i in range(0, len(data_points), chunk_size):
        chunk = data_points[i:i + chunk_size]
        data_table = table_formatter(chunk)
        chunk_prompt = f"""{prompt_base}

Processing samples {i+1}-{min(i+chunk_size, len(data_points))} of {len(data_points)}."""
        
        result = call_llm(chunk_prompt, data_table=data_table, config=config)
        results.append(result)
    
    # Guard against empty results (e.g., if data was truncated to nothing)
    if not results:
        return table_formatter([])

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
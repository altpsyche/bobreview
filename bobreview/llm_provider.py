"""
LLM provider and prompt generation for BobReview.
"""

import os
import re
import statistics
import time
from typing import Dict, List, Any, Optional

from .cache import get_cache
from .utils import log_verbose, log_warning, format_number
from .analysis import format_data_table

# Check for OpenAI availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def clean_llm_response(response: str) -> str:
    """Clean LLM response by removing markdown code fences and extra formatting."""
    # Remove markdown code fences (```html, ```, etc.)
    # Remove opening code fence with optional leading spaces and language
    response = re.sub(r'^[ \t]*```[^\n]*\n?', '', response, flags=re.MULTILINE)
    # Remove closing code fence (also tolerating leading spaces)
    response = re.sub(r'\n?[ \t]*```\s*$', '', response, flags=re.MULTILINE)
    # Remove any remaining standalone code fences
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    
    return response.strip()


def call_llm(
    prompt: str,
    data_table: str | None = None,
    config=None,
    max_retries: int = 3,
) -> str:
    """
    Generate LLM text for a prompt (optionally augmented with a data table), using caching, dry-run support, and retry/backoff on rate limits.
    
    Parameters:
        prompt (str): The user-facing prompt to send to the LLM.
        data_table (str, optional): Optional tabular context appended to the prompt.
        config (ReportConfig): Report configuration providing OpenAI settings, temperature, caching, and dry-run flags.
        max_retries (int): Maximum number of retry attempts for rate-limited calls.
    
    Returns:
        str: Cleaned text response from the LLM (code fences removed).
    
    Raises:
        RuntimeError: If OpenAI library is unavailable, API key is missing, quota is exceeded, rate limits persist after retries, or other OpenAI/API errors occur.
        ValueError: If `config` is not provided.
    """
    if config is None:
        raise ValueError("ReportConfig is required")
    
    # Dry run mode - return placeholder (check before OpenAI availability to allow pipeline validation)
    if config.dry_run:
        return "<p>Dry run mode - LLM analysis would appear here</p>"
    
    # Combine prompt with data table if provided
    full_prompt = prompt
    if data_table:
        full_prompt = f"""{prompt}

Data Table:
{data_table}"""
    
    # Check cache first
    cache = get_cache()
    if cache:
        cached_response = cache.get(full_prompt, data_table or "", config.openai_model)
        if cached_response is not None:
            log_verbose("Using cached LLM response", config)
            return cached_response
    
    # Check OpenAI availability (only needed for actual API calls)
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI library not available. Install with: pip install openai")
    
    if not config.openai_api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --openai-key")
    else:
        api_key = config.openai_api_key
    
    client = openai.OpenAI(api_key=api_key)
    
    log_verbose(f"Calling LLM API (model: {config.openai_model})", config)
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=config.llm_temperature,
                max_tokens=2000
            )
            # Clean the response to remove markdown code fences
            result = clean_llm_response(response.choices[0].message.content)
            
            # Cache the response
            if cache:
                cache.set(full_prompt, data_table or "", config.openai_model, result)
            
            return result
        
        except openai.RateLimitError as e:
            error_str = str(e).lower()
            if "insufficient_quota" in error_str or "quota" in error_str:
                raise RuntimeError(
                    "OpenAI API quota exceeded. Please check your billing and plan details at "
                    "https://platform.openai.com/account/billing. "
                    "You may need to add payment information or upgrade your plan."
                ) from e
            
            # Rate limit (but not quota) - retry with backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (time.time() % 1)  # Exponential backoff with jitter
                log_warning(
                    f"Rate limit hit, retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})",
                    config
                )
                time.sleep(wait_time)
            else:
                raise RuntimeError(
                    f"Rate limit exceeded after {max_retries} attempts. "
                    "Please wait a moment and try again, or check your API usage limits."
                ) from e
        
        except openai.APIError as e:
            # For other API errors, don't retry
            raise RuntimeError(f"OpenAI API error: {e}") from e
        
        except Exception as e:
            # For unexpected errors, don't retry
            raise RuntimeError(f"Unexpected error calling OpenAI API: {e}") from e
    
    raise RuntimeError(f"Failed to call OpenAI API after {max_retries} attempts")


def call_llm_chunked(
    prompt_base: str,
    data_points: List[Dict[str, Any]],
    config,
    chunk_size: int | None = None,
) -> str:
    """Call LLM with data points in chunks and combine results."""
    if chunk_size is None:
        chunk_size = config.image_chunk_size
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    
    if not data_points:
        # No data, just call LLM with prompt
        return call_llm(prompt_base, data_table=None, config=config)
    
    # Process data in chunks
    results = []
    for i in range(0, len(data_points), chunk_size):
        chunk = data_points[i:i + chunk_size]
        data_table = format_data_table(chunk)
        chunk_prompt = f"""{prompt_base}

Processing samples {i+1}-{min(i+chunk_size, len(data_points))} of {len(data_points)}."""
        
        result = call_llm(chunk_prompt, data_table=data_table, config=config)
        results.append(result)
    
    # Combine results
    if len(results) == 1:
        return results[0]
    else:
        # Ask LLM to combine the chunked results
        combine_prompt = f"""You have analyzed performance data in {len(results)} chunks. Combine these analyses into a single coherent response:

{chr(10).join([f"Chunk {i+1}:{chr(10)}{result}" for i, result in enumerate(results)])}

Provide a unified analysis that integrates all the information from these chunks."""
        return call_llm(combine_prompt, data_table=None, config=config)


def generate_executive_summary(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config,
    _images_dir_rel: str,
) -> str:
    """Generate executive summary using LLM."""
    critical_idx, critical_point = stats['critical']
    
    # Gather sample data points for context (critical, high-load, low-load)
    sample_data: List[Dict[str, Any]] = []
    # Include critical hotspot when index is valid
    if 0 <= critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
    else:
        log_warning(f"Critical index {critical_idx} out of range for {len(data_points)} samples", config)
    
    # Include a few high-load and low-load samples
    for idx, _ in stats['high_load'][:2]:
        if idx != critical_idx and idx < len(data_points):
            sample_data.append(data_points[idx])
    
    for idx, _ in stats['low_load'][:1]:
        if idx < len(data_points):
            sample_data.append(data_points[idx])
    
    prompt = f"""You are analyzing a performance report for a game level/scene. Generate a concise executive summary (2-3 paragraphs) based on this data:

Location: {config.location}
Total samples: {stats['count']}
Average draw calls: {format_number(stats['draws']['mean'], 0)}
Average triangles: {format_number(stats['tris']['mean'], 0)}
Median draw calls: {format_number(stats['draws']['median'], 0)}
Median triangles: {format_number(stats['tris']['median'], 0)}
Peak hotspot: Index {critical_idx} with {critical_point['draws']} draws and {format_number(critical_point['tris'])} triangles
High-load frames: {len(stats['high_load'])} (threshold: ≥{config.high_load_draw_threshold} draws or ≥{format_number(config.high_load_tri_threshold, 0)} tris)
Low-load frames: {len(stats['low_load'])} (threshold: <{config.low_load_draw_threshold} draws and <{format_number(config.low_load_tri_threshold, 0)} tris)

Analyze the provided data table to understand performance patterns across different samples.

Write a professional executive summary that:
1. Summarizes overall performance health
2. Highlights key concerns (if any)
3. Mentions the peak hotspot and its impact
4. Provides a brief assessment of variance

Use HTML paragraph tags (<p>) for formatting. Be concise and data-driven."""

    return call_llm_chunked(prompt, sample_data, config)


def generate_metric_deep_dive(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config,
    _images_dir_rel: str,
) -> Dict[str, str]:
    """
    Generate metric deep dive sections using LLM.
    
    Precondition: data_points must be non-empty (enforced by caller).
    """
    results: Dict[str, str] = {}
    
    if not data_points:
        log_warning("No data points available for metric deep dive; skipping LLM sections.", config)
        return results
    
    # Gather sample data points for draw calls analysis
    draw_samples = []
    for idx, _ in stats['draws']['outliers_high'][:5]:
        if idx < len(data_points):
            draw_samples.append(data_points[idx])
    for idx, _ in stats['draws']['outliers_low'][:2]:
        if idx < len(data_points):
            draw_samples.append(data_points[idx])
    
    # Draw Calls section
    prompt = f"""Analyze draw call performance data and write 2-3 paragraphs:

Statistics:
- Samples: {stats['count']}
- Min: {stats['draws']['min']}, Max: {stats['draws']['max']}
- Q1: {format_number(stats['draws']['q1'], 0)}, Median: {format_number(stats['draws']['median'], 0)}, Q3: {format_number(stats['draws']['q3'], 0)}
- Mean: {format_number(stats['draws']['mean'], 1)}, Std Dev: {format_number(stats['draws']['stdev'], 1)}
- High outliers (>2 std dev): {len(stats['draws']['outliers_high'])} frames at indices {', '.join([str(i) for i, _ in stats['draws']['outliers_high']])}
- Low outliers (>2 std dev): {len(stats['draws']['outliers_low'])} frames at indices {', '.join([str(i) for i, _ in stats['draws']['outliers_low']])}
- Hard cap threshold: {config.draw_hard_cap}

Analyze the provided data table to understand patterns in high and low draw call frames.

Write analysis covering:
1. Typical performance range (Q1-Q3)
2. Significance of outliers
3. Comparison to thresholds
4. What the distribution suggests

Use HTML paragraph tags. Be technical but accessible."""
    
    results['draws'] = call_llm_chunked(prompt, draw_samples, config)
    
    # Triangle Count section
    tri_samples = []
    for idx, _ in stats['tris']['outliers_high'][:5]:
        if idx < len(data_points):
            tri_samples.append(data_points[idx])
    
    prompt = f"""Analyze triangle count performance data and write 2-3 paragraphs:

Statistics:
- Samples: {stats['count']}
- Min: {format_number(stats['tris']['min'])}, Max: {format_number(stats['tris']['max'])}
- Q1: {format_number(stats['tris']['q1'])}, Median: {format_number(stats['tris']['median'])}, Q3: {format_number(stats['tris']['q3'])}
- Mean: {format_number(stats['tris']['mean'], 1)}, Std Dev: {format_number(stats['tris']['stdev'], 1)}
- High outliers (>2 std dev): {len(stats['tris']['outliers_high'])} frames at indices {', '.join([str(i) for i, _ in stats['tris']['outliers_high']])}
- Hard cap threshold: {format_number(config.tri_hard_cap, 0)}

Analyze the provided data table to understand patterns in high triangle count frames.

Write analysis covering:
1. Distribution characteristics
2. Impact of high outliers
3. Comparison to thresholds
4. Geometry complexity assessment

Use HTML paragraph tags. Be technical but accessible."""
    
    results['tris'] = call_llm_chunked(prompt, tri_samples, config)
    
    # Temporal and Correlation sections
    timestamps = [p['ts'] for p in data_points]
    time_span = max(timestamps) - min(timestamps)
    avg_interval = time_span / (len(data_points) - 1) if len(data_points) > 1 else 0
    sorted_by_draws = sorted(data_points, key=lambda x: x['draws'])
    low_draw_tris = statistics.mean([p['tris'] for p in sorted_by_draws[:10]])
    high_draw_tris = statistics.mean([p['tris'] for p in sorted_by_draws[-10:]])
    
    # Gather correlation data samples
    corr_samples = []
    for point in sorted_by_draws[:5]:  # Low draw samples
        corr_samples.append(point)
    for point in sorted_by_draws[-5:]:  # High draw samples
        corr_samples.append(point)
    
    prompt = f"""Analyze temporal behavior and correlation between draw calls and triangle counts:

Temporal:
- Time span: {time_span} seconds ({time_span/60:.1f} minutes)
- Average interval: {avg_interval:.1f} seconds
- No missing samples

Correlation:
- Low draw call frames (bottom 10): avg {format_number(low_draw_tris, 0)} triangles
- High draw call frames (top 10): avg {format_number(high_draw_tris, 0)} triangles

Analyze the provided data table showing low-draw and high-draw frames to understand the correlation.

Write 2 paragraphs:
1. Temporal behavior analysis
2. Draw calls vs triangle correlation and its implications

Use HTML paragraph tags. Include a heading <h3>2.4 Draw Calls vs Triangle Correlation</h3> before the second paragraph."""
    
    results['temporal'] = call_llm_chunked(prompt, corr_samples, config)
    
    return results


def generate_zones_hotspots(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config,
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate zones and hotspots analysis using LLM."""
    results = {}
    
    # High-load analysis
    high_load_summary = f"{len(stats['high_load'])} frames exceed thresholds (≥{config.high_load_draw_threshold} draws or ≥{format_number(config.high_load_tri_threshold, 0)} tris)"
    high_load_details = "\n".join([f"Index {i}: {p['draws']} draws, {format_number(p['tris'])} tris" for i, p in stats['high_load'][:5]])
    
    # Gather high-load data points
    high_load_samples = []
    for idx, _ in stats['high_load']:
        if idx < len(data_points):
            high_load_samples.append(data_points[idx])
    
    prompt = f"""Analyze high-load performance frames:

{high_load_summary}
Top frames:
{high_load_details}

Analyze the provided data table to identify patterns.

Write 1-2 paragraphs analyzing:
1. Patterns in high-load frames
2. Whether they're draw-call or geometry dominated
3. Common characteristics

Use HTML paragraph tags."""
    
    results['high_load'] = call_llm_chunked(prompt, high_load_samples, config)
    
    # Low-load analysis
    low_load_summary = f"{len(stats['low_load'])} frames below thresholds (<{config.low_load_draw_threshold} draws and <{format_number(config.low_load_tri_threshold, 0)} tris)"
    
    low_load_samples = []
    for idx, _ in stats['low_load']:
        if idx < len(data_points):
            low_load_samples.append(data_points[idx])
    
    prompt = f"""Analyze low-load baseline frames:

{low_load_summary}

Analyze the provided data table to understand what makes these frames perform well.

Write 1 paragraph explaining their significance as performance baselines.

Use HTML paragraph tags."""
    
    results['low_load'] = call_llm_chunked(prompt, low_load_samples, config)
    
    return results


def generate_optimization_checklist(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config,
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate optimization checklist using LLM."""
    results = {}
    
    critical_idx, critical_point = stats['critical']
    
    # Critical hotspot analysis - use the critical data point
    critical_samples: List[Dict[str, Any]] = []
    if 0 <= critical_idx < len(data_points):
        critical_samples.append(data_points[critical_idx])
    else:
        log_warning(f"Critical index {critical_idx} out of range for {len(data_points)} samples", config)
    
    prompt = f"""Generate optimization recommendations for a critical performance hotspot:

Critical hotspot: Index {critical_idx}
- Draw calls: {critical_point['draws']} (hard cap: {config.draw_hard_cap})
- Triangles: {format_number(critical_point['tris'])} (hard cap: {format_number(config.tri_hard_cap, 0)})
- Test case: {critical_point['testcase']}

Analyze the provided data to understand the context and identify specific optimization opportunities.

Generate:
1. Inspection steps (3-4 bullet points)
2. Optimization actions organized by category:
   - Geometry optimizations
   - Draw call optimizations  
   - Lighting/shadow optimizations
   - Verification steps

Format as HTML with <ul> and <li> tags. Be specific and actionable."""

    results['critical'] = call_llm_chunked(prompt, critical_samples, config)
    
    # High-geometry hotspots
    high_geo_count = len([p for _, p in stats['high_load'] if p['tris'] >= config.high_load_tri_threshold])
    high_geo_samples = []
    for idx, point in stats['high_load']:
        if point['tris'] >= config.high_load_tri_threshold and idx < len(data_points):
            high_geo_samples.append(data_points[idx])
    
    prompt = f"""Generate optimization recommendations for high-geometry hotspots:

Affected frames: {high_geo_count} above {format_number(config.high_load_tri_threshold, 0)} triangles
Target: reduce below {format_number(config.tri_hard_cap, 0)} triangles

Analyze the provided data table to identify geometry complexity patterns.

Generate 4-5 actionable bullet points focusing on geometry/LOD optimization.

Format as HTML <ul> with <li> tags."""

    results['high_geometry'] = call_llm_chunked(prompt, high_geo_samples, config)
    
    # High-draw hotspots
    high_draw_samples = []
    for idx, point in stats['high_load']:
        if point['draws'] >= config.high_load_draw_threshold and idx < len(data_points):
            high_draw_samples.append(data_points[idx])
    
    prompt = f"""Generate optimization recommendations for high-draw-call hotspots:

Focus: frames with draws ≥ {config.high_load_draw_threshold}
Target: reduce below {config.draw_soft_cap} draw calls

Analyze the provided data table to identify draw call batching opportunities.

Generate 4-5 actionable bullet points focusing on draw call batching and material consolidation.

Format as HTML <ul> with <li> tags."""

    results['high_draw'] = call_llm_chunked(prompt, high_draw_samples, config)
    
    return results


def generate_system_recommendations(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config,
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate system-level recommendations using LLM."""
    results = {}
    
    # Gather representative data points from different performance zones
    sample_data: List[Dict[str, Any]] = []
    # Critical hotspot
    critical_idx = stats['critical'][0]
    if 0 <= critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
    else:
        log_warning(f"Critical index {critical_idx} out of range for {len(data_points)} samples", config)
    
    # High-load samples
    for idx, _ in stats['high_load'][:3]:
        if idx < len(data_points) and idx != critical_idx:
            sample_data.append(data_points[idx])
    
    # Low-load samples
    for idx, _ in stats['low_load'][:2]:
        if idx < len(data_points):
            sample_data.append(data_points[idx])
    
    prompt = f"""Generate system-level performance optimization recommendations based on this analysis:

Location: {config.location}
Total samples: {stats['count']}
High-load frames: {len(stats['high_load'])}
Peak: {stats['critical'][1]['draws']} draws, {format_number(stats['critical'][1]['tris'])} tris
Thresholds: {config.draw_hard_cap} draws, {format_number(config.tri_hard_cap, 0)} tris

Analyze the provided data table representing different performance zones (critical hotspots, high-load, and low-load frames) to understand patterns.

Generate recommendations organized by category:
1. LOD System (3-4 points)
2. Occlusion and Visibility (3-4 points)
3. Lighting and Shadows (3-4 points)
4. Materials and Textures (3-4 points)
5. Capture and Regression (3-4 points)

Format each category as:
<h3>Category Name</h3>
<ul class="body-text">
  <li>Recommendation 1</li>
  <li>Recommendation 2</li>
  ...
</ul>

Be specific, actionable, and relevant to the data."""
    
    results['full'] = call_llm_chunked(prompt, sample_data, config)
    
    return results


"""
LLM provider and prompt generation for BobReview.
"""

import os
import re
import statistics
import time
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ReportConfig

from .cache import get_cache
from .utils import log_verbose, log_warning, format_number
from .analysis import format_data_table
from .llm_registry import register_llm_generator, LLMGeneratorDefinition

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
    config: "Optional[ReportConfig]" = None,
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
                max_tokens=config.llm_max_tokens
            )
            # Clean the response to remove markdown code fences
            result = clean_llm_response(response.choices[0].message.content)
            
            # Cache the response
            if cache:
                cache.set(full_prompt, data_table or "", config.openai_model, result)
        
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
        else:
            return result
    
    raise RuntimeError(f"Failed to call OpenAI API after {max_retries} attempts")


def call_llm_chunked(
    prompt_base: str,
    data_points: List[Dict[str, Any]],
    config: "ReportConfig",
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
        # Build the chunks text separately to avoid backslash in f-string expression
        chunks_text = '\n'.join([f"Chunk {i+1}:\n{result}" for i, result in enumerate(results)])
        combine_prompt = f"""You have analyzed performance data in {len(results)} chunks. Combine these analyses into a single coherent response:

{chunks_text}

Provide a unified analysis that integrates all the information from these chunks."""
        return call_llm(combine_prompt, data_table=None, config=config)


def generate_executive_summary(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> str:
    """Generate executive summary using LLM."""
    critical_idx, critical_point = stats['critical']
    
    # Gather sample data points for context (critical, high-load, low-load)
    # Use a set to track seen indices and avoid duplicates
    sample_data: List[Dict[str, Any]] = []
    seen_indices: set[int] = set()
    
    # Include critical hotspot when index is valid
    critical_valid = False
    if 0 <= critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
        seen_indices.add(critical_idx)
        critical_valid = True
    else:
        log_warning(f"Critical index {critical_idx} out of range for {len(data_points)} samples", config)
    
    # Include a few high-load and low-load samples
    for idx, _ in stats['high_load'][:2]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    for idx, _ in stats['low_load'][:1]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    # Build peak hotspot description
    peak_hotspot_desc = (
        f"Index {critical_idx} with {critical_point['draws']} draws and {format_number(critical_point['tris'])} triangles"
        if critical_valid else "Data not available"
    )
    
    prompt = f"""You are analyzing a performance report for a game level/scene. Generate a concise executive summary (2-3 paragraphs) based on this data:

Location: {config.location}
Total samples: {stats['count']}

Draw Calls:
- Mean: {format_number(stats['draws']['mean'], 0)}, Median: {format_number(stats['draws']['median'], 0)}
- P90: {format_number(stats['draws']['p90'], 0)}, P95: {format_number(stats['draws']['p95'], 0)}, P99: {format_number(stats['draws']['p99'], 0)}
- CV (variability): {format_number(stats['draws']['cv'], 1)}%
- 95% CI: [{format_number(stats['confidence_intervals']['draws'][0], 0)}, {format_number(stats['confidence_intervals']['draws'][1], 0)}]
- Trend: {stats['trends']['draws']['direction']} (slope: {format_number(stats['trends']['draws']['slope'], 3)})

Triangles:
- Mean: {format_number(stats['tris']['mean'], 0)}, Median: {format_number(stats['tris']['median'], 0)}
- P90: {format_number(stats['tris']['p90'], 0)}, P95: {format_number(stats['tris']['p95'], 0)}, P99: {format_number(stats['tris']['p99'], 0)}
- CV (variability): {format_number(stats['tris']['cv'], 1)}%
- 95% CI: [{format_number(stats['confidence_intervals']['tris'][0], 0)}, {format_number(stats['confidence_intervals']['tris'][1], 0)}]
- Trend: {stats['trends']['tris']['direction']} (slope: {format_number(stats['trends']['tris']['slope'], 1)})

Frame Time Analysis:
- Mean interval: {format_number(stats['frame_times']['mean'], 1)}s, Median: {format_number(stats['frame_times']['median'], 1)}s
- Anomalies (hitches): {len(stats['frame_times']['anomalies'])} detected

Peak hotspot: {peak_hotspot_desc}
High-load frames: {len(stats['high_load'])} (threshold: ≥{config.high_load_draw_threshold} draws or ≥{format_number(config.high_load_tri_threshold, 0)} tris)
Low-load frames: {len(stats['low_load'])} (threshold: <{config.low_load_draw_threshold} draws and <{format_number(config.low_load_tri_threshold, 0)} tris)

Analyze the provided data table to understand performance patterns across different samples.

Write a professional executive summary that:
1. Summarizes overall performance health (reference P90/P95 values for realistic expectations)
2. Highlights key concerns based on trends and variability (CV indicates consistency)
3. Mentions the peak hotspot and its impact
4. Assesses variance and trend direction (improving/stable/degrading)
5. Comments on frame time stability if anomalies exist

Use HTML paragraph tags (<p>) for formatting. Be concise, data-driven, and reference the enhanced statistics (percentiles, trends, CV)."""

    return call_llm_chunked(prompt, sample_data, config)


def generate_metric_deep_dive(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> Dict[str, str]:
    """
    Generate metric deep dive sections using LLM.
    
    Returns an empty dict if data_points is empty.
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

Basic Statistics:
- Samples: {stats['count']}
- Min: {stats['draws']['min']}, Max: {stats['draws']['max']}
- Q1: {format_number(stats['draws']['q1'], 0)}, Median: {format_number(stats['draws']['median'], 0)}, Q3: {format_number(stats['draws']['q3'], 0)}
- Mean: {format_number(stats['draws']['mean'], 1)}, Std Dev: {format_number(stats['draws']['stdev'], 1)}

Advanced Metrics:
- P90: {format_number(stats['draws']['p90'], 0)}, P95: {format_number(stats['draws']['p95'], 0)}, P99: {format_number(stats['draws']['p99'], 0)}
- Variance: {format_number(stats['draws']['variance'], 1)}, CV: {format_number(stats['draws']['cv'], 1)}%
- 95% Confidence Interval: [{format_number(stats['confidence_intervals']['draws'][0], 0)}, {format_number(stats['confidence_intervals']['draws'][1], 0)}]
- Trend: {stats['trends']['draws']['direction']} (slope: {format_number(stats['trends']['draws']['slope'], 3)})

Outlier Detection (Multiple Methods):
- Sigma method (>2 sigma): {len(stats['draws']['outliers_high'])} high, {len(stats['draws']['outliers_low'])} low
- IQR method: {len(stats['outliers_iqr']['draws'])} outliers
- MAD method (robust): {len(stats['outliers_mad']['draws'])} outliers
- Hard cap threshold: {config.draw_hard_cap}

Analyze the provided data table to understand patterns in high and low draw call frames.

Write analysis covering:
1. Typical performance range (Q1-Q3) and P90/P95 expectations
2. Variability assessment (CV < 10% = consistent, 10-30% = moderate, >30% = high variance)
3. Trend direction and its implications (improving vs degrading)
4. Significance of outliers detected by different methods
5. Comparison to thresholds and confidence intervals

Use HTML paragraph tags. Be technical but accessible. Reference the advanced metrics."""
    
    results['draws'] = call_llm_chunked(prompt, draw_samples, config)
    
    # Triangle Count section
    tri_samples = []
    for idx, _ in stats['tris']['outliers_high'][:5]:
        if idx < len(data_points):
            tri_samples.append(data_points[idx])
    
    prompt = f"""Analyze triangle count performance data and write 2-3 paragraphs:

Basic Statistics:
- Samples: {stats['count']}
- Min: {format_number(stats['tris']['min'])}, Max: {format_number(stats['tris']['max'])}
- Q1: {format_number(stats['tris']['q1'])}, Median: {format_number(stats['tris']['median'])}, Q3: {format_number(stats['tris']['q3'])}
- Mean: {format_number(stats['tris']['mean'], 1)}, Std Dev: {format_number(stats['tris']['stdev'], 1)}

Advanced Metrics:
- P90: {format_number(stats['tris']['p90'], 0)}, P95: {format_number(stats['tris']['p95'], 0)}, P99: {format_number(stats['tris']['p99'], 0)}
- Variance: {format_number(stats['tris']['variance'], 0)}, CV: {format_number(stats['tris']['cv'], 1)}%
- 95% Confidence Interval: [{format_number(stats['confidence_intervals']['tris'][0], 0)}, {format_number(stats['confidence_intervals']['tris'][1], 0)}]
- Trend: {stats['trends']['tris']['direction']} (slope: {format_number(stats['trends']['tris']['slope'], 1)})

Outlier Detection (Multiple Methods):
- Sigma method (>2 sigma): {len(stats['tris']['outliers_high'])} high, {len(stats['tris']['outliers_low'])} low
- IQR method: {len(stats['outliers_iqr']['tris'])} outliers
- MAD method (robust): {len(stats['outliers_mad']['tris'])} outliers
- Hard cap threshold: {format_number(config.tri_hard_cap, 0)}

Analyze the provided data table to understand patterns in high triangle count frames.

Write analysis covering:
1. Distribution characteristics and P90/P95 expectations
2. Variability assessment using CV (coefficient of variation)
3. Trend direction (improving/stable/degrading) and implications for geometry budget
4. Impact of high outliers detected by different methods
5. Comparison to thresholds and confidence intervals
6. Geometry complexity assessment

Use HTML paragraph tags. Be technical but accessible. Reference the advanced metrics."""
    
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

Temporal Analysis:
- Time span: {time_span} seconds ({time_span/60:.1f} minutes)
- Average interval: {avg_interval:.1f} seconds
- No missing samples

Frame Time Analysis:
- Min frame time: {stats['frame_times']['min']}s, Max: {stats['frame_times']['max']}s
- Mean: {format_number(stats['frame_times']['mean'], 1)}s, Median: {format_number(stats['frame_times']['median'], 1)}s
- Frame time anomalies (>3x median): {len(stats['frame_times']['anomalies'])} detected
{f"- Anomaly indices: {', '.join([str(i) for i, _ in stats['frame_times']['anomalies'][:5]])}" if stats['frame_times']['anomalies'] else "- No significant frame time spikes"}

Correlation Analysis:
- Low draw call frames (bottom 10): avg {format_number(low_draw_tris, 0)} triangles
- High draw call frames (top 10): avg {format_number(high_draw_tris, 0)} triangles
- Draw calls trend: {stats['trends']['draws']['direction']}
- Triangles trend: {stats['trends']['tris']['direction']}

Analyze the provided data table showing low-draw and high-draw frames to understand the correlation.

Write 2-3 paragraphs:
1. Temporal behavior analysis including frame time stability (mention anomalies if present)
2. Performance trends over time (are things improving, stable, or degrading?)
3. Draw calls vs triangle correlation and its implications

Use HTML paragraph tags. Include a heading <h3>Temporal & Correlation Analysis</h3> before your analysis."""
    
    results['temporal'] = call_llm_chunked(prompt, corr_samples, config)
    
    return results


def generate_zones_hotspots(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
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
    config: "ReportConfig",
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
    
    # High-geometry hotspots - collect count and samples in single pass
    high_geo_samples: List[Dict[str, Any]] = []
    for idx, point in stats['high_load']:
        if point['tris'] >= config.high_load_tri_threshold and idx < len(data_points):
            high_geo_samples.append(data_points[idx])
    high_geo_count = len(high_geo_samples)
    
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
    config: "ReportConfig",
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate system-level recommendations using LLM."""
    results = {}
    
    # Gather representative data points from different performance zones
    # Use a set to track seen indices and avoid duplicates
    sample_data: List[Dict[str, Any]] = []
    seen_indices: set[int] = set()
    
    # Critical hotspot
    critical_idx = stats['critical'][0]
    if 0 <= critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
        seen_indices.add(critical_idx)
    else:
        log_warning(f"Critical index {critical_idx} out of range for {len(data_points)} samples", config)
    
    # High-load samples
    for idx, _ in stats['high_load'][:3]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    # Low-load samples
    for idx, _ in stats['low_load'][:2]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    prompt = f"""Generate system-level performance optimization recommendations based on this comprehensive analysis:

Location: {config.location}
Total samples: {stats['count']}

Performance Summary:
- Draw Calls: Mean {format_number(stats['draws']['mean'], 0)}, P90 {format_number(stats['draws']['p90'], 0)}, P95 {format_number(stats['draws']['p95'], 0)}
- Triangles: Mean {format_number(stats['tris']['mean'], 0)}, P90 {format_number(stats['tris']['p90'], 0)}, P95 {format_number(stats['tris']['p95'], 0)}
- Variability: Draw CV {format_number(stats['draws']['cv'], 1)}%, Tris CV {format_number(stats['tris']['cv'], 1)}%
- Trends: Draws {stats['trends']['draws']['direction']}, Tris {stats['trends']['tris']['direction']}

Critical Metrics:
- Peak hotspot: {stats['critical'][1]['draws']} draws, {format_number(stats['critical'][1]['tris'])} tris
- High-load frames: {len(stats['high_load'])}
- Frame time anomalies: {len(stats['frame_times']['anomalies'])}
- Thresholds: {config.draw_hard_cap} draws, {format_number(config.tri_hard_cap, 0)} tris

Analyze the provided data table representing different performance zones (critical hotspots, high-load, and low-load frames) to understand patterns.

Generate recommendations organized by category:
1. LOD System (3-4 points) - prioritize if triangles trend is degrading or CV is high
2. Occlusion and Visibility (3-4 points) - prioritize if draw calls are high
3. Lighting and Shadows (3-4 points)
4. Materials and Textures (3-4 points) - prioritize if draw call CV is high
5. Capture and Regression (3-4 points) - emphasize trend monitoring if trends are degrading

Format each category as:
<h3>Category Name</h3>
<ul class="body-text">
  <li>Recommendation 1</li>
  <li>Recommendation 2</li>
  ...
</ul>

Be specific, actionable, and relevant to the data. Reference the trends and variability metrics when making recommendations."""
    
    results['full'] = call_llm_chunked(prompt, sample_data, config)
    
    return results


def generate_visual_analysis(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> str:
    """Generate visual analysis interpretation for distribution charts."""
    
    prompt = f"""Analyze the distribution patterns in this performance data and write 2 paragraphs:

Draw Calls Distribution:
- Mean: {format_number(stats['draws']['mean'], 0)}, Median: {format_number(stats['draws']['median'], 0)}
- P90: {format_number(stats['draws']['p90'], 0)}, P95: {format_number(stats['draws']['p95'], 0)}, P99: {format_number(stats['draws']['p99'], 0)}
- Range: {stats['draws']['min']} to {stats['draws']['max']}
- Variance: {format_number(stats['draws']['variance'], 1)}, CV: {format_number(stats['draws']['cv'], 1)}%
- Trend: {stats['trends']['draws']['direction']}

Triangle Distribution:
- Mean: {format_number(stats['tris']['mean'], 0)}, Median: {format_number(stats['tris']['median'], 0)}
- P90: {format_number(stats['tris']['p90'], 0)}, P95: {format_number(stats['tris']['p95'], 0)}, P99: {format_number(stats['tris']['p99'], 0)}
- Range: {format_number(stats['tris']['min'])} to {format_number(stats['tris']['max'])}
- Variance: {format_number(stats['tris']['variance'], 0)}, CV: {format_number(stats['tris']['cv'], 1)}%
- Trend: {stats['trends']['tris']['direction']}

Write analysis covering:
1. What the distribution shape suggests (normal, skewed, bimodal, etc.)
2. Interpretation of the percentiles (P90/P95/P99 tell us about tail behavior)
3. Whether the distributions are consistent or highly variable (using CV)
4. What the trends indicate about performance trajectory

Use HTML paragraph tags (<p>). Be insightful and reference the specific metrics."""

    return call_llm(prompt, data_table=None, config=config)


def generate_statistical_interpretation(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> str:
    """Generate interpretation of advanced statistical metrics."""
    
    prompt = f"""Provide a concise interpretation (2 paragraphs) of these advanced performance statistics:

Variability Analysis:
- Draw Calls CV: {format_number(stats['draws']['cv'], 1)}% (< 10% = consistent, 10-30% = moderate, > 30% = high variance)
- Triangles CV: {format_number(stats['tris']['cv'], 1)}%

Confidence Intervals (95%):
- Draw Calls: [{format_number(stats['confidence_intervals']['draws'][0], 0)}, {format_number(stats['confidence_intervals']['draws'][1], 0)}]
- Triangles: [{format_number(stats['confidence_intervals']['tris'][0], 0)}, {format_number(stats['confidence_intervals']['tris'][1], 0)}]

Trend Analysis:
- Draw Calls: {stats['trends']['draws']['direction']} (slope: {format_number(stats['trends']['draws']['slope'], 3)})
- Triangles: {stats['trends']['tris']['direction']} (slope: {format_number(stats['trends']['tris']['slope'], 1)})

Frame Time Analysis:
- Mean: {format_number(stats['frame_times']['mean'], 1)}s, Median: {format_number(stats['frame_times']['median'], 1)}s
- Anomalies detected: {len(stats['frame_times']['anomalies'])}

Outlier Detection Consensus:
- Draws: Sigma method ({len(stats['draws']['outliers_high']) + len(stats['draws']['outliers_low'])}), IQR ({len(stats['outliers_iqr']['draws'])}), MAD ({len(stats['outliers_mad']['draws'])})
- Triangles: Sigma method ({len(stats['tris']['outliers_high']) + len(stats['tris']['outliers_low'])}), IQR ({len(stats['outliers_iqr']['tris'])}), MAD ({len(stats['outliers_mad']['tris'])})

Write interpretation covering:
1. Overall performance consistency and predictability (based on CV and confidence intervals)
2. Performance trajectory and whether action is needed (based on trends)
3. Frame time stability and any concerns (based on anomalies)
4. Reliability of outlier detection (consensus across methods)

Use HTML paragraph tags (<p>). Be practical and actionable."""

    return call_llm(prompt, data_table=None, config=config)


# Register all LLM generators
register_llm_generator(LLMGeneratorDefinition(
    section_name='Executive Summary',
    generator_func=generate_executive_summary,
    description='High-level performance overview and key findings'
))

register_llm_generator(LLMGeneratorDefinition(
    section_name='Metric Deep Dive',
    generator_func=generate_metric_deep_dive,
    description='Detailed draw calls and triangle count analysis'
))

register_llm_generator(LLMGeneratorDefinition(
    section_name='Zones & Hotspots',
    generator_func=generate_zones_hotspots,
    description='High-load and low-load frame analysis'
))

register_llm_generator(LLMGeneratorDefinition(
    section_name='Visual Analysis',
    generator_func=generate_visual_analysis,
    description='Distribution chart interpretation'
))

register_llm_generator(LLMGeneratorDefinition(
    section_name='Statistical Interpretation',
    generator_func=generate_statistical_interpretation,
    description='Advanced statistical metrics interpretation'
))

register_llm_generator(LLMGeneratorDefinition(
    section_name='Optimization Checklist',
    generator_func=generate_optimization_checklist,
    description='Actionable optimization recommendations'
))

register_llm_generator(LLMGeneratorDefinition(
    section_name='System Recommendations',
    generator_func=generate_system_recommendations,
    description='System-level architecture improvements'
))

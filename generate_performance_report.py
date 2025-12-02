#!/usr/bin/env python3
"""
Generate performance_report.html from captured PNG files using LLM analysis.

This script analyzes performance data from screenshots and generates
a comprehensive HTML report using LLM to analyze images and generate content.

Usage:
    python generate_performance_report.py --dir <path_to_images> --openai-key <key> --output performance_report.html
    python generate_performance_report.py --dir <path_to_images> --openai-key <key> --output report.html --title "My Level" --draw-cap 600 --tri-cap 120000
"""

import argparse
import os
import statistics
import json
import time
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    title: str = "Performance Analysis Report"
    location: str = "Unknown Location"
    draw_soft_cap: int = 550
    draw_hard_cap: int = 600
    tri_soft_cap: int = 100000
    tri_hard_cap: int = 120000
    high_load_draw_threshold: int = 600
    high_load_tri_threshold: int = 100000
    low_load_draw_threshold: int = 400
    low_load_tri_threshold: int = 50000
    outlier_sigma: float = 2.0
    enable_recommendations: bool = True
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    image_chunk_size: int = 10  # Number of data samples to send per LLM call


def parse_filename(filename):
    """Parse filename format: TestCase_tricount_drawcalls_timestamp.png"""
    parts = filename.replace('.png', '').split('_')
    if len(parts) < 4:
        raise ValueError(f"Invalid filename format: {filename}")
    testcase = parts[0]
    tricount = int(parts[1])
    drawcalls = int(parts[2])
    timestamp = int(parts[3])
    return {
        'testcase': testcase,
        'tris': tricount,
        'draws': drawcalls,
        'ts': timestamp,
        'img': filename
    }


def analyze_data(data_points, config: ReportConfig):
    """Calculate statistics and identify hotspots."""
    draws = [p['draws'] for p in data_points]
    tris = [p['tris'] for p in data_points]
    
    draw_mean = statistics.mean(draws)
    draw_stdev = statistics.stdev(draws) if len(draws) > 1 else 0
    tri_mean = statistics.mean(tris)
    tri_stdev = statistics.stdev(tris) if len(tris) > 1 else 0
    
    # Identify outliers (>Nσ from mean)
    sigma = config.outlier_sigma
    draw_outliers_high = [(i, p) for i, p in enumerate(data_points) 
                          if p['draws'] > draw_mean + sigma * draw_stdev]
    draw_outliers_low = [(i, p) for i, p in enumerate(data_points) 
                        if p['draws'] < draw_mean - sigma * draw_stdev]
    tri_outliers_high = [(i, p) for i, p in enumerate(data_points) 
                        if p['tris'] > tri_mean + sigma * tri_stdev]
    
    # High-load frames: configurable thresholds
    high_load = [(i, p) for i, p in enumerate(data_points) 
                 if p['draws'] >= config.high_load_draw_threshold or 
                    p['tris'] >= config.high_load_tri_threshold]
    
    # Low-load frames: configurable thresholds
    low_load = [(i, p) for i, p in enumerate(data_points) 
                if p['draws'] < config.low_load_draw_threshold and 
                   p['tris'] < config.low_load_tri_threshold]
    
    # Critical hotspot (worst frame)
    worst_idx = max(range(len(data_points)), 
                    key=lambda i: data_points[i]['draws'] + data_points[i]['tris'] / 1000)
    critical = (worst_idx, data_points[worst_idx])
    
    return {
        'draws': {
            'min': min(draws), 'max': max(draws), 'mean': draw_mean, 'median': statistics.median(draws),
            'q1': statistics.quantiles(draws, n=4)[0] if len(draws) > 1 else draws[0],
            'q3': statistics.quantiles(draws, n=4)[2] if len(draws) > 1 else draws[0],
            'stdev': draw_stdev,
            'outliers_high': draw_outliers_high,
            'outliers_low': draw_outliers_low
        },
        'tris': {
            'min': min(tris), 'max': max(tris), 'mean': tri_mean, 'median': statistics.median(tris),
            'q1': statistics.quantiles(tris, n=4)[0] if len(tris) > 1 else tris[0],
            'q3': statistics.quantiles(tris, n=4)[2] if len(tris) > 1 else tris[0],
            'stdev': tri_stdev,
            'outliers_high': tri_outliers_high
        },
        'high_load': high_load,
        'low_load': low_load,
        'critical': critical,
        'count': len(data_points)
    }


def format_number(n, decimals=1):
    """Format number with thousand separators."""
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


def format_data_table(data_points: List[Dict[str, Any]], max_rows: int = None) -> str:
    """Format data points as a markdown table for LLM."""
    if max_rows:
        data_points = data_points[:max_rows]
    
    if not data_points:
        return "No data available."
    
    # Create table header
    table = "| Index | Test Case | Draw Calls | Triangles | Timestamp |\n"
    table += "|-------|-----------|------------|-----------|----------|\n"
    
    # Add rows
    for idx, point in enumerate(data_points):
        table += f"| {idx} | {point['testcase']} | {point['draws']} | {format_number(point['tris'])} | {point['ts']} |\n"
    
    if max_rows and len(data_points) == max_rows:
        table += f"\n(Showing first {max_rows} of {len(data_points)} total samples)"
    
    return table


def clean_llm_response(response: str) -> str:
    """Clean LLM response by removing markdown code fences and extra formatting."""
    # Remove markdown code fences (```html, ```, etc.)
    # Remove opening code fence with optional language
    response = re.sub(r'^```[\w]*\s*\n?', '', response, flags=re.MULTILINE)
    # Remove closing code fence
    response = re.sub(r'\n?```\s*$', '', response, flags=re.MULTILINE)
    # Remove any remaining standalone code fences
    response = re.sub(r'\n```[\w]*\s*\n', '\n', response)
    response = re.sub(r'\n```\s*\n', '\n', response)
    
    return response.strip()


def call_llm(prompt: str, data_table: str = None, config: ReportConfig = None, max_retries: int = 3) -> str:
    """Call OpenAI API to generate text. Raises error if LLM is unavailable or fails."""
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI library not available. Install with: pip install openai")
    
    if not config:
        raise ValueError("ReportConfig is required")
    
    if not config.openai_api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --openai-key")
    else:
        api_key = config.openai_api_key
    
    client = openai.OpenAI(api_key=api_key)
    
    # Combine prompt with data table if provided
    full_prompt = prompt
    if data_table:
        full_prompt = f"""{prompt}

Data Table:
{data_table}"""
    
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
            return clean_llm_response(response.choices[0].message.content)
        
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
                print(f"Rate limit hit, retrying in {wait_time:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
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


def call_llm_chunked(prompt_base: str, data_points: List[Dict[str, Any]], config: ReportConfig, chunk_size: int = None) -> str:
    """Call LLM with data points in chunks and combine results."""
    if chunk_size is None:
        chunk_size = config.image_chunk_size
    
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


def generate_executive_summary(data_points, stats, config: ReportConfig, images_dir_rel: str) -> str:
    """Generate executive summary using LLM."""
    critical_idx = stats['critical'][0]
    critical_point = stats['critical'][1]
    
    # Gather sample data points for context (critical, high-load, low-load)
    sample_data = []
    # Include critical hotspot
    sample_data.append(data_points[critical_idx])
    
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


def generate_metric_deep_dive(data_points, stats, config: ReportConfig, images_dir_rel: str) -> Dict[str, str]:
    """Generate metric deep dive sections using LLM."""
    results = {}
    
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
- High outliers (>2σ): {len(stats['draws']['outliers_high'])} frames at indices {', '.join([str(i) for i, _ in stats['draws']['outliers_high']])}
- Low outliers (>2σ): {len(stats['draws']['outliers_low'])} frames at indices {', '.join([str(i) for i, _ in stats['draws']['outliers_low']])}
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
- High outliers (>2σ): {len(stats['tris']['outliers_high'])} frames at indices {', '.join([str(i) for i, _ in stats['tris']['outliers_high']])}
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


def generate_zones_hotspots(data_points, stats, config: ReportConfig, images_dir_rel: str) -> Dict[str, str]:
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


def generate_optimization_checklist(data_points, stats, config: ReportConfig, images_dir_rel: str) -> Dict[str, str]:
    """Generate optimization checklist using LLM."""
    results = {}
    
    critical_idx = stats['critical'][0]
    critical_point = stats['critical'][1]
    
    # Critical hotspot analysis - use the critical data point
    critical_samples = [data_points[critical_idx]] if critical_idx < len(data_points) else []
    
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


def generate_system_recommendations(data_points, stats, config: ReportConfig, images_dir_rel: str) -> Dict[str, str]:
    """Generate system-level recommendations using LLM."""
    results = {}
    
    # Gather representative data points from different performance zones
    sample_data = []
    # Critical hotspot
    critical_idx = stats['critical'][0]
    if critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
    
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


def generate_html(data_points, stats, images_dir_rel, output_path, config: ReportConfig):
    """Generate the complete HTML report."""
    
    # Calculate time span
    timestamps = [p['ts'] for p in data_points]
    time_span = max(timestamps) - min(timestamps)
    avg_interval = time_span / (len(data_points) - 1) if len(data_points) > 1 else 0
    
    # Correlation analysis
    sorted_by_draws = sorted(data_points, key=lambda x: x['draws'])
    low_draw_tris = statistics.mean([p['tris'] for p in sorted_by_draws[:10]])
    high_draw_tris = statistics.mean([p['tris'] for p in sorted_by_draws[-10:]])
    
    # Extract critical hotspot values for cleaner template
    critical_idx = stats['critical'][0]
    critical_point = stats['critical'][1]
    critical_draws = critical_point['draws']
    critical_tris = critical_point['tris']
    critical_tris_formatted = format_number(critical_tris)
    critical_img = critical_point['img']
    
    # Generate LLM content
    # Convert relative image path to absolute for LLM functions
    images_dir_abs = (output_path.parent / images_dir_rel).resolve() if images_dir_rel else output_path.parent
    
    print("Generating LLM content...")
    exec_summary = generate_executive_summary(data_points, stats, config, str(images_dir_abs))
    metric_content = generate_metric_deep_dive(data_points, stats, config, str(images_dir_abs))
    zones_content = generate_zones_hotspots(data_points, stats, config, str(images_dir_abs))
    optimization_content = generate_optimization_checklist(data_points, stats, config, str(images_dir_abs))
    system_recs = generate_system_recommendations(data_points, stats, config, str(images_dir_abs))
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{config.title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {{
      --bg: #070b10;
      --bg-elevated: #0e141b;
      --bg-soft: #151c26;
      --accent: #4ea1ff;
      --accent-soft: rgba(78, 161, 255, 0.15);
      --accent-strong: #ffb347;
      --text-main: #f5f7fb;
      --text-soft: #a8b3c5;
      --border-subtle: #1e2835;
      --danger: #ff5c5c;
      --warn: #e6b35c;
      --ok: #4fd18b;
      --mono: "SF Mono", Menlo, Consolas, monospace;
      --sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --radius-lg: 12px;
      --radius-md: 8px;
      --shadow-soft: 0 18px 45px rgba(0, 0, 0, 0.55);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 0;
      font-family: var(--sans);
      background: radial-gradient(circle at top left, #152033 0, #05080c 45%, #020308 100%);
      color: var(--text-main);
      -webkit-font-smoothing: antialiased;
    }}

    a {{
      color: var(--accent);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}

    .page {{
      max-width: 1200px;
      margin: 24px auto 48px;
      padding: 0 20px 32px;
    }}

    header {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 20px 24px 18px;
      margin-bottom: 20px;
      border-radius: var(--radius-lg);
      background: linear-gradient(135deg, rgba(78, 161, 255, 0.1), rgba(21, 25, 36, 0.95));
      border: 1px solid rgba(78, 161, 255, 0.4);
      box-shadow: var(--shadow-soft);
    }}

    header h1 {{
      margin: 0;
      font-size: 24px;
      letter-spacing: 0.03em;
    }}

    header .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 13px;
      color: var(--text-soft);
    }}

    header .meta span {{
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      background: rgba(4, 7, 14, 0.5);
    }}

    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
      gap: 20px;
      align-items: start;
    }}

    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: minmax(0, 1fr);
      }}
    }}

    .panel {{
      background: linear-gradient(145deg, rgba(9, 13, 20, 0.98), rgba(7, 11, 18, 0.98));
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      padding: 18px 20px 20px;
      box-shadow: var(--shadow-soft);
    }}

    .panel + .panel {{
      margin-top: 16px;
    }}

    .panel h2 {{
      margin: 0 0 10px;
      font-size: 18px;
      border-left: 3px solid var(--accent);
      padding-left: 8px;
    }}

    .panel h3 {{
      margin: 18px 0 6px;
      font-size: 15px;
      color: var(--text-soft);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-top: 6px;
    }}

    .stat-card {{
      padding: 12px 12px 10px;
      border-radius: var(--radius-md);
      background: radial-gradient(circle at top, rgba(78,161,255,0.16), rgba(13,19,29,0.96));
      border: 1px solid rgba(78, 161, 255, 0.45);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .stat-card.danger {{
      background: radial-gradient(circle at top, rgba(255,92,92,0.16), rgba(20,9,12,0.98));
      border-color: rgba(255,92,92,0.6);
    }}

    .stat-card.warn {{
      background: radial-gradient(circle at top, rgba(230,179,92,0.14), rgba(24,19,8,0.98));
      border-color: rgba(230,179,92,0.55);
    }}

    .stat-card.ok {{
      background: radial-gradient(circle at top, rgba(79,209,139,0.15), rgba(10,25,18,0.98));
      border-color: rgba(79,209,139,0.6);
    }}

    .stat-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-soft);
    }}

    .stat-value {{
      font-size: 20px;
      font-weight: 600;
    }}

    .stat-sub {{
      font-size: 12px;
      color: var(--text-soft);
    }}

    .body-text {{
      font-size: 14px;
      color: var(--text-soft);
      line-height: 1.6;
      margin: 4px 0 0;
    }}

    .body-text strong {{
      color: var(--text-main);
    }}

    .pill-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
      font-size: 12px;
    }}

    .pill {{
      padding: 4px 9px;
      border-radius: 999px;
      border: 1px solid var(--border-subtle);
      background: rgba(10, 14, 22, 0.9);
      color: var(--text-soft);
    }}

    .pill.ok {{
      border-color: rgba(79,209,139,0.65);
      color: var(--ok);
    }}

    .pill.warn {{
      border-color: rgba(230,179,92,0.65);
      color: var(--warn);
    }}

    .pill.danger {{
      border-color: rgba(255,92,92,0.7);
      color: var(--danger);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 8px;
      border-radius: var(--radius-md);
      overflow: hidden;
    }}

    thead {{
      background: linear-gradient(135deg, #192232, #111722);
    }}

    thead th {{
      padding: 8px 10px;
      text-align: left;
      font-weight: 500;
      color: var(--text-soft);
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
    }}

    tbody tr:nth-child(even) {{
      background: rgba(9, 13, 20, 0.9);
    }}

    tbody tr:nth-child(odd) {{
      background: rgba(5, 8, 15, 0.95);
    }}

    tbody td {{
      padding: 6px 10px;
      border-bottom: 1px solid rgba(13, 19, 30, 0.9);
      vertical-align: top;
      white-space: nowrap;
      color: var(--text-soft);
    }}

    tbody td.notes {{
      white-space: normal;
    }}

    tbody tr:hover {{
      background: rgba(78, 161, 255, 0.05);
    }}

    .thumb-small {{
      display: block;
      width: 80px;
      height: 60px;
      object-fit: cover;
      border-radius: 4px;
      margin-top: 4px;
      border: 1px solid var(--border-subtle);
      transform: scaleY(-1);
    }}

    .thumb-large {{
      display: block;
      width: 100%;
      max-width: 500px;
      height: auto;
      border-radius: var(--radius-md);
      margin: 12px 0;
      border: 1px solid var(--border-subtle);
      transform: scaleY(-1);
    }}

    .code-block {{
      font-family: var(--mono);
      font-size: 12px;
      background: rgba(4, 7, 14, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      white-space: pre;
      overflow-x: auto;
      color: var(--text-soft);
    }}

    .callout {{
      margin-top: 10px;
      padding: 10px 11px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
      background: rgba(10, 15, 24, 0.98);
      font-size: 13px;
      color: var(--text-soft);
    }}

    .callout-title {{
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
      color: var(--text-main);
    }}

    .callout.critical {{
      border-color: rgba(255,92,92,0.7);
      background: rgba(20,9,12,0.98);
    }}

    .callout.warn {{
      border-color: rgba(230,179,92,0.7);
      background: rgba(24,19,8,0.98);
    }}

    .metric-mono {{
      font-family: var(--mono);
      font-size: 12px;
      color: var(--text-main);
    }}

    .notes {{
      font-size: 11px;
      color: var(--text-soft);
      font-style: italic;
    }}

    .footer {{
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
      font-size: 12px;
      color: var(--text-soft);
      text-align: center;
    }}

    ul.body-text {{
      margin-left: 20px;
    }}

    ul.body-text li {{
      margin: 6px 0;
    }}

    .section-anchor {{
      scroll-margin-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>{config.title}</h1>
      <div class="meta">
        <span>{stats['count']} captures</span>
        <span>{config.location}</span>
        <span>Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
      </div>
      <div class="meta">
        <a href="#exec-summary">1. Executive summary</a>
        <a href="#metrics">2. Metric deep dive</a>
        <a href="#zones">3. Zones & hotspots</a>
        <a href="#checklist">4. Optimization checklist</a>
        <a href="#system-recs">5. System-level recommendations</a>
        <a href="#stats">6. Statistical summary</a>
        <a href="#table">7. Full sample table</a>
      </div>
    </header>

    <div class="layout">
      <main>
        <section id="exec-summary" class="panel section-anchor">
          <h2>1. Executive Summary</h2>
          <div class="summary-grid">
            <div class="stat-card ok">
              <div class="stat-label">Average performance</div>
              <div class="stat-value">{format_number(stats['draws']['mean'], 0)} draws</div>
              <div class="stat-sub">{format_number(stats['tris']['mean'], 0)} triangles &middot; median {format_number(stats['draws']['median'], 0)} / {format_number(stats['tris']['median'], 0)}</div>
            </div>
            <div class="stat-card danger">
              <div class="stat-label">Peak hotspot</div>
              <div class="stat-value">{critical_draws} draws</div>
              <div class="stat-sub">{format_number(critical_tris)} triangles (index {critical_idx})</div>
            </div>
            <div class="stat-card warn">
              <div class="stat-label">High-load frames</div>
              <div class="stat-value">{len(stats['high_load'])}</div>
              <div class="stat-sub">Draws ≥ {config.high_load_draw_threshold} or tris ≥ {format_number(config.high_load_tri_threshold, 0)}</div>
            </div>
          </div>
          {exec_summary}
          <div class="pill-row">
            <span class="pill ok">Average: {format_number(stats['draws']['mean'], 0)} draws / {format_number(stats['tris']['mean'], 0)} tris</span>
            <span class="pill warn">High variance detected</span>
            <span class="pill danger">Peak: {critical_draws} draws / {critical_tris_formatted} tris</span>
          </div>
        </section>

        <section id="metrics" class="panel section-anchor">
          <h2>2. Metric Deep Dive</h2>

          <h3>2.1 Draw Calls</h3>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Samples</td><td>{stats['count']}</td></tr>
              <tr><td>Min</td><td>{stats['draws']['min']}</td></tr>
              <tr><td>Q1</td><td>{format_number(stats['draws']['q1'], 0)}</td></tr>
              <tr><td>Median</td><td>{format_number(stats['draws']['median'], 0)}</td></tr>
              <tr><td>Q3</td><td>{format_number(stats['draws']['q3'], 0)}</td></tr>
              <tr><td>Max</td><td>{stats['draws']['max']}</td></tr>
              <tr><td>Mean</td><td>{format_number(stats['draws']['mean'], 1)}</td></tr>
              <tr><td>Std dev</td><td>{format_number(stats['draws']['stdev'], 1)}</td></tr>
            </tbody>
          </table>
          {metric_content['draws']}

          <h3>2.2 Triangle Count</h3>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Samples</td><td>{stats['count']}</td></tr>
              <tr><td>Min</td><td>{format_number(stats['tris']['min'])}</td></tr>
              <tr><td>Q1</td><td>{format_number(stats['tris']['q1'])}</td></tr>
              <tr><td>Median</td><td>{format_number(stats['tris']['median'])}</td></tr>
              <tr><td>Q3</td><td>{format_number(stats['tris']['q3'])}</td></tr>
              <tr><td>Max</td><td>{format_number(stats['tris']['max'])}</td></tr>
              <tr><td>Mean</td><td>{format_number(stats['tris']['mean'], 1)}</td></tr>
              <tr><td>Std dev</td><td>{format_number(stats['tris']['stdev'], 1)}</td></tr>
            </tbody>
          </table>
          {metric_content['tris']}

          {metric_content['temporal']}
        </section>

        <section id="zones" class="panel section-anchor">
          <h2>3. Performance Zones and Hotspots</h2>

          <h3>3.1 High‑Load Frames</h3>
          <p class="body-text">
            High‑load is defined as <strong>draw calls ≥ {config.high_load_draw_threshold}</strong> or
            <strong>triangle count ≥ {format_number(config.high_load_tri_threshold, 0)}</strong>.
          </p>
          <table>
            <thead>
              <tr>
                <th>Index</th>
                <th>Draws</th>
                <th>Tris</th>
                <th>Image</th>
              </tr>
            </thead>
            <tbody>
"""
    
    # High-load table
    for idx, point in stats['high_load']:
        html += f"""              <tr>
                <td>{idx}</td><td>{point['draws']}</td><td>{format_number(point['tris'])}</td>
                <td>
                  {point['img']}
                  <img class="thumb-small" src="{images_dir_rel}/{point['img']}" alt="Index {idx} high-load frame">
                </td>
              </tr>
"""
    
    html += f"""            </tbody>
          </table>
          {zones_content['high_load']}

          <h3>3.2 Low‑Load Baselines</h3>
          <p class="body-text">
            Low‑load frames (<strong>draws &lt; {config.low_load_draw_threshold}</strong> and <strong>tris &lt; {format_number(config.low_load_tri_threshold, 0)}</strong>)
            represent baseline performance and are useful design references.
          </p>
          {zones_content['low_load']}
          <table>
            <thead>
              <tr>
                <th>Index</th>
                <th>Draws</th>
                <th>Tris</th>
                <th>Image</th>
              </tr>
            </thead>
            <tbody>
"""
    
    # Low-load table
    for idx, point in stats['low_load']:
        html += f"""              <tr>
                <td>{idx}</td><td>{point['draws']}</td><td>{format_number(point['tris'])}</td>
                <td>
                  {point['img']}
                  <img class="thumb-small" src="{images_dir_rel}/{point['img']}" alt="Index {idx} low-load frame">
                </td>
              </tr>
"""
    
    html += f"""            </tbody>
          </table>

        </section>

        <section id="stats" class="panel section-anchor">
          <h2>6. Statistical Summary</h2>
          <h3>6.1 Draw Calls</h3>
          <div class="code-block">Minimum:    {stats['draws']['min']}
Q1:        {format_number(stats['draws']['q1'], 0)}
Median:    {format_number(stats['draws']['median'], 0)}
Q3:        {format_number(stats['draws']['q3'], 0)}
Maximum:   {stats['draws']['max']}
Mean:      {format_number(stats['draws']['mean'], 1)}
Std Dev:   {format_number(stats['draws']['stdev'], 1)}
          </div>

          <h3>6.2 Triangle Count</h3>
          <div class="code-block">Minimum:    {format_number(stats['tris']['min'])}
Q1:        {format_number(stats['tris']['q1'])}
Median:    {format_number(stats['tris']['median'])}
Q3:        {format_number(stats['tris']['q3'])}
Maximum:   {format_number(stats['tris']['max'])}
Mean:      {format_number(stats['tris']['mean'], 1)}
Std Dev:   {format_number(stats['tris']['stdev'], 1)}
          </div>
        </section>
      </main>

      <aside>
        <section id="checklist" class="panel section-anchor">
          <h2>4. Concrete Optimization Checklist</h2>

          <h3>4.1 Global Budgets</h3>
          <div class="summary-grid">
            <div class="stat-card ok">
              <div class="stat-label">Draw calls</div>
              <div class="stat-value">&le; {config.draw_soft_cap}</div>
              <div class="stat-sub">Soft cap {config.draw_soft_cap} &middot; hard cap {config.draw_hard_cap}</div>
            </div>
            <div class="stat-card ok">
              <div class="stat-label">Triangle count</div>
              <div class="stat-value">&le; {format_number(config.tri_soft_cap / 1000, 0)}k</div>
              <div class="stat-sub">Soft cap {format_number(config.tri_soft_cap, 0)} &middot; hard cap {format_number(config.tri_hard_cap, 0)}</div>
            </div>
          </div>
          <p class="body-text">
            Any capture exceeding the hard cap should be treated as a performance issue and scheduled
            for optimization work.
          </p>

          <h3>4.2 Critical Hotspot – Index CRITICAL_IDX_PLACEHOLDER</h3>
          <div class="callout critical">
            <div class="callout-title">Index CRITICAL_IDX_PLACEHOLDER – CRITICAL_IMG_PLACEHOLDER</div>
            <div>CRITICAL_DRAWS_PLACEHOLDER draw calls &middot; CRITICAL_TRIS_PLACEHOLDER triangles</div>
          </div>
          <img
            class="thumb-large"
            src="IMAGES_DIR_PLACEHOLDER/CRITICAL_IMG_PLACEHOLDER"
            alt="Critical hotspot frame (index CRITICAL_IDX_PLACEHOLDER)"
          />
          {optimization_content['critical']}

          <h3>4.3 High‑Geometry Hotspots</h3>
          <p class="body-text">
            Affects {len([p for _, p in stats['high_load'] if p['tris'] >= config.high_load_tri_threshold])} frame(s) above {format_number(config.high_load_tri_threshold, 0)} triangles.
          </p>
          {optimization_content['high_geometry']}

          <h3>4.4 High‑Draw Hotspots</h3>
          <p class="body-text">
            Focus on frames with draws ≥ {config.high_load_draw_threshold}.
          </p>
          {optimization_content['high_draw']}


        </section>
"""
    
    # System recommendations section (optional)
    if config.enable_recommendations and system_recs.get('full'):
        html += f"""
        <section id="system-recs" class="panel section-anchor">
          <h2>5. System‑Level Recommendations</h2>
          {system_recs['full']}
        </section>
"""
    
    html += """
        <section id="table" class="panel section-anchor">
          <h2>7. Full Sample Table</h2>
          <p class="body-text">
            Complete capture list for traceability.
          </p>
          <div style="max-height: 320px; overflow: auto; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); margin-top: 8px;">
            <table>
              <thead>
                <tr>
                  <th>Idx</th>
                  <th>Timestamp</th>
                  <th>Draws</th>
                  <th>Tris</th>
                  <th>Image</th>
                </tr>
              </thead>
              <tbody>
"""
    
    # Full table
    for idx, point in enumerate(data_points):
        html += f"""                <tr>
                  <td>{idx}</td><td>{point['ts']}</td><td>{point['draws']}</td><td>{format_number(point['tris'])}</td>
                  <td>
                    {point['img']}
                    <img class="thumb-small" src="{images_dir_rel}/{point['img']}" alt="Index {idx} frame">
                  </td>
                </tr>
"""
    
    html += """              </tbody>
            </table>
          </div>

          <div class="footer">
            Report generated from automated performance capture.  
            Intended for performance analysis and optimization planning.
          </div>
        </section>
      </aside>
    </div>
  </div>
</body>
</html>
"""
    
    # Replace critical hotspot placeholders
    html = html.replace('CRITICAL_IDX_PLACEHOLDER', str(critical_idx))
    html = html.replace('CRITICAL_IMG_PLACEHOLDER', critical_img)
    html = html.replace('CRITICAL_DRAWS_PLACEHOLDER', str(critical_draws))
    html = html.replace('CRITICAL_TRIS_PLACEHOLDER', critical_tris_formatted)
    html = html.replace('IMAGES_DIR_PLACEHOLDER', images_dir_rel)
    
    return html


def main():
    parser = argparse.ArgumentParser(
        description='Generate performance report HTML from captured PNG files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults
  python generate_performance_report.py --dir ./screenshots

  # Custom thresholds and title
  python generate_performance_report.py --dir ./screenshots --title "My Level Analysis" \\
    --draw-hard-cap 700 --tri-hard-cap 150000 --location "City District"

  # Use LLM to generate contextual content (requires OpenAI API key)
  python generate_performance_report.py --dir ./screenshots \\
    --openai-key sk-... --title "AI-Generated Analysis"

  # Or set OPENAI_API_KEY environment variable
  export OPENAI_API_KEY=sk-...
  python generate_performance_report.py --dir ./screenshots

  # Disable recommendations section
  python generate_performance_report.py --dir ./screenshots --no-recommendations
        """
    )
    parser.add_argument(
        '--dir', type=str, default='.',
        help='Directory containing PNG files (default: current directory)'
    )
    parser.add_argument(
        '--output', type=str, default='performance_report.html',
        help='Output HTML file (default: performance_report.html)'
    )
    parser.add_argument(
        '--images-dir', type=str, default=None,
        help='Relative path to images directory from output (auto-detected if not specified)'
    )
    parser.add_argument(
        '--title', type=str, default=None,
        help='Report title (default: "Performance Analysis Report")'
    )
    parser.add_argument(
        '--location', type=str, default=None,
        help='Location/level name (default: "Unknown Location")'
    )
    parser.add_argument(
        '--draw-soft-cap', type=int, default=550,
        help='Soft cap for draw calls (default: 550)'
    )
    parser.add_argument(
        '--draw-hard-cap', type=int, default=600,
        help='Hard cap for draw calls (default: 600)'
    )
    parser.add_argument(
        '--tri-soft-cap', type=int, default=100000,
        help='Soft cap for triangles (default: 100000)'
    )
    parser.add_argument(
        '--tri-hard-cap', type=int, default=120000,
        help='Hard cap for triangles (default: 120000)'
    )
    parser.add_argument(
        '--high-load-draws', type=int, default=None,
        help='High-load threshold for draw calls (default: same as draw-hard-cap)'
    )
    parser.add_argument(
        '--high-load-tris', type=int, default=None,
        help='High-load threshold for triangles (default: same as tri-hard-cap)'
    )
    parser.add_argument(
        '--low-load-draws', type=int, default=400,
        help='Low-load threshold for draw calls (default: 400)'
    )
    parser.add_argument(
        '--low-load-tris', type=int, default=50000,
        help='Low-load threshold for triangles (default: 50000)'
    )
    parser.add_argument(
        '--outlier-sigma', type=float, default=2.0,
        help='Sigma multiplier for outlier detection (default: 2.0)'
    )
    parser.add_argument(
        '--no-recommendations', action='store_true',
        help='Disable system-level recommendations section'
    )
    parser.add_argument(
        '--openai-key', type=str, default=None,
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )
    parser.add_argument(
        '--image-chunk-size', type=int, default=10,
        help='Number of data samples to send per LLM call (default: 10)'
    )
    parser.add_argument(
        '--openai-model', type=str, default='gpt-4o',
        help='OpenAI model to use (default: gpt-4o)'
    )
    parser.add_argument(
        '--llm-temperature', type=float, default=0.7,
        help='LLM temperature for generation (default: 0.7)'
    )
    
    args = parser.parse_args()
    
    # Check for OpenAI API key
    openai_key = args.openai_key or os.getenv('OPENAI_API_KEY')
    if not openai_key:
        parser.error("OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --openai-key")
    
    # Build configuration
    config = ReportConfig(
        title=args.title or "Performance Analysis Report",
        location=args.location or "Unknown Location",
        draw_soft_cap=args.draw_soft_cap,
        draw_hard_cap=args.draw_hard_cap,
        tri_soft_cap=args.tri_soft_cap,
        tri_hard_cap=args.tri_hard_cap,
        high_load_draw_threshold=args.high_load_draws or args.draw_hard_cap,
        high_load_tri_threshold=args.high_load_tris or args.tri_hard_cap,
        low_load_draw_threshold=args.low_load_draws,
        low_load_tri_threshold=args.low_load_tris,
        outlier_sigma=args.outlier_sigma,
        enable_recommendations=not args.no_recommendations,
        openai_api_key=openai_key,
        openai_model=args.openai_model,
        llm_temperature=args.llm_temperature,
        image_chunk_size=args.image_chunk_size
    )
    
    # Find PNG files
    input_dir = Path(args.dir).resolve()
    png_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.png')]
    
    if not png_files:
        print(f"Error: No PNG files found in {input_dir}")
        return 1
    
    print(f"Found {len(png_files)} PNG files")
    
    # Parse data
    data_points = []
    for png_file in png_files:
        try:
            data_points.append(parse_filename(png_file))
        except (ValueError, IndexError) as e:
            print(f"Warning: Skipping {png_file} - {e}")
            continue
    
    if not data_points:
        print("Error: No valid data points found")
        return 1
    
    # Sort by timestamp
    data_points.sort(key=lambda x: x['ts'])
    
    # Calculate statistics
    print("Analyzing data...")
    stats = analyze_data(data_points, config)
    
    # Determine image directory path
    output_path = Path(args.output).resolve()
    if args.images_dir:
        images_dir_rel = args.images_dir
    else:
        try:
            images_dir_rel = input_dir.relative_to(output_path.parent).as_posix()
        except ValueError:
            images_dir_rel = os.path.relpath(input_dir, output_path.parent).replace(os.sep, '/')
    
    # Generate HTML
    print(f"Generating report: {output_path}")
    html = generate_html(data_points, stats, images_dir_rel, output_path, config)
    
    # Write output
    output_path.write_text(html, encoding='utf-8')
    print(f"Success! Report written to {output_path}")
    print(f"  - {stats['count']} samples analyzed")
    print(f"  - {len(stats['high_load'])} high-load frames identified")
    print(f"  - Critical hotspot: index {stats['critical'][0]} ({stats['critical'][1]['draws']} draws, {format_number(stats['critical'][1]['tris'])} tris)")
    
    return 0


if __name__ == '__main__':
    exit(main())


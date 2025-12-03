#!/usr/bin/env python3
"""
HTML report generation for BobReview.
"""

import json
import math
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import quote

from .utils import format_number, log_info, log_verbose, log_warning, image_to_base64
from .llm_provider import (
    generate_executive_summary,
    generate_metric_deep_dive,
    generate_zones_hotspots,
    generate_optimization_checklist,
    generate_system_recommendations,
    generate_visual_analysis,
    generate_statistical_interpretation
)

# Check for tqdm availability
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    class tqdm:
        def __init__(self, iterable=None, _desc=None, _total=None, **_kwargs):
            self.iterable = iterable
        def __iter__(self):
            return iter(self.iterable)


def _prepare_timeline_data(data_points: List[Dict[str, Any]], metric: str, config) -> str:
    """
    Prepare timeline chart data for Chart.js.
    
    Parameters:
        data_points: List of data points
        metric: 'draws' or 'tris'
        config: Report configuration
    
    Returns:
        JSON string with chart data
    """
    data = []
    for i, point in enumerate(data_points):
        value = point[metric]
        # Classify performance zone
        if metric == 'draws':
            if value >= config.high_load_draw_threshold:
                color = 'rgba(255, 92, 92, 0.8)'  # red
            elif value < config.low_load_draw_threshold:
                color = 'rgba(79, 209, 139, 0.8)'  # green
            else:
                color = 'rgba(230, 179, 92, 0.8)'  # yellow
        else:  # tris
            if value >= config.high_load_tri_threshold:
                color = 'rgba(255, 92, 92, 0.8)'
            elif value < config.low_load_tri_threshold:
                color = 'rgba(79, 209, 139, 0.8)'
            else:
                color = 'rgba(230, 179, 92, 0.8)'
        
        data.append({
            'x': i,
            'y': value,
            'color': color,
            'label': f"Index {i}: {point['testcase']}"
        })
    
    return json.dumps(data)


def _prepare_scatter_data(data_points: List[Dict[str, Any]], config) -> str:
    """
    Prepare scatter plot data (draws vs tris) for Chart.js.
    
    Parameters:
        data_points: List of data points
        config: Report configuration
    
    Returns:
        JSON string with chart data
    """
    data = []
    for i, point in enumerate(data_points):
        draws = point['draws']
        tris = point['tris']
        
        # Classify by performance zone (both must be high for red)
        if (draws >= config.high_load_draw_threshold or 
            tris >= config.high_load_tri_threshold):
            color = 'rgba(255, 92, 92, 0.7)'
        elif (draws < config.low_load_draw_threshold and 
              tris < config.low_load_tri_threshold):
            color = 'rgba(79, 209, 139, 0.7)'
        else:
            color = 'rgba(230, 179, 92, 0.7)'
        
        data.append({
            'x': draws,
            'y': tris,
            'color': color,
            'label': f"Index {i}: {point['testcase']}"
        })
    
    return json.dumps(data)


def _prepare_histogram_data(values: List[float], num_bins: int = 20) -> Dict[str, Any]:
    """
    Prepare histogram data by calculating bins and frequencies.
    
    Parameters:
        values: List of numeric values
        num_bins: Number of histogram bins
    
    Returns:
        dict: Contains 'bins' (list of bin edges) and 'frequencies' (list of counts)
    """
    if not values:
        return {'bins': [], 'frequencies': []}
    
    min_val = min(values)
    max_val = max(values)
    
    # Handle edge case where all values are the same
    if min_val == max_val:
        return {
            'bins': [min_val],
            'frequencies': [len(values)]
        }
    
    bin_width = (max_val - min_val) / num_bins
    bins = [min_val + i * bin_width for i in range(num_bins + 1)]
    frequencies = [0] * num_bins
    
    for value in values:
        # Find which bin this value belongs to
        bin_index = int((value - min_val) / bin_width)
        # Handle edge case where value == max_val
        if bin_index >= num_bins:
            bin_index = num_bins - 1
        frequencies[bin_index] += 1
    
    # Create bin labels (midpoints)
    bin_labels = [(bins[i] + bins[i+1]) / 2 for i in range(num_bins)]
    
    return {
        'labels': bin_labels,
        'frequencies': frequencies
    }


def generate_html_report(
    data_points: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    images_dir_rel: str, 
    output_path: Path, 
    config
) -> str:
    """
    Builds a complete HTML performance report combining analysis, images, and LLM-generated sections.
    
    Parameters:
        data_points (List[dict]): Ordered list of parsed capture records (each with keys like 'ts', 'draws', 'tris', 'img').
        stats (dict): Aggregated analysis results (expected keys include 'draws', 'tris', 'high_load', 'low_load', 'critical', 'count').
        images_dir_rel (str): Path to the images directory relative to the output HTML file; used for image src attributes.
        output_path (Path): Destination file path for the generated HTML; used to resolve absolute image directory when composing prompts.
        config (ReportConfig): Report configuration (titles, thresholds, caps, LLM/cache options, and rendering flags).
    
    Returns:
        str: A complete HTML document as a string containing styled sections (executive summary, metric deep dive, zones & hotspots,
        optimization checklist, optional system recommendations), embedded thumbnails, statistical summaries, and a full sample table.
    """
    
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
    
    # Pre-encode all images to base64 if embed_images is enabled
    image_data_uris = {}
    if config.embed_images:
        log_info("Embedding images as base64 data URIs...", config)
        unique_images = set(point['img'] for point in data_points)
        for img_name in unique_images:
            img_path = images_dir_abs / img_name
            data_uri = image_to_base64(img_path)
            if data_uri:
                image_data_uris[img_name] = data_uri
            else:
                log_warning(f"Could not encode image: {img_name}", config)
        log_verbose(f"Encoded {len(image_data_uris)} images to base64", config)
    
    # Prepare chart data
    timeline_draws_data = _prepare_timeline_data(data_points, 'draws', config)
    timeline_tris_data = _prepare_timeline_data(data_points, 'tris', config)
    scatter_data = _prepare_scatter_data(data_points, config)
    
    # Prepare histogram data
    draws_values = [p['draws'] for p in data_points]
    tris_values = [p['tris'] for p in data_points]
    histogram_draws = _prepare_histogram_data(draws_values)
    histogram_tris = _prepare_histogram_data(tris_values)
    
    log_info("Generating LLM content...", config)
    
    sections = [
        ("Executive Summary", lambda: generate_executive_summary(data_points, stats, config, str(images_dir_abs))),
        ("Metric Deep Dive", lambda: generate_metric_deep_dive(data_points, stats, config, str(images_dir_abs))),
        ("Zones & Hotspots", lambda: generate_zones_hotspots(data_points, stats, config, str(images_dir_abs))),
        ("Visual Analysis", lambda: generate_visual_analysis(data_points, stats, config, str(images_dir_abs))),
        ("Statistical Interpretation", lambda: generate_statistical_interpretation(data_points, stats, config, str(images_dir_abs))),
        ("Optimization Checklist", lambda: generate_optimization_checklist(data_points, stats, config, str(images_dir_abs))),
    ]
    
    if config.enable_recommendations:
        sections.append(
            ("System Recommendations", lambda: generate_system_recommendations(data_points, stats, config, str(images_dir_abs)))
        )
    
    if TQDM_AVAILABLE and not config.quiet:
        iterator = tqdm(sections, desc="Generating sections")
    else:
        iterator = sections
    
    results = {}
    for section_name, generate_func in iterator:
        log_verbose(f"Generating: {section_name}", config)
        results[section_name] = generate_func()
    
    exec_summary = results["Executive Summary"]
    metric_content = results["Metric Deep Dive"]
    zones_content = results["Zones & Hotspots"]
    visual_analysis_content = results["Visual Analysis"]
    statistical_interpretation = results["Statistical Interpretation"]
    optimization_content = results["Optimization Checklist"]
    system_recs = results.get("System Recommendations", {})
    
    html = _generate_html_template(
        config, stats, data_points, images_dir_rel,
        critical_idx, critical_draws, critical_tris_formatted, critical_img,
        exec_summary, metric_content, zones_content, visual_analysis_content, 
        statistical_interpretation, optimization_content, system_recs,
        image_data_uris,
        timeline_draws_data, timeline_tris_data, scatter_data,
        histogram_draws, histogram_tris
    )
    
    return html


def _get_image_src(img_name: str, images_dir_rel: str, image_data_uris: Dict[str, str]) -> str:
    """
    Return the image source attribute value - either a base64 data URI or a relative file path.
    
    Parameters:
        img_name (str): The image filename.
        images_dir_rel (str): Relative path to images directory.
        image_data_uris (dict): Mapping of image names to base64 data URIs.
    
    Returns:
        str: Either a data URI or a relative file path for use in img src attribute.
    """
    if img_name in image_data_uris:
        return image_data_uris[img_name]
    if images_dir_rel:
        return f"{images_dir_rel}/{quote(img_name)}"
    return quote(img_name)


def _generate_html_template(
    config, stats, data_points, images_dir_rel,
    critical_idx, critical_draws, critical_tris_formatted, critical_img,
    exec_summary, metric_content, zones_content, visual_analysis_content,
    statistical_interpretation, optimization_content, system_recs,
    image_data_uris: Optional[Dict[str, str]] = None,
    timeline_draws_data: str = "[]",
    timeline_tris_data: str = "[]",
    scatter_data: str = "[]",
    histogram_draws: Optional[Dict[str, Any]] = None,
    histogram_tris: Optional[Dict[str, Any]] = None
) -> str:
    """Generate the HTML template with all content."""
    if image_data_uris is None:
        image_data_uris = {}
    if histogram_draws is None:
        histogram_draws = {'labels': [], 'frequencies': []}
    if histogram_tris is None:
        histogram_tris = {'labels': [], 'frequencies': []}
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{config.title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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

    .chart-container {{
      position: relative;
      width: 100%;
      margin: 16px 0;
      padding: 16px;
      background: rgba(4, 7, 14, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
    }}

    .chart-container canvas {{
      max-height: 320px;
    }}

    .chart-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .chart-description {{
      font-size: 12px;
      color: var(--text-soft);
      margin-bottom: 8px;
      line-height: 1.4;
    }}

    .trend-indicator {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .trend-indicator.improving {{
      background: rgba(79, 209, 139, 0.15);
      color: var(--ok);
      border: 1px solid rgba(79, 209, 139, 0.4);
    }}

    .trend-indicator.improving::before {{
      content: '↓';
      font-size: 14px;
    }}

    .trend-indicator.stable {{
      background: rgba(78, 161, 255, 0.15);
      color: var(--accent);
      border: 1px solid rgba(78, 161, 255, 0.4);
    }}

    .trend-indicator.stable::before {{
      content: '→';
      font-size: 14px;
    }}

    .trend-indicator.degrading {{
      background: rgba(255, 92, 92, 0.15);
      color: var(--danger);
      border: 1px solid rgba(255, 92, 92, 0.4);
    }}

    .trend-indicator.degrading::before {{
      content: '↑';
      font-size: 14px;
    }}

    .percentile-badge {{
      display: inline-block;
      padding: 2px 7px;
      margin: 2px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      font-family: var(--mono);
      background: rgba(78, 161, 255, 0.12);
      color: var(--accent);
      border: 1px solid rgba(78, 161, 255, 0.3);
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 10px;
      margin: 10px 0;
    }}

    .stats-item {{
      padding: 8px 10px;
      background: rgba(4, 7, 14, 0.6);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
    }}

    .stats-item-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-soft);
      margin-bottom: 4px;
    }}

    .stats-item-value {{
      font-size: 16px;
      font-weight: 600;
      font-family: var(--mono);
      color: var(--text-main);
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
        <a href="#visual-analysis">4. Visual analysis</a>
        <a href="#checklist">5. Optimization checklist</a>
        <a href="#system-recs">6. System-level recommendations</a>
        <a href="#stats">7. Statistical summary</a>
        <a href="#table">8. Full sample table</a>
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
              <div class="stat-sub">{format_number(stats['critical'][1]['tris'])} triangles (index {critical_idx})</div>
            </div>
            <div class="stat-card warn">
              <div class="stat-label">High-load frames</div>
              <div class="stat-value">{len(stats['high_load'])}</div>
              <div class="stat-sub">Draws ≥ {config.high_load_draw_threshold} or tris ≥ {format_number(config.high_load_tri_threshold, 0)}</div>
            </div>
          </div>
          <div style="margin-top: 12px;">
            <span class="percentile-badge">P90 Draws: {format_number(stats['draws']['p90'], 0)}</span>
            <span class="percentile-badge">P95 Draws: {format_number(stats['draws']['p95'], 0)}</span>
            <span class="percentile-badge">P99 Draws: {format_number(stats['draws']['p99'], 0)}</span>
            <span class="percentile-badge">P90 Tris: {format_number(stats['tris']['p90'], 0)}</span>
            <span class="percentile-badge">P95 Tris: {format_number(stats['tris']['p95'], 0)}</span>
          </div>
          <div style="margin-top: 8px;">
            <span style="font-size: 12px; color: var(--text-soft);">Trend: </span>
            <span class="trend-indicator {stats['trends']['draws']['direction']}">{stats['trends']['draws']['direction'].title()} Draws</span>
            <span class="trend-indicator {stats['trends']['tris']['direction']}">{stats['trends']['tris']['direction'].title()} Tris</span>
            <span style="font-size: 12px; color: var(--text-soft); margin-left: 8px;">CV: {format_number(stats['draws']['cv'], 1)}% draws / {format_number(stats['tris']['cv'], 1)}% tris</span>
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

          <h3>2.3 Timeline Visualizations</h3>
          <div class="chart-container">
            <div class="chart-title">Draw Calls Over Time</div>
            <p class="chart-description">
              Timeline showing draw call progression across captures. 
              <span style="color: var(--ok);">Green</span> = low load, 
              <span style="color: var(--warn);">Yellow</span> = medium, 
              <span style="color: var(--danger);">Red</span> = high load.
            </p>
            <canvas id="timeline-draws-chart"></canvas>
          </div>

          <div class="chart-container">
            <div class="chart-title">Triangle Count Over Time</div>
            <p class="chart-description">
              Timeline showing triangle count progression across captures.
            </p>
            <canvas id="timeline-tris-chart"></canvas>
          </div>

          <div class="chart-container">
            <div class="chart-title">Draw Calls vs Triangles (Scatter)</div>
            <p class="chart-description">
              Correlation between draw calls and triangle count. Each point represents one capture.
            </p>
            <canvas id="scatter-chart"></canvas>
          </div>

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
        img_src = _get_image_src(point['img'], images_dir_rel, image_data_uris)
        html += f"""              <tr>
                <td>{idx}</td><td>{point['draws']}</td><td>{format_number(point['tris'])}</td>
                <td>
                  {escape(point['img'])}
                  <img class="thumb-small" src="{img_src}" alt="Index {idx} high-load frame">
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
        img_src = _get_image_src(point['img'], images_dir_rel, image_data_uris)
        html += f"""              <tr>
                <td>{idx}</td><td>{point['draws']}</td><td>{format_number(point['tris'])}</td>
                <td>
                  {escape(point['img'])}
                  <img class="thumb-small" src="{img_src}" alt="Index {idx} low-load frame">
                </td>
              </tr>
"""
    
    html += f"""            </tbody>
          </table>

        </section>

        <section id="visual-analysis" class="panel section-anchor">
          <h2>4. Visual Analysis - Distribution Charts</h2>
          {visual_analysis_content}
          
          <h3>4.1 Draw Calls Distribution</h3>
          <div class="chart-container">
            <div class="chart-description">
              Frequency distribution showing how draw calls are distributed across captures.
              Vertical lines indicate key percentiles: <span style="color: var(--accent);">Median (P50)</span>, 
              <span style="color: var(--warn);">P90</span>, <span style="color: var(--danger);">P95</span>.
            </div>
            <canvas id="histogram-draws-chart"></canvas>
          </div>

          <h3>4.2 Triangle Count Distribution</h3>
          <div class="chart-container">
            <div class="chart-description">
              Frequency distribution showing how triangle counts are distributed across captures.
            </div>
            <canvas id="histogram-tris-chart"></canvas>
          </div>
        </section>

        <section id="stats" class="panel section-anchor">
          <h2>7. Statistical Summary</h2>
          {statistical_interpretation}
          
          <h3>7.1 Draw Calls</h3>
          <div class="code-block">Minimum:    {stats['draws']['min']}
Q1:        {format_number(stats['draws']['q1'], 0)}
Median:    {format_number(stats['draws']['median'], 0)}
Q3:        {format_number(stats['draws']['q3'], 0)}
Maximum:   {stats['draws']['max']}
Mean:      {format_number(stats['draws']['mean'], 1)}
Std Dev:   {format_number(stats['draws']['stdev'], 1)}
          </div>

          <h3>7.2 Triangle Count</h3>
          <div class="code-block">Minimum:    {format_number(stats['tris']['min'])}
Q1:        {format_number(stats['tris']['q1'])}
Median:    {format_number(stats['tris']['median'])}
Q3:        {format_number(stats['tris']['q3'])}
Maximum:   {format_number(stats['tris']['max'])}
Mean:      {format_number(stats['tris']['mean'], 1)}
Std Dev:   {format_number(stats['tris']['stdev'], 1)}
          </div>

          <h3>7.3 Percentile Analysis</h3>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls - P90</div>
              <div class="stats-item-value">{format_number(stats['draws']['p90'], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls - P95</div>
              <div class="stats-item-value">{format_number(stats['draws']['p95'], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls - P99</div>
              <div class="stats-item-value">{format_number(stats['draws']['p99'], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles - P90</div>
              <div class="stats-item-value">{format_number(stats['tris']['p90'], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles - P95</div>
              <div class="stats-item-value">{format_number(stats['tris']['p95'], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles - P99</div>
              <div class="stats-item-value">{format_number(stats['tris']['p99'], 0)}</div>
            </div>
          </div>

          <h3>7.4 Variability Metrics</h3>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls - Variance</div>
              <div class="stats-item-value">{format_number(stats['draws']['variance'], 1)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls - CV</div>
              <div class="stats-item-value">{format_number(stats['draws']['cv'], 1)}%</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles - Variance</div>
              <div class="stats-item-value">{format_number(stats['tris']['variance'], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles - CV</div>
              <div class="stats-item-value">{format_number(stats['tris']['cv'], 1)}%</div>
            </div>
          </div>
          <p class="body-text">
            <strong>Coefficient of Variation (CV)</strong> indicates relative variability: 
            &lt;10% = low variability, 10-30% = moderate, &gt;30% = high variability.
          </p>

          <h3>7.5 Confidence Intervals (95%)</h3>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls - Mean CI</div>
              <div class="stats-item-value">{format_number(stats['confidence_intervals']['draws'][0], 0)} - {format_number(stats['confidence_intervals']['draws'][1], 0)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles - Mean CI</div>
              <div class="stats-item-value">{format_number(stats['confidence_intervals']['tris'][0], 0)} - {format_number(stats['confidence_intervals']['tris'][1], 0)}</div>
            </div>
          </div>
          <p class="body-text">
            95% confidence intervals for the true population mean based on sample data.
          </p>

          <h3>7.6 Trend Analysis</h3>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls Trend</div>
              <div class="stats-item-value">
                <span class="trend-indicator {stats['trends']['draws']['direction']}">{stats['trends']['draws']['direction'].title()}</span>
              </div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles Trend</div>
              <div class="stats-item-value">
                <span class="trend-indicator {stats['trends']['tris']['direction']}">{stats['trends']['tris']['direction'].title()}</span>
              </div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Draw Calls Slope</div>
              <div class="stats-item-value">{format_number(stats['trends']['draws']['slope'], 3)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Triangles Slope</div>
              <div class="stats-item-value">{format_number(stats['trends']['tris']['slope'], 1)}</div>
            </div>
          </div>
          <p class="body-text">
            <strong>Trend analysis</strong> shows performance trajectory over time. 
            Improving = metrics decreasing (better), Stable = no significant change, Degrading = metrics increasing (worse).
          </p>

          <h3>7.7 Frame Time Analysis</h3>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item-label">Min Frame Time</div>
              <div class="stats-item-value">{stats['frame_times']['min']}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Max Frame Time</div>
              <div class="stats-item-value">{stats['frame_times']['max']}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Mean Frame Time</div>
              <div class="stats-item-value">{format_number(stats['frame_times']['mean'], 1)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Median Frame Time</div>
              <div class="stats-item-value">{format_number(stats['frame_times']['median'], 1)}</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Frame Time Anomalies</div>
              <div class="stats-item-value">{len(stats['frame_times']['anomalies'])}</div>
            </div>
          </div>
          <p class="body-text">
            Frame time deltas between consecutive captures. Anomalies are frame times exceeding 3x the median (potential hitches).
          </p>

          <h3>7.8 Outlier Detection Comparison</h3>
          <div class="stats-grid">
            <div class="stats-item">
              <div class="stats-item-label">Sigma Method (Draws)</div>
              <div class="stats-item-value">{len(stats['draws']['outliers_high']) + len(stats['draws']['outliers_low'])} outliers</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">IQR Method (Draws)</div>
              <div class="stats-item-value">{len(stats['outliers_iqr']['draws'])} outliers</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">MAD Method (Draws)</div>
              <div class="stats-item-value">{len(stats['outliers_mad']['draws'])} outliers</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">Sigma Method (Tris)</div>
              <div class="stats-item-value">{len(stats['tris']['outliers_high'])} outliers</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">IQR Method (Tris)</div>
              <div class="stats-item-value">{len(stats['outliers_iqr']['tris'])} outliers</div>
            </div>
            <div class="stats-item">
              <div class="stats-item-label">MAD Method (Tris)</div>
              <div class="stats-item-value">{len(stats['outliers_mad']['tris'])} outliers</div>
            </div>
          </div>
          <p class="body-text">
            Multiple outlier detection methods provide different perspectives. 
            <strong>Sigma:</strong> Based on standard deviations. 
            <strong>IQR:</strong> Interquartile range method (robust to extreme values). 
            <strong>MAD:</strong> Median Absolute Deviation (most robust, especially for non-normal distributions).
          </p>
        </section>
      </main>

      <aside>
        <section id="checklist" class="panel section-anchor">
          <h2>5. Concrete Optimization Checklist</h2>

          <h3>5.1 Global Budgets</h3>
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

          <h3>5.2 Critical Hotspot – Index {critical_idx}</h3>
          <div class="callout critical">
            <div class="callout-title">Index {critical_idx} – {escape(critical_img)}</div>
            <div>{critical_draws} draw calls &middot; {critical_tris_formatted} triangles</div>
          </div>
          <img
            class="thumb-large"
            src="{_get_image_src(critical_img, images_dir_rel, image_data_uris)}"
            alt="Critical hotspot frame (index {critical_idx})"
          />
          {optimization_content['critical']}

          <h3>5.3 High‑Geometry Hotspots</h3>
          <p class="body-text">
            Affects {len([p for _, p in stats['high_load'] if p['tris'] >= config.high_load_tri_threshold])} frame(s) above {format_number(config.high_load_tri_threshold, 0)} triangles.
          </p>
          {optimization_content['high_geometry']}

          <h3>5.4 High‑Draw Hotspots</h3>
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
          <h2>6. System‑Level Recommendations</h2>
          {system_recs['full']}
        </section>
"""
    
    html += f"""
        <section id="table" class="panel section-anchor">
          <h2>8. Full Sample Table</h2>
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
        img_src = _get_image_src(point['img'], images_dir_rel, image_data_uris)
        html += f"""                <tr>
                  <td>{idx}</td><td>{point['ts']}</td><td>{point['draws']}</td><td>{format_number(point['tris'])}</td>
                  <td>
                    {escape(point['img'])}
                    <img class="thumb-small" src="{img_src}" alt="Index {idx} frame">
                  </td>
                </tr>
"""
    
    html += f"""              </tbody>
            </table>
          </div>

          <div class="footer">
            Generated by BobReview - Performance Analysis and Review Tool
          </div>
        </section>
      </aside>
    </div>
  </div>

  <script>
    // Wait for DOM and Chart.js to be ready
    window.addEventListener('load', function() {{
      // Check if Chart.js is loaded
      if (typeof Chart === 'undefined') {{
        console.error('Chart.js failed to load');
        return;
      }}

      // Chart.js default configuration
      Chart.defaults.color = '#a8b3c5';
      Chart.defaults.borderColor = '#1e2835';
      Chart.defaults.font.family = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      Chart.defaults.font.size = 12;

      // Timeline - Draw Calls
      try {{
        const timelineDrawsData = {timeline_draws_data};
        console.log('Timeline draws data loaded:', timelineDrawsData.length, 'points');
        
        const canvasDraws = document.getElementById('timeline-draws-chart');
        if (!canvasDraws) {{
          console.error('Canvas element timeline-draws-chart not found');
          return;
        }}
        
        const ctxDraws = canvasDraws.getContext('2d');
        new Chart(ctxDraws, {{
      type: 'line',
      data: {{
        labels: timelineDrawsData.map((d, i) => i),
        datasets: [{{
          label: 'Draw Calls',
          data: timelineDrawsData.map(d => d.y),
          borderColor: 'rgba(78, 161, 255, 0.8)',
          backgroundColor: timelineDrawsData.map(d => d.color),
          pointBackgroundColor: timelineDrawsData.map(d => d.color),
          pointBorderColor: timelineDrawsData.map(d => d.color),
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.2,
          fill: false
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: function(context) {{
                const point = timelineDrawsData[context.dataIndex];
                return point.label + ': ' + point.y + ' draws';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            title: {{ display: true, text: 'Capture Index', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }}
          }},
          y: {{
            title: {{ display: true, text: 'Draw Calls', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            beginAtZero: true
          }}
        }}
      }}
    }});
      }} catch (error) {{
        console.error('Error creating timeline draws chart:', error);
      }}

      // Timeline - Triangles
      try {{
        const timelineTrisData = {timeline_tris_data};
        console.log('Timeline tris data loaded:', timelineTrisData.length, 'points');
        
        const canvasTris = document.getElementById('timeline-tris-chart');
        if (!canvasTris) {{
          console.error('Canvas element timeline-tris-chart not found');
          return;
        }}
        
        const ctxTris = canvasTris.getContext('2d');
        new Chart(ctxTris, {{
      type: 'line',
      data: {{
        labels: timelineTrisData.map((d, i) => i),
        datasets: [{{
          label: 'Triangles',
          data: timelineTrisData.map(d => d.y),
          borderColor: 'rgba(78, 161, 255, 0.8)',
          backgroundColor: timelineTrisData.map(d => d.color),
          pointBackgroundColor: timelineTrisData.map(d => d.color),
          pointBorderColor: timelineTrisData.map(d => d.color),
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.2,
          fill: false
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: function(context) {{
                const point = timelineTrisData[context.dataIndex];
                return point.label + ': ' + point.y.toLocaleString() + ' tris';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            title: {{ display: true, text: 'Capture Index', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }}
          }},
          y: {{
            title: {{ display: true, text: 'Triangles', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            beginAtZero: true,
            ticks: {{
              callback: function(value) {{
                return value >= 1000 ? (value/1000) + 'k' : value;
              }}
            }}
          }}
        }}
      }}
    }});
      }} catch (error) {{
        console.error('Error creating timeline tris chart:', error);
      }}

      // Scatter Plot - Draws vs Triangles
      try {{
        const scatterData = {scatter_data};
        console.log('Scatter data loaded:', scatterData.length, 'points');
        
        const canvasScatter = document.getElementById('scatter-chart');
        if (!canvasScatter) {{
          console.error('Canvas element scatter-chart not found');
          return;
        }}
        
        const ctxScatter = canvasScatter.getContext('2d');
        new Chart(ctxScatter, {{
      type: 'scatter',
      data: {{
        datasets: [{{
          label: 'Captures',
          data: scatterData.map(d => ({{ x: d.x, y: d.y }})),
          backgroundColor: scatterData.map(d => d.color),
          borderColor: scatterData.map(d => d.color.replace('0.7', '1')),
          borderWidth: 1,
          pointRadius: 5,
          pointHoverRadius: 7
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: function(context) {{
                const point = scatterData[context.dataIndex];
                return point.label + ' - ' + point.x + ' draws, ' + point.y.toLocaleString() + ' tris';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            title: {{ display: true, text: 'Draw Calls', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            beginAtZero: true
          }},
          y: {{
            title: {{ display: true, text: 'Triangles', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            beginAtZero: true,
            ticks: {{
              callback: function(value) {{
                return value >= 1000 ? (value/1000) + 'k' : value;
              }}
            }}
          }}
        }}
      }}
    }});
      }} catch (error) {{
        console.error('Error creating scatter chart:', error);
      }}

      // Histogram - Draw Calls Distribution
      try {{
        const histogramDrawsLabels = {json.dumps(histogram_draws['labels'])};
        const histogramDrawsFreq = {json.dumps(histogram_draws['frequencies'])};
        console.log('Histogram draws data loaded:', histogramDrawsLabels.length, 'bins');
        
        const canvasHistDraws = document.getElementById('histogram-draws-chart');
        if (!canvasHistDraws) {{
          console.error('Canvas element histogram-draws-chart not found');
          return;
        }}
        
        const ctxHistDraws = canvasHistDraws.getContext('2d');
        new Chart(ctxHistDraws, {{
      type: 'bar',
      data: {{
        labels: histogramDrawsLabels.map(x => Math.round(x)),
        datasets: [{{
          label: 'Frequency',
          data: histogramDrawsFreq,
          backgroundColor: 'rgba(78, 161, 255, 0.6)',
          borderColor: 'rgba(78, 161, 255, 1)',
          borderWidth: 1
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              title: function(context) {{
                return 'Draw Calls: ' + context[0].label;
              }},
              label: function(context) {{
                return 'Count: ' + context.parsed.y + ' captures';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            title: {{ display: true, text: 'Draw Calls (bin center)', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }}
          }},
          y: {{
            title: {{ display: true, text: 'Frequency', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            beginAtZero: true,
            ticks: {{ precision: 0 }}
          }}
        }}
      }}
    }});
      }} catch (error) {{
        console.error('Error creating histogram draws chart:', error);
      }}

      // Histogram - Triangles Distribution
      try {{
        const histogramTrisLabels = {json.dumps(histogram_tris['labels'])};
        const histogramTrisFreq = {json.dumps(histogram_tris['frequencies'])};
        console.log('Histogram tris data loaded:', histogramTrisLabels.length, 'bins');
        
        const canvasHistTris = document.getElementById('histogram-tris-chart');
        if (!canvasHistTris) {{
          console.error('Canvas element histogram-tris-chart not found');
          return;
        }}
        
        const ctxHistTris = canvasHistTris.getContext('2d');
        new Chart(ctxHistTris, {{
      type: 'bar',
      data: {{
        labels: histogramTrisLabels.map(x => Math.round(x)),
        datasets: [{{
          label: 'Frequency',
          data: histogramTrisFreq,
          backgroundColor: 'rgba(78, 161, 255, 0.6)',
          borderColor: 'rgba(78, 161, 255, 1)',
          borderWidth: 1
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              title: function(context) {{
                const val = context[0].label;
                return 'Triangles: ' + (val >= 1000 ? (val/1000).toFixed(1) + 'k' : val);
              }},
              label: function(context) {{
                return 'Count: ' + context.parsed.y + ' captures';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            title: {{ display: true, text: 'Triangle Count (bin center)', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            ticks: {{
              callback: function(value, index) {{
                const val = histogramTrisLabels[index];
                return val >= 1000 ? (val/1000).toFixed(1) + 'k' : Math.round(val);
              }}
            }}
          }},
          y: {{
            title: {{ display: true, text: 'Frequency', color: '#a8b3c5' }},
            grid: {{ color: 'rgba(30, 40, 53, 0.5)' }},
            beginAtZero: true,
            ticks: {{ precision: 0 }}
          }}
        }}
      }}
    }});
      }} catch (error) {{
        console.error('Error creating histogram tris chart:', error);
      }}

      console.log('All charts initialized successfully');
    }}); // End of window.addEventListener('load')
  </script>
</body>
</html>
"""
    
    return html


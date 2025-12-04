#!/usr/bin/env python3
"""
Base HTML utilities and shared components for BobReview reports.
"""

import json
import re
from html import escape
from typing import Dict, Any, Optional, List
from urllib.parse import quote


def sanitize_llm_html(content: str) -> str:
    """
    Sanitize LLM-generated HTML to prevent XSS while preserving safe formatting tags.
    
    Allows: p, strong, em, b, i, u, ul, ol, li, br, span, div
    Removes: script, iframe, object, embed, and dangerous attributes
    
    Parameters:
        content: HTML content from LLM
    
    Returns:
        Sanitized HTML string
    """
    if not content:
        return ""
    
    # Remove script tags and content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous tags
    dangerous_tags = ['iframe', 'object', 'embed', 'form', 'input', 'button', 'link', 'meta', 'style']
    for tag in dangerous_tags:
        content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(f'<{tag}[^>]*/?>', '', content, flags=re.IGNORECASE)
    
    # Remove dangerous attributes (on*, javascript:, data:)
    content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', content, flags=re.IGNORECASE)
    content = re.sub(r'(href|src)\s*=\s*["\']?\s*javascript:', r'\1="', content, flags=re.IGNORECASE)
    content = re.sub(r'(href|src)\s*=\s*["\']?\s*data:', r'\1="', content, flags=re.IGNORECASE)
    
    return content.strip()


def get_trend_icon(direction: str) -> str:
    """
    Return FontAwesome icon name for trend direction.
    
    Parameters:
        direction: Trend direction ('improving', 'degrading', or 'stable')
    
    Returns:
        FontAwesome icon name without 'fa-' prefix
    """
    if direction == 'improving':
        return 'arrow-down'
    elif direction == 'degrading':
        return 'arrow-up'
    else:  # stable
        return 'arrow-right'


def get_shared_css() -> str:
    """Return the shared CSS for all report pages."""
    return """
    :root {
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
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 0;
      font-family: var(--sans);
      background: radial-gradient(circle at top left, #152033 0, #05080c 45%, #020308 100%);
      color: var(--text-main);
      -webkit-font-smoothing: antialiased;
    }

    a {
      color: var(--accent);
      text-decoration: none;
    }

    a:hover {
      text-decoration: underline;
    }

    .page {
      max-width: 1200px;
      margin: 24px auto 48px;
      padding: 0 20px 32px;
    }

    header {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 20px 24px 18px;
      margin-bottom: 20px;
      border-radius: var(--radius-lg);
      background: linear-gradient(135deg, rgba(78, 161, 255, 0.1), rgba(21, 25, 36, 0.95));
      border: 1px solid rgba(78, 161, 255, 0.4);
      box-shadow: var(--shadow-soft);
    }

    header h1 {
      margin: 0;
      font-size: 24px;
      letter-spacing: 0.03em;
    }

    header .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      font-size: 13px;
      color: var(--text-soft);
    }

    header .meta span {
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      background: rgba(4, 7, 14, 0.5);
    }

    .nav-links {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      padding: 16px 20px;
      margin-bottom: 20px;
      border-radius: var(--radius-lg);
      background: rgba(14, 20, 27, 0.8);
      border: 1px solid var(--border-subtle);
    }

    .nav-links a {
      padding: 8px 16px;
      border-radius: 6px;
      background: rgba(78, 161, 255, 0.1);
      border: 1px solid rgba(78, 161, 255, 0.3);
      transition: all 0.2s;
    }

    .nav-links a:hover {
      background: rgba(78, 161, 255, 0.2);
      text-decoration: none;
      transform: translateY(-1px);
    }

    .nav-links a.active {
      background: var(--accent);
      color: var(--bg);
      font-weight: 600;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
      gap: 20px;
      align-items: start;
    }

    @media (max-width: 900px) {
      .layout {
        grid-template-columns: minmax(0, 1fr);
      }
    }

    .panel {
      background: linear-gradient(145deg, rgba(9, 13, 20, 0.98), rgba(7, 11, 18, 0.98));
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      padding: 18px 20px 20px;
      box-shadow: var(--shadow-soft);
    }

    .panel + .panel {
      margin-top: 16px;
    }

    .panel h2 {
      margin: 0 0 10px;
      font-size: 18px;
      border-left: 3px solid var(--accent);
      padding-left: 8px;
    }

    .panel h3 {
      margin: 18px 0 6px;
      font-size: 15px;
      color: var(--text-soft);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-top: 6px;
    }

    .stat-card {
      padding: 12px 12px 10px;
      border-radius: var(--radius-md);
      background: radial-gradient(circle at top, rgba(78,161,255,0.16), rgba(13,19,29,0.96));
      border: 1px solid rgba(78, 161, 255, 0.45);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .stat-card.danger {
      background: radial-gradient(circle at top, rgba(255,92,92,0.16), rgba(20,9,12,0.98));
      border-color: rgba(255,92,92,0.6);
    }

    .stat-card.warn {
      background: radial-gradient(circle at top, rgba(230,179,92,0.14), rgba(24,19,8,0.98));
      border-color: rgba(230,179,92,0.55);
    }

    .stat-card.ok {
      background: radial-gradient(circle at top, rgba(79,209,139,0.15), rgba(10,25,18,0.98));
      border-color: rgba(79,209,139,0.6);
    }

    .stat-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-soft);
    }

    .stat-value {
      font-size: 20px;
      font-weight: 600;
    }

    .stat-sub {
      font-size: 12px;
      color: var(--text-soft);
    }

    .body-text {
      font-size: 14px;
      color: var(--text-soft);
      line-height: 1.6;
      margin: 4px 0 0;
    }

    .body-text strong {
      color: var(--text-main);
    }

    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
      font-size: 12px;
    }

    .pill {
      padding: 4px 9px;
      border-radius: 999px;
      border: 1px solid var(--border-subtle);
      background: rgba(10, 14, 22, 0.9);
      color: var(--text-soft);
    }

    .pill.ok {
      border-color: rgba(79,209,139,0.65);
      color: var(--ok);
    }

    .pill.warn {
      border-color: rgba(230,179,92,0.65);
      color: var(--warn);
    }

    .pill.danger {
      border-color: rgba(255,92,92,0.7);
      color: var(--danger);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 8px;
      border-radius: var(--radius-md);
      overflow: hidden;
    }

    thead {
      background: linear-gradient(135deg, #192232, #111722);
    }

    thead th {
      padding: 8px 10px;
      text-align: left;
      font-weight: 500;
      color: var(--text-soft);
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
    }

    tbody tr:nth-child(even) {
      background: rgba(9, 13, 20, 0.9);
    }

    tbody tr:nth-child(odd) {
      background: rgba(5, 8, 15, 0.95);
    }

    tbody td {
      padding: 6px 10px;
      border-bottom: 1px solid rgba(13, 19, 30, 0.9);
      vertical-align: top;
      white-space: nowrap;
      color: var(--text-soft);
    }

    tbody td.notes {
      white-space: normal;
    }

    tbody tr:hover {
      background: rgba(78, 161, 255, 0.05);
    }

    .thumb-small {
      display: block;
      width: 80px;
      height: 60px;
      object-fit: cover;
      border-radius: 4px;
      margin-top: 4px;
      border: 1px solid var(--border-subtle);
      transform: scaleY(-1);
    }

    .thumb-large {
      display: block;
      width: 100%;
      max-width: 500px;
      height: auto;
      border-radius: var(--radius-md);
      margin: 12px 0;
      border: 1px solid var(--border-subtle);
      transform: scaleY(-1);
    }

    .code-block {
      font-family: var(--mono);
      font-size: 12px;
      background: rgba(4, 7, 14, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      white-space: pre;
      overflow-x: auto;
      color: var(--text-soft);
    }

    .callout {
      margin-top: 10px;
      padding: 10px 11px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
      background: rgba(10, 15, 24, 0.98);
      font-size: 13px;
      color: var(--text-soft);
    }

    .callout-title {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
      color: var(--text-main);
    }

    .callout.critical {
      border-color: rgba(255,92,92,0.7);
      background: rgba(20,9,12,0.98);
    }

    .callout.warn {
      border-color: rgba(230,179,92,0.7);
      background: rgba(24,19,8,0.98);
    }

    .metric-mono {
      font-family: var(--mono);
      font-size: 12px;
      color: var(--text-main);
    }

    .notes {
      font-size: 11px;
      color: var(--text-soft);
      font-style: italic;
    }

    .footer {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
      font-size: 12px;
      color: var(--text-soft);
      text-align: center;
    }

    ul.body-text {
      margin-left: 20px;
    }

    ul.body-text li {
      margin: 6px 0;
    }

    .section-anchor {
      scroll-margin-top: 20px;
    }

    .chart-container {
      position: relative;
      width: 100%;
      margin: 16px 0;
      padding: 16px;
      background: rgba(4, 7, 14, 0.8);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
    }

    .chart-container canvas {
      max-height: 320px;
    }

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
    }

    .chart-description {
      font-size: 12px;
      color: var(--text-soft);
      margin-bottom: 8px;
      line-height: 1.4;
    }

    .trend-indicator {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .trend-indicator.improving {
      background: rgba(79, 209, 139, 0.15);
      color: var(--ok);
      border: 1px solid rgba(79, 209, 139, 0.4);
    }

    .trend-indicator.improving i {
      font-size: 12px;
    }

    .trend-indicator.stable {
      background: rgba(78, 161, 255, 0.15);
      color: var(--accent);
      border: 1px solid rgba(78, 161, 255, 0.4);
    }

    .trend-indicator.stable i {
      font-size: 12px;
    }

    .trend-indicator.degrading {
      background: rgba(255, 92, 92, 0.15);
      color: var(--danger);
      border: 1px solid rgba(255, 92, 92, 0.4);
    }

    .trend-indicator.degrading i {
      font-size: 12px;
    }

    .percentile-badge {
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
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 10px;
      margin: 10px 0;
    }

    .stats-item {
      padding: 8px 10px;
      background: rgba(4, 7, 14, 0.6);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
    }

    .stats-item-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-soft);
      margin-bottom: 4px;
    }

    .stats-item-value {
      font-size: 16px;
      font-weight: 600;
      font-family: var(--mono);
      color: var(--text-main);
    }

    /* Card styles for homepage */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .feature-card {
      background: linear-gradient(135deg, rgba(14, 20, 27, 0.9), rgba(7, 11, 18, 0.95));
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-subtle);
      padding: 20px;
      transition: all 0.3s;
      cursor: pointer;
    }

    .feature-card:hover {
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(78, 161, 255, 0.15);
    }

    .feature-card h3 {
      margin: 0 0 8px 0;
      font-size: 16px;
      color: var(--text-main);
      text-transform: none;
    }

    .feature-card p {
      margin: 0;
      font-size: 13px;
      color: var(--text-soft);
      line-height: 1.5;
    }

    .feature-card .icon {
      font-size: 32px;
      margin-bottom: 12px;
      color: var(--accent);
    }
    
    .feature-card .icon i {
      display: block;
    }
    """


def get_page_header(title: str, subtitle: str = "", nav_items: Optional[List[tuple]] = None) -> str:
    """
    Generate a page header with navigation.
    
    Parameters:
        title: Page title
        subtitle: Optional subtitle
        nav_items: List of (label, url, is_active) tuples for navigation
    
    Returns:
        HTML string for the header
    """
    nav_html = ""
    if nav_items:
        nav_links = []
        for label, url, is_active in nav_items:
            active_class = ' class="active"' if is_active else ''
            nav_links.append(f'<a href="{escape(url)}"{active_class}>{escape(label)}</a>')
        nav_html = f'<div class="nav-links">{" ".join(nav_links)}</div>'
    
    subtitle_html = f'<div class="meta"><span>{escape(subtitle)}</span></div>' if subtitle else ''
    
    return f"""
    <header>
      <h1>{escape(title)}</h1>
      {subtitle_html}
    </header>
    {nav_html}
    """


def get_html_template(title: str, body_content: str, include_chartjs: bool = False) -> str:
    """
    Generate a complete HTML document with shared styles.
    
    Parameters:
        title: Page title (for <title> tag)
        body_content: HTML content for the body
        include_chartjs: Whether to include Chart.js library
    
    Returns:
        Complete HTML document as string
    """
    chartjs_script = ""
    if include_chartjs:
        chartjs_script = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>'
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{escape(title)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" integrity="sha512-z3gLpd7yknf1YoNbCzqRKc4qyor8gaKU1qmn+CShxbuBusANI9QpRohGBreCFkKxLhei6S9CQXFEbbKuqLg0DA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  {chartjs_script}
  <style>
{get_shared_css()}
  </style>
</head>
<body>
  <div class="page">
{body_content}
  </div>
</body>
</html>
"""


def get_image_src(img_name: str, images_dir_rel: str, image_data_uris: Dict[str, str]) -> str:
    """
    Return the image source attribute value - either a base64 data URI or a relative file path.
    
    Parameters:
        img_name: The image filename
        images_dir_rel: Relative path to images directory
        image_data_uris: Mapping of image names to base64 data URIs
    
    Returns:
        Either a data URI or a relative file path for use in img src attribute
    """
    if img_name in image_data_uris:
        return image_data_uris[img_name]
    if images_dir_rel:
        return f"{images_dir_rel}/{quote(img_name)}"
    return quote(img_name)


def prepare_timeline_data(data_points: List[Dict[str, Any]], metric: str, config) -> str:
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


def prepare_scatter_data(data_points: List[Dict[str, Any]], config) -> str:
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
        
        # Classify by performance zone (either draws or tris high = red)
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


def prepare_histogram_data(values: List[float], num_bins: int = 20) -> Dict[str, Any]:
    """
    Prepare histogram data by calculating bins and frequencies.
    
    Parameters:
        values: List of numeric values
        num_bins: Number of histogram bins
    
    Returns:
        dict: Contains 'labels' (list of bin centers) and 'frequencies' (list of counts)
    """
    if not values:
        return {'labels': [], 'frequencies': []}
    
    min_val = min(values)
    max_val = max(values)
    
    # Handle edge case where all values are the same
    if min_val == max_val:
        return {
            'labels': [min_val],
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


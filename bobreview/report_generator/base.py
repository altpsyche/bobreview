"""
Base HTML utilities and shared components for BobReview reports.
"""

import json
from html import escape
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import quote

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


def sanitize_llm_html(content: str) -> str:
    """
    Sanitize LLM-generated HTML to prevent XSS while preserving safe formatting tags.
    
    Uses the bleach library (whitelist-based approach) when available, otherwise
    returns escaped HTML as a fallback.
    
    Allowed tags: p, strong, em, b, i, u, ul, ol, li, br, span, div, h1-h6
    Allowed attributes: class (on span/div), href (on a)
    
    Parameters:
        content: HTML content from LLM
    
    Returns:
        Sanitized HTML string
    """
    if not content:
        return ""
    
    if not BLEACH_AVAILABLE:
        # Fallback: escape all HTML if bleach is not available
        return escape(content)
    
    # Whitelist of safe tags
    allowed_tags = [
        'p', 'strong', 'em', 'b', 'i', 'u', 
        'ul', 'ol', 'li', 'br', 'span', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'code', 'pre', 'blockquote'
    ]
    
    # Whitelist of safe attributes
    allowed_attributes = {
        'span': ['class'],
        'div': ['class'],
        'a': ['href'],
        'code': ['class']
    }
    
    # Whitelist of safe protocols for links
    allowed_protocols = ['http', 'https', 'mailto']
    
    # Sanitize using bleach
    sanitized = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True  # Strip disallowed tags instead of escaping them
    )
    
    return sanitized.strip()


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
    """
    Read shared CSS from external styles.css file.
    
    This function reads the CSS content from the styles.css file located in the
    same directory as this module. The CSS is the single source of truth for
    all report styling.
    
    Returns:
        str: Complete CSS content for embedding in HTML
    """
    from pathlib import Path
    css_path = Path(__file__).parent / "styles.css"
    return css_path.read_text(encoding='utf-8')


def get_css_source_path() -> Path:
    """
    Get the path to the source styles.css file.
    
    Returns:
        Path: Absolute path to styles.css in the package
    """
    from pathlib import Path
    return Path(__file__).parent / "styles.css"


def copy_css_to_output(output_dir: Path) -> Path:
    """
    Copy styles.css to the output directory.
    
    Parameters:
        output_dir: Directory where HTML files are being generated
    
    Returns:
        Path: Path to the copied CSS file
    """
    import shutil
    from pathlib import Path
    
    source = get_css_source_path()
    dest = Path(output_dir) / "styles.css"
    shutil.copy2(source, dest)
    return dest


# =============================================================================
# HTML Component Builders
# =============================================================================

def render_stat_card(label: str, value: str, subtitle: str = "", variant: str = "") -> str:
    """
    Render a stat-card HTML component.
    
    Parameters:
        label: Small label text at top (e.g., "Average Performance")
        value: Large value text (e.g., "450 draws")
        subtitle: Optional smaller text below value
        variant: CSS variant class - 'ok', 'warn', 'danger', or '' for default
    
    Returns:
        HTML string for the stat-card component
    """
    variant_class = f" {variant}" if variant else ""
    subtitle_html = f'<div class="stat-sub">{subtitle}</div>' if subtitle else ""
    
    return f'''<div class="stat-card{variant_class}">
  <div class="stat-label">{label}</div>
  <div class="stat-value">{value}</div>
  {subtitle_html}
</div>'''


def render_stats_item(label: str, value: str) -> str:
    """
    Render a stats-item HTML component.
    
    Parameters:
        label: Label text (e.g., "Total Captures")
        value: Value text (e.g., "150")
    
    Returns:
        HTML string for the stats-item component
    """
    return f'''<div class="stats-item">
  <div class="stats-item-label">{label}</div>
  <div class="stats-item-value">{value}</div>
</div>'''


def render_metric_table(metric_name: str, stats: Dict[str, Any], format_fn) -> str:
    """
    Render a metric statistics table (for draws or tris).
    
    Parameters:
        metric_name: Display name (e.g., "Draw Calls", "Triangle Count")
        stats: Dictionary with keys: min, max, q1, median, q3, mean, stdev, variance, cv
        format_fn: Function to format numbers (typically format_number from utils)
    
    Returns:
        HTML string for the metric table
    """
    return f'''<h3>{metric_name}</h3>
<table>
  <thead>
    <tr>
      <th>Metric</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Min</td><td>{format_fn(stats['min'])}</td></tr>
    <tr><td>Q1 (25th percentile)</td><td>{format_fn(stats['q1'], 0)}</td></tr>
    <tr><td>Median (50th percentile)</td><td>{format_fn(stats['median'], 0)}</td></tr>
    <tr><td>Q3 (75th percentile)</td><td>{format_fn(stats['q3'], 0)}</td></tr>
    <tr><td>Max</td><td>{format_fn(stats['max'])}</td></tr>
    <tr><td>Mean</td><td>{format_fn(stats['mean'], 1)}</td></tr>
    <tr><td>Std Dev</td><td>{format_fn(stats['stdev'], 1)}</td></tr>
    <tr><td>Variance</td><td>{format_fn(stats['variance'], 1)}</td></tr>
    <tr><td>CV (Coefficient of Variation)</td><td>{format_fn(stats['cv'], 1)}%</td></tr>
  </tbody>
</table>'''


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


def get_html_template(title: str, body_content: str, include_chartjs: bool = False, linked_css: bool = False, theme_id: str = None) -> str:
    """
    Generate a complete HTML document with shared styles.
    
    Parameters:
        title: Page title (for <title> tag)
        body_content: HTML content for the body
        include_chartjs: Whether to include Chart.js library
        linked_css: If True, link to external styles.css; if False, embed CSS inline
        theme_id: Optional theme ID to use (default: 'dark')
    
    Returns:
        Complete HTML document as string
    """
    from ..theme_registry import get_theme_css_variables
    
    chartjs_script = ""
    if include_chartjs:
        chartjs_script = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>'
    
    # Either link to external CSS or embed inline
    if linked_css:
        css_section = '<link rel="stylesheet" href="styles.css">'
    else:
        css_section = f'<style>\n{get_shared_css()}\n  </style>'
    
    # Add theme override if non-default theme
    theme_override = ''
    if theme_id and theme_id != 'dark':
        theme_css = get_theme_css_variables(theme_id)
        if theme_css:
            theme_override = f'<style>\n{theme_css}\n  </style>'
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{escape(title)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" integrity="sha512-z3gLpd7yknf1YoNbCzqRKc4qyor8gaKU1qmn+CShxbuBusANI9QpRohGBreCFkKxLhei6S9CQXFEbbKuqLg0DA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  {chartjs_script}
  {css_section}
  {theme_override}
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


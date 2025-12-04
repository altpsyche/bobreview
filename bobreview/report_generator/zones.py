"""
Zones and hotspots page generator for BobReview reports.
"""

from html import escape
from typing import Dict, List, Any
from .base import (
    get_html_template, 
    get_page_header, 
    get_image_src, 
    sanitize_llm_html,
    render_stat_card
)
from .registry import register_page, PageDefinition, get_nav_items
from ..utils import format_number


def generate_zones_page(
    stats: Dict[str, Any],
    images_dir_rel: str,
    image_data_uris: Dict[str, str],
    config,
    zones_content: Dict[str, str]
) -> str:
    """
    Generate the zones and hotspots analysis page.
    
    Parameters:
        stats: Aggregated analysis results
        images_dir_rel: Relative path to images directory
        image_data_uris: Mapping of image names to base64 data URIs
        config: Report configuration
        zones_content: Zone analysis content from LLM
    
    Returns:
        Complete HTML document for the zones page
    """
    nav_items = get_nav_items('zones.html')
    
    header = get_page_header("Performance Zones and Hotspots", f"{stats['count']} captures · {config.location}", nav_items)
    
    # Build high-load table
    high_load_rows = []
    for idx, point in stats['high_load']:
        img_src = get_image_src(point['img'], images_dir_rel, image_data_uris)
        high_load_rows.append(f"""
          <tr>
            <td>{idx}</td>
            <td>{point['draws']}</td>
            <td>{format_number(point['tris'])}</td>
            <td>
              {escape(point['img'])}
              <img class="thumb-small" src="{img_src}" alt="Index {idx} high-load frame">
            </td>
          </tr>
        """)
    
    high_load_table = "".join(high_load_rows) if high_load_rows else """
          <tr>
            <td colspan="4" style="text-align: center; font-style: italic;">No high-load frames detected</td>
          </tr>
    """
    
    # Build low-load table
    low_load_rows = []
    for idx, point in stats['low_load']:
        img_src = get_image_src(point['img'], images_dir_rel, image_data_uris)
        low_load_rows.append(f"""
          <tr>
            <td>{idx}</td>
            <td>{point['draws']}</td>
            <td>{format_number(point['tris'])}</td>
            <td>
              {escape(point['img'])}
              <img class="thumb-small" src="{img_src}" alt="Index {idx} low-load frame">
            </td>
          </tr>
        """)
    
    low_load_table = "".join(low_load_rows) if low_load_rows else """
          <tr>
            <td colspan="4" style="text-align: center; font-style: italic;">No low-load frames detected</td>
          </tr>
    """
    
    # Build critical hotspot section only if data is available
    critical_hotspot_section = ""
    if stats['count'] > 0 and stats.get('critical'):
        critical_idx, critical_point = stats['critical']
        critical_img_src = get_image_src(critical_point['img'], images_dir_rel, image_data_uris)
        critical_hotspot_section = f"""
    <section class="panel" style="margin-top: 20px;">
      <h2>Critical Hotspot</h2>
      <p class="body-text">
        The single worst-performing capture that demands the highest priority for optimization work.
      </p>
      
      <div class="callout critical">
        <div class="callout-title">Index {critical_idx} - {escape(critical_point['img'])}</div>
        <div>{critical_point['draws']} draw calls &middot; {format_number(critical_point['tris'])} triangles</div>
      </div>
      
      <img
        class="thumb-large"
        src="{critical_img_src}"
        alt="Critical hotspot frame (index {critical_idx})"
        style="max-width: 100%;"
      />
      
      <div class="body-text">
        <strong>Analysis:</strong> This frame represents the peak load in the capture session. 
        Focus optimization efforts here first, as improvements will have the most significant impact.
      </div>
    </section>
"""
    
    # Build stat cards using component
    high_pct = (len(stats['high_load']) / stats['count'] * 100) if stats['count'] > 0 else 0.0
    low_pct = (len(stats['low_load']) / stats['count'] * 100) if stats['count'] > 0 else 0.0
    medium_count = stats['count'] - len(stats['high_load']) - len(stats['low_load'])
    
    high_card = render_stat_card("High-Load Frames", str(len(stats['high_load'])), f"{high_pct:.1f}% of captures", "danger")
    medium_card = render_stat_card("Medium-Load Frames", str(medium_count), "Between thresholds", "warn")
    low_card = render_stat_card("Low-Load Frames", str(len(stats['low_load'])), f"{low_pct:.1f}% of captures", "ok")
    
    body_content = f"""{header}
    
    <section class="panel">
      <h2>Performance Zones Overview</h2>
      <p class="body-text">
        Performance zones categorize captures based on their resource usage. This helps identify 
        problematic areas requiring optimization and establish baseline performance expectations.
      </p>
      
      <div class="summary-grid">
        {high_card}
        {medium_card}
        {low_card}
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>High-Load Frames</h2>
      <p class="body-text">
        High-load is defined as <strong>draw calls ≥ {config.high_load_draw_threshold}</strong> or
        <strong>triangle count ≥ {format_number(config.high_load_tri_threshold, 0)}</strong>.
        These frames require immediate attention and optimization.
      </p>
      
      {sanitize_llm_html(zones_content.get('high_load', ''))}
      
      <table>
        <thead>
          <tr>
            <th>Index</th>
            <th>Draws</th>
            <th>Triangles</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
{high_load_table}
        </tbody>
      </table>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Low-Load Baselines</h2>
      <p class="body-text">
        Low-load frames (<strong>draws &lt; {config.low_load_draw_threshold}</strong> and 
        <strong>tris &lt; {format_number(config.low_load_tri_threshold, 0)}</strong>)
        represent baseline performance and are useful design references for optimal scenes.
      </p>
      
      {sanitize_llm_html(zones_content.get('low_load', ''))}
      
      <table>
        <thead>
          <tr>
            <th>Index</th>
            <th>Draws</th>
            <th>Triangles</th>
            <th>Image</th>
          </tr>
        </thead>
        <tbody>
{low_load_table}
        </tbody>
      </table>
    </section>
    
{critical_hotspot_section}
    
    <div class="footer">
      Generated by BobReview - <a href="index.html">Back to Home</a>
    </div>
"""
    
    return get_html_template(f"{config.title} - Zones & Hotspots", body_content, include_chartjs=False, linked_css=config.linked_css)


# Register this page
register_page(PageDefinition(
    id='zones',
    filename='zones.html',
    nav_label='Zones & Hotspots',
    nav_order=30,
    llm_section='Zones & Hotspots',
    page_generator=generate_zones_page,
    requires_images=True,
    requires_data_points=False
))

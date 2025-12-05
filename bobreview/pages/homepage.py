"""
Homepage generator for BobReview multi-page reports.
"""

from datetime import datetime
from typing import Dict, List, Any
from .base import (
    get_html_template, 
    get_page_header, 
    get_trend_icon, 
    sanitize_llm_html,
    render_stat_card,
    render_stats_item
)
from ..registry.pages import register_page, PageDefinition, get_nav_items, get_enabled_pages
from ..core.utils import format_number


def _generate_feature_cards(stats: Dict[str, Any]) -> str:
    """
    Generate feature cards dynamically from the page registry.
    Excludes the homepage itself.
    """
    cards = []
    for page in get_enabled_pages():
        if page.id == 'home':  # Skip homepage
            continue
        if not page.card_description:  # Skip pages without card info
            continue
        
        # Build dynamic pills based on page type
        pills = ""
        if page.id == 'zones':
            pills = f'''<div class="pill-row" style="margin-top: 12px;">
                <span class="pill danger">{len(stats['high_load'])} high-load</span>
                <span class="pill ok">{len(stats['low_load'])} low-load</span>
              </div>'''
        
        cards.append(f'''
        <a href="{page.filename}" style="text-decoration: none;">
          <div class="feature-card">
            <div class="icon"><i class="fas {page.card_icon}"></i></div>
            <h3>{page.nav_label}</h3>
            <p>{page.card_description}</p>
            {pills}
          </div>
        </a>''')
    
    return '\n'.join(cards)



def generate_homepage(
    stats: Dict[str, Any], 
    config,
    exec_summary: str
) -> str:
    """
    Generate the homepage/index with executive summary and links to detailed pages.
    
    Parameters:
        stats: Aggregated analysis results
        config: Report configuration
        exec_summary: Executive summary content from LLM (HTML string)
    
    Returns:
        Complete HTML document for the homepage
    """
    critical_idx = stats['critical'][0]
    critical_point = stats['critical'][1]
    critical_draws = critical_point['draws']
    critical_tris = format_number(critical_point['tris'])
    
    nav_items = get_nav_items('index.html')
    
    header = get_page_header(config.title, f"{stats['count']} captures · {config.location} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", nav_items)
    
    # Build stat cards
    avg_card = render_stat_card(
        "Average Performance",
        f"{format_number(stats['draws']['mean'], 0)} draws",
        f"{format_number(stats['tris']['mean'], 0)} triangles &middot; median {format_number(stats['draws']['median'], 0)} / {format_number(stats['tris']['median'], 0)}",
        "ok"
    )
    
    peak_card = render_stat_card(
        "Peak Hotspot",
        f"{critical_draws} draws",
        f"{critical_tris} triangles (index {critical_idx})",
        "danger"
    )
    
    highload_card = render_stat_card(
        "High-Load Frames",
        str(len(stats['high_load'])),
        f"Draws ≥ {config.high_load_draw_threshold} or tris ≥ {format_number(config.high_load_tri_threshold, 0)}",
        "warn"
    )
    
    # Build stats items
    stats_items = [
        render_stats_item("Total Captures", str(stats['count'])),
        render_stats_item("Draw Calls Range", f"{stats['draws']['min']} - {stats['draws']['max']}"),
        render_stats_item("Triangles Range", f"{format_number(stats['tris']['min'])} - {format_number(stats['tris']['max'])}"),
        render_stats_item("High-Load Frames", str(len(stats['high_load']))),
        render_stats_item("Low-Load Frames", str(len(stats['low_load']))),
        render_stats_item("Performance Variance", f"{format_number(stats['draws']['cv'], 1)}%"),
    ]
    
    body_content = f"""{header}
    
    <!-- Executive Summary Section -->
    <section class="panel">
      <h2>Executive Summary</h2>
      
      <div class="summary-grid">
        {avg_card}
        {peak_card}
        {highload_card}
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
        <span class="trend-indicator {stats['trends']['draws']['direction']}">
          <i class="fas fa-{get_trend_icon(stats['trends']['draws']['direction'])}"></i> {stats['trends']['draws']['direction'].title()} Draws
        </span>
        <span class="trend-indicator {stats['trends']['tris']['direction']}">
          <i class="fas fa-{get_trend_icon(stats['trends']['tris']['direction'])}"></i> {stats['trends']['tris']['direction'].title()} Tris
        </span>
        <span style="font-size: 12px; color: var(--text-soft); margin-left: 8px;">CV: {format_number(stats['draws']['cv'], 1)}% draws / {format_number(stats['tris']['cv'], 1)}% tris</span>
      </div>
      
      {sanitize_llm_html(exec_summary)}
      
      <div class="pill-row">
        <span class="pill ok">Average: {format_number(stats['draws']['mean'], 0)} draws / {format_number(stats['tris']['mean'], 0)} tris</span>
        {'<span class="pill warn">High variance detected</span>' if stats['draws']['cv'] > 30 or stats['tris']['cv'] > 30 else ''}
        <span class="pill danger">Peak: {critical_draws} draws / {critical_tris} tris</span>
      </div>
    </section>
    
    <!-- Navigation Cards -->
    <section class="panel" style="margin-top: 20px;">
      <h2>Detailed Analysis</h2>
      <p class="body-text">Explore different aspects of the performance analysis:</p>
      
      <div class="card-grid">
        {_generate_feature_cards(stats)}
      </div>
    </section>
    
    <!-- Quick Stats Section -->
    <section class="panel" style="margin-top: 20px;">
      <h2>Quick Statistics</h2>
      
      <div class="stats-grid">
        {''.join(stats_items)}
      </div>
    </section>
    
    <div class="footer">
      Generated by BobReview - Performance Analysis and Review Tool
    </div>
"""
    
    return get_html_template(f"{config.title} - Home", body_content, include_chartjs=False, linked_css=config.linked_css, theme_id=config.theme_id)


# Register this page
register_page(PageDefinition(
    id='home',
    filename='index.html',
    nav_label='Home',
    nav_order=10,
    llm_section='Executive Summary',
    page_generator=generate_homepage,
    requires_images=False,
    requires_data_points=False
))

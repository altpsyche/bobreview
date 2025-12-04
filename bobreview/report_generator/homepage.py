#!/usr/bin/env python3
"""
Homepage generator for BobReview multi-page reports.
"""

from datetime import datetime
from typing import Dict, List, Any
from .base import get_html_template, get_page_header, get_trend_icon, sanitize_llm_html
from ..utils import format_number


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
    
    nav_items = [
        ("Home", "index.html", True),
        ("Metrics", "metrics.html", False),
        ("Zones & Hotspots", "zones.html", False),
        ("Visual Analysis", "visuals.html", False),
        ("Optimization", "optimization.html", False),
        ("Statistics", "stats.html", False),
    ]
    
    header = get_page_header(config.title, f"{stats['count']} captures · {config.location} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}", nav_items)
    
    body_content = f"""{header}
    
    <!-- Executive Summary Section -->
    <section class="panel">
      <h2>Executive Summary</h2>
      
      <div class="summary-grid">
        <div class="stat-card ok">
          <div class="stat-label">Average Performance</div>
          <div class="stat-value">{format_number(stats['draws']['mean'], 0)} draws</div>
          <div class="stat-sub">{format_number(stats['tris']['mean'], 0)} triangles &middot; median {format_number(stats['draws']['median'], 0)} / {format_number(stats['tris']['median'], 0)}</div>
        </div>
        
        <div class="stat-card danger">
          <div class="stat-label">Peak Hotspot</div>
          <div class="stat-value">{critical_draws} draws</div>
          <div class="stat-sub">{critical_tris} triangles (index {critical_idx})</div>
        </div>
        
        <div class="stat-card warn">
          <div class="stat-label">High-Load Frames</div>
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
        <a href="metrics.html" style="text-decoration: none;">
          <div class="feature-card">
            <div class="icon"><i class="fas fa-chart-line"></i></div>
            <h3>Metric Deep Dive</h3>
            <p>Detailed statistical analysis of draw calls and triangle counts with interactive timelines and correlation charts.</p>
            <div class="pill-row" style="margin-top: 12px;">
              <span class="pill">Timeline charts</span>
              <span class="pill">Scatter plots</span>
            </div>
          </div>
        </a>
        
        <a href="zones.html" style="text-decoration: none;">
          <div class="feature-card">
            <div class="icon"><i class="fas fa-fire"></i></div>
            <h3>Zones & Hotspots</h3>
            <p>Identify high-load and low-load frames, critical hotspots, and performance zones requiring optimization.</p>
            <div class="pill-row" style="margin-top: 12px;">
              <span class="pill danger">{len(stats['high_load'])} high-load</span>
              <span class="pill ok">{len(stats['low_load'])} low-load</span>
            </div>
          </div>
        </a>
        
        <a href="visuals.html" style="text-decoration: none;">
          <div class="feature-card">
            <div class="icon"><i class="fas fa-chart-bar"></i></div>
            <h3>Visual Analysis</h3>
            <p>Distribution histograms and visual breakdowns showing performance patterns across all captures.</p>
            <div class="pill-row" style="margin-top: 12px;">
              <span class="pill">Histograms</span>
              <span class="pill">Distributions</span>
            </div>
          </div>
        </a>
        
        <a href="optimization.html" style="text-decoration: none;">
          <div class="feature-card">
            <div class="icon"><i class="fas fa-tasks"></i></div>
            <h3>Optimization Checklist</h3>
            <p>Actionable recommendations for addressing critical hotspots and high-load frames with budget guidelines.</p>
            <div class="pill-row" style="margin-top: 12px;">
              <span class="pill">Budgets</span>
              <span class="pill">Recommendations</span>
            </div>
          </div>
        </a>
        
        <a href="stats.html" style="text-decoration: none;">
          <div class="feature-card">
            <div class="icon"><i class="fas fa-calculator"></i></div>
            <h3>Statistical Summary</h3>
            <p>Comprehensive statistical analysis including percentiles, confidence intervals, and outlier detection.</p>
            <div class="pill-row" style="margin-top: 12px;">
              <span class="pill">Percentiles</span>
              <span class="pill">Outliers</span>
            </div>
          </div>
        </a>
        
        <div class="feature-card" style="opacity: 0.6; cursor: default;">
          <div class="icon"><i class="fas fa-table"></i></div>
          <h3>Full Sample Table</h3>
          <p>Complete capture list with all frames. View all {stats['count']} captures with timestamps, metrics, and thumbnails.</p>
        </div>
      </div>
    </section>
    
    <!-- Quick Stats Section -->
    <section class="panel" style="margin-top: 20px;">
      <h2>Quick Statistics</h2>
      
      <div class="stats-grid">
        <div class="stats-item">
          <div class="stats-item-label">Total Captures</div>
          <div class="stats-item-value">{stats['count']}</div>
        </div>
        
        <div class="stats-item">
          <div class="stats-item-label">Draw Calls Range</div>
          <div class="stats-item-value">{stats['draws']['min']} - {stats['draws']['max']}</div>
        </div>
        
        <div class="stats-item">
          <div class="stats-item-label">Triangles Range</div>
          <div class="stats-item-value">{format_number(stats['tris']['min'])} - {format_number(stats['tris']['max'])}</div>
        </div>
        
        <div class="stats-item">
          <div class="stats-item-label">High-Load Frames</div>
          <div class="stats-item-value">{len(stats['high_load'])}</div>
        </div>
        
        <div class="stats-item">
          <div class="stats-item-label">Low-Load Frames</div>
          <div class="stats-item-value">{len(stats['low_load'])}</div>
        </div>
        
        <div class="stats-item">
          <div class="stats-item-label">Performance Variance</div>
          <div class="stats-item-value">{format_number(stats['draws']['cv'], 1)}%</div>
        </div>
      </div>
    </section>
    
    <div class="footer">
      Generated by BobReview - Performance Analysis and Review Tool
    </div>
"""
    
    return get_html_template(f"{config.title} - Home", body_content, include_chartjs=False)


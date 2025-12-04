#!/usr/bin/env python3
"""
Visual analysis page generator with distribution charts.
"""

import json
from typing import Dict, List, Any
from .base import get_html_template, get_page_header, prepare_histogram_data, sanitize_llm_html
from ..utils import format_number


def generate_visuals_page(
    data_points: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    config,
    visual_analysis_content: str
) -> str:
    """
    Generate the visual analysis page with distribution charts.
    
    Parameters:
        data_points: List of parsed capture records
        stats: Aggregated analysis results
        config: Report configuration
        visual_analysis_content: Visual analysis content from LLM
    
    Returns:
        Complete HTML document for the visual analysis page
    """
    nav_items = [
        ("Home", "index.html", False),
        ("Metrics", "metrics.html", False),
        ("Zones & Hotspots", "zones.html", False),
        ("Visual Analysis", "visuals.html", True),
        ("Optimization", "optimization.html", False),
        ("Statistics", "stats.html", False),
    ]
    
    header = get_page_header("Visual Analysis - Distribution Charts", f"{stats['count']} captures · {config.location}", nav_items)
    
    # Prepare histogram data
    draws_values = [p['draws'] for p in data_points]
    tris_values = [p['tris'] for p in data_points]
    histogram_draws = prepare_histogram_data(draws_values)
    histogram_tris = prepare_histogram_data(tris_values)
    
    body_content = f"""{header}
    
    <section class="panel">
      <h2>Visual Analysis</h2>
      <p class="body-text">
        Distribution charts reveal patterns in performance data, showing how draw calls and triangle counts 
        are distributed across all captures. This helps identify clustering, outliers, and overall performance characteristics.
      </p>
      
      {sanitize_llm_html(visual_analysis_content)}
      
      <div class="summary-grid" style="margin-top: 16px;">
        <div class="stat-card">
          <div class="stat-label">Draw Calls Distribution</div>
          <div class="stat-value">{stats['draws']['min']} - {stats['draws']['max']}</div>
          <div class="stat-sub">Range of {stats['draws']['max'] - stats['draws']['min']} draws</div>
        </div>
        
        <div class="stat-card">
          <div class="stat-label">Triangles Distribution</div>
          <div class="stat-value">{format_number(stats['tris']['min'])} - {format_number(stats['tris']['max'])}</div>
          <div class="stat-sub">Range of {format_number(stats['tris']['max'] - stats['tris']['min'])} tris</div>
        </div>
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Draw Calls Distribution</h2>
      <p class="body-text">
        Frequency distribution showing how draw calls are distributed across captures.
        Vertical clusters indicate common performance levels, while outliers show exceptional cases.
      </p>
      
      <div class="chart-container">
        <div class="chart-description">
          This histogram shows the frequency of different draw call counts. 
          Key percentiles: <span style="color: var(--accent);">Median (P50)</span> at {format_number(stats['draws']['median'], 0)}, 
          <span style="color: var(--warn);">P90</span> at {format_number(stats['draws']['p90'], 0)}, 
          <span style="color: var(--danger);">P95</span> at {format_number(stats['draws']['p95'], 0)}.
        </div>
        <canvas id="histogram-draws-chart"></canvas>
      </div>
      
      <div class="stats-grid" style="margin-top: 16px;">
        <div class="stats-item">
          <div class="stats-item-label">Most Common Range</div>
          <div class="stats-item-value">Q1-Q3</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Q1 (25th percentile)</div>
          <div class="stats-item-value">{format_number(stats['draws']['q1'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Median (50th percentile)</div>
          <div class="stats-item-value">{format_number(stats['draws']['median'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Q3 (75th percentile)</div>
          <div class="stats-item-value">{format_number(stats['draws']['q3'], 0)}</div>
        </div>
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Triangle Count Distribution</h2>
      <p class="body-text">
        Frequency distribution showing how triangle counts are distributed across captures.
        This reveals geometry complexity patterns in your scenes.
      </p>
      
      <div class="chart-container">
        <div class="chart-description">
          This histogram shows the frequency of different triangle counts. 
          Key percentiles: <span style="color: var(--accent);">Median (P50)</span> at {format_number(stats['tris']['median'], 0)}, 
          <span style="color: var(--warn);">P90</span> at {format_number(stats['tris']['p90'], 0)}, 
          <span style="color: var(--danger);">P95</span> at {format_number(stats['tris']['p95'], 0)}.
        </div>
        <canvas id="histogram-tris-chart"></canvas>
      </div>
      
      <div class="stats-grid" style="margin-top: 16px;">
        <div class="stats-item">
          <div class="stats-item-label">Most Common Range</div>
          <div class="stats-item-value">Q1-Q3</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Q1 (25th percentile)</div>
          <div class="stats-item-value">{format_number(stats['tris']['q1'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Median (50th percentile)</div>
          <div class="stats-item-value">{format_number(stats['tris']['median'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Q3 (75th percentile)</div>
          <div class="stats-item-value">{format_number(stats['tris']['q3'], 0)}</div>
        </div>
      </div>
    </section>
    
    <div class="footer">
      Generated by BobReview - <a href="index.html">Back to Home</a>
    </div>
    
    <script>
      // Wait for DOM and Chart.js to be ready
      window.addEventListener('load', function() {{
        if (typeof Chart === 'undefined') {{
          console.error('Chart.js failed to load');
          return;
        }}

        // Chart.js default configuration
        Chart.defaults.color = '#a8b3c5';
        Chart.defaults.borderColor = '#1e2835';
        Chart.defaults.font.family = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        Chart.defaults.font.size = 12;

        // Histogram - Draw Calls Distribution
        try {{
          const histogramDrawsLabels = {json.dumps(histogram_draws['labels'])};
          const histogramDrawsFreq = {json.dumps(histogram_draws['frequencies'])};
          
          const canvasHistDraws = document.getElementById('histogram-draws-chart');
          if (!canvasHistDraws) throw new Error('Canvas not found');
          
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
          
          const canvasHistTris = document.getElementById('histogram-tris-chart');
          if (!canvasHistTris) throw new Error('Canvas not found');
          
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
      }});
    </script>
"""
    
    return get_html_template(f"{config.title} - Visual Analysis", body_content, include_chartjs=True)


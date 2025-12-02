#!/usr/bin/env python3
"""
HTML report generation for BobReview.
"""

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import quote

from .utils import format_number, log_info, log_verbose
from .llm_provider import (
    generate_executive_summary,
    generate_metric_deep_dive,
    generate_zones_hotspots,
    generate_optimization_checklist,
    generate_system_recommendations
)

# Check for tqdm availability
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    class tqdm:
        def __init__(self, iterable=None, desc=None, total=None, **kwargs):
            self.iterable = iterable
            self.desc = desc
        def __iter__(self):
            return iter(self.iterable)


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
    
    log_info("Generating LLM content...", config)
    
    sections = [
        ("Executive Summary", lambda: generate_executive_summary(data_points, stats, config, str(images_dir_abs))),
        ("Metric Deep Dive", lambda: generate_metric_deep_dive(data_points, stats, config, str(images_dir_abs))),
        ("Zones & Hotspots", lambda: generate_zones_hotspots(data_points, stats, config, str(images_dir_abs))),
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
    optimization_content = results["Optimization Checklist"]
    system_recs = results.get("System Recommendations", {})
    
    html = _generate_html_template(
        config, stats, data_points, images_dir_rel,
        critical_idx, critical_draws, critical_tris_formatted, critical_img,
        exec_summary, metric_content, zones_content, optimization_content, system_recs
    )
    
    return html


def _generate_html_template(
    config, stats, data_points, images_dir_rel,
    critical_idx, critical_draws, critical_tris_formatted, critical_img,
    exec_summary, metric_content, zones_content, optimization_content, system_recs
) -> str:
    """Generate the HTML template with all content."""
    
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
              <div class="stat-sub">{format_number(stats['critical'][1]['tris'])} triangles (index {critical_idx})</div>
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
                  {escape(point['img'])}
                  <img class="thumb-small" src="{images_dir_rel}/{quote(point['img'])}" alt="Index {idx} high-load frame">
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
                  {escape(point['img'])}
                  <img class="thumb-small" src="{images_dir_rel}/{quote(point['img'])}" alt="Index {idx} low-load frame">
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

          <h3>4.2 Critical Hotspot – Index {critical_idx}</h3>
          <div class="callout critical">
            <div class="callout-title">Index {critical_idx} – {escape(critical_img)}</div>
            <div>{critical_draws} draw calls &middot; {critical_tris_formatted} triangles</div>
          </div>
          <img
            class="thumb-large"
            src="{images_dir_rel}/{quote(critical_img)}"
            alt="Critical hotspot frame (index {critical_idx})"
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
                    {escape(point['img'])}
                    <img class="thumb-small" src="{images_dir_rel}/{quote(point['img'])}" alt="Index {idx} frame">
                  </td>
                </tr>
"""
    
    html += """              </tbody>
            </table>
          </div>

          <div class="footer">
            Generated by BobReview - Performance Analysis and Review Tool
          </div>
        </section>
      </aside>
    </div>
  </div>
</body>
</html>
"""
    
    return html


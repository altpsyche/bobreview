"""
Statistical summary page generator with comprehensive metrics.
"""

from html import escape
from typing import Dict, List, Any
from .base import get_html_template, get_page_header, get_image_src, get_trend_icon, sanitize_llm_html
from .registry import register_page, PageDefinition, get_nav_items
from ..utils import format_number


def generate_stats_page(
    data_points: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    images_dir_rel: str,
    image_data_uris: Dict[str, str],
    config,
    statistical_interpretation: str
) -> str:
    """
    Generate the comprehensive statistical summary page.
    
    Parameters:
        data_points: List of parsed capture records
        stats: Aggregated analysis results
        images_dir_rel: Relative path to images directory
        image_data_uris: Mapping of image names to base64 data URIs
        config: Report configuration
        statistical_interpretation: Statistical interpretation from LLM
    
    Returns:
        Complete HTML document for the statistics page
    """
    nav_items = get_nav_items('stats.html')
    
    header = get_page_header("Statistical Summary", f"{stats['count']} captures · {config.location}", nav_items)
    
    # Build full sample table
    table_rows = []
    for idx, point in enumerate(data_points):
        img_src = get_image_src(point['img'], images_dir_rel, image_data_uris)
        table_rows.append(f"""
          <tr>
            <td>{idx}</td>
            <td>{point['ts']}</td>
            <td>{point['draws']}</td>
            <td>{format_number(point['tris'])}</td>
            <td>
              {escape(point['img'])}
              <img class="thumb-small" src="{img_src}" alt="Index {idx} frame">
            </td>
          </tr>
        """)
    
    full_table = "".join(table_rows)
    
    body_content = f"""{header}
    
    <section class="panel">
      <h2>Statistical Summary</h2>
      <p class="body-text">
        Comprehensive statistical analysis of performance data including measures of central tendency, 
        dispersion, percentiles, and confidence intervals.
      </p>
      
      {sanitize_llm_html(statistical_interpretation)}
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Draw Calls Statistics</h2>
      
      <div class="code-block">Samples:   {stats['count']}
Minimum:   {stats['draws']['min']}
Q1:        {format_number(stats['draws']['q1'], 0)}
Median:    {format_number(stats['draws']['median'], 0)}
Q3:        {format_number(stats['draws']['q3'], 0)}
Maximum:   {stats['draws']['max']}
Mean:      {format_number(stats['draws']['mean'], 1)}
Std Dev:   {format_number(stats['draws']['stdev'], 1)}
Variance:  {format_number(stats['draws']['variance'], 1)}
CV:        {format_number(stats['draws']['cv'], 1)}%
IQR:       {format_number(stats['draws']['q3'] - stats['draws']['q1'], 0)}</div>
      
      <h3>Percentile Analysis</h3>
      <div class="stats-grid">
        <div class="stats-item">
          <div class="stats-item-label">P50 (Median)</div>
          <div class="stats-item-value">{format_number(stats['draws']['median'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P75</div>
          <div class="stats-item-value">{format_number(stats['draws']['q3'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P90</div>
          <div class="stats-item-value">{format_number(stats['draws']['p90'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P95</div>
          <div class="stats-item-value">{format_number(stats['draws']['p95'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P99</div>
          <div class="stats-item-value">{format_number(stats['draws']['p99'], 0)}</div>
        </div>
      </div>
      
      <h3>Outlier Detection</h3>
      <div class="stats-grid">
        <div class="stats-item">
          <div class="stats-item-label">Sigma Method (+/-{config.outlier_sigma} sigma)</div>
          <div class="stats-item-value">{len(stats['draws']['outliers_high']) + len(stats['draws']['outliers_low'])} outliers</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">IQR Method</div>
          <div class="stats-item-value">{len(stats['outliers_iqr']['draws'])} outliers</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">MAD Method</div>
          <div class="stats-item-value">{len(stats['outliers_mad']['draws'])} outliers</div>
        </div>
      </div>
      <p class="body-text" style="margin-top: 8px;">
        <strong>Sigma:</strong> Based on standard deviations. 
        <strong>IQR:</strong> Interquartile range method (robust to extremes). 
        <strong>MAD:</strong> Median Absolute Deviation (most robust for non-normal distributions).
      </p>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Triangle Count Statistics</h2>
      
      <div class="code-block">Samples:   {stats['count']}
Minimum:   {format_number(stats['tris']['min'])}
Q1:        {format_number(stats['tris']['q1'])}
Median:    {format_number(stats['tris']['median'])}
Q3:        {format_number(stats['tris']['q3'])}
Maximum:   {format_number(stats['tris']['max'])}
Mean:      {format_number(stats['tris']['mean'], 1)}
Std Dev:   {format_number(stats['tris']['stdev'], 1)}
Variance:  {format_number(stats['tris']['variance'], 0)}
CV:        {format_number(stats['tris']['cv'], 1)}%
IQR:       {format_number(stats['tris']['q3'] - stats['tris']['q1'])}</div>
      
      <h3>Percentile Analysis</h3>
      <div class="stats-grid">
        <div class="stats-item">
          <div class="stats-item-label">P50 (Median)</div>
          <div class="stats-item-value">{format_number(stats['tris']['median'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P75</div>
          <div class="stats-item-value">{format_number(stats['tris']['q3'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P90</div>
          <div class="stats-item-value">{format_number(stats['tris']['p90'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P95</div>
          <div class="stats-item-value">{format_number(stats['tris']['p95'], 0)}</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">P99</div>
          <div class="stats-item-value">{format_number(stats['tris']['p99'], 0)}</div>
        </div>
      </div>
      
      <h3>Outlier Detection</h3>
      <div class="stats-grid">
        <div class="stats-item">
          <div class="stats-item-label">Sigma Method (+/-{config.outlier_sigma} sigma)</div>
          <div class="stats-item-value">{len(stats['tris']['outliers_high']) + len(stats['tris']['outliers_low'])} outliers</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">IQR Method</div>
          <div class="stats-item-value">{len(stats['outliers_iqr']['tris'])} outliers</div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">MAD Method</div>
          <div class="stats-item-value">{len(stats['outliers_mad']['tris'])} outliers</div>
        </div>
      </div>
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Confidence Intervals (95%)</h2>
      <p class="body-text">
        95% confidence intervals for the true population mean based on sample data. 
        This range indicates where we expect the true mean to lie with 95% confidence.
      </p>
      
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
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Variability Metrics</h2>
      <p class="body-text">
        <strong>Coefficient of Variation (CV)</strong> indicates relative variability: 
        &lt;10% = low variability, 10-30% = moderate, &gt;30% = high variability.
        High variability suggests inconsistent performance across scenes.
      </p>
      
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
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Trend Analysis</h2>
      <p class="body-text">
        <strong>Trend analysis</strong> shows performance trajectory over time. 
        Improving = metrics decreasing (better), Stable = no significant change, Degrading = metrics increasing (worse).
      </p>
      
      <div class="stats-grid">
        <div class="stats-item">
          <div class="stats-item-label">Draw Calls Trend</div>
          <div class="stats-item-value">
            <span class="trend-indicator {stats['trends']['draws']['direction']}">
              <i class="fas fa-{get_trend_icon(stats['trends']['draws']['direction'])}"></i> {stats['trends']['draws']['direction'].title()}
            </span>
          </div>
        </div>
        <div class="stats-item">
          <div class="stats-item-label">Triangles Trend</div>
          <div class="stats-item-value">
            <span class="trend-indicator {stats['trends']['tris']['direction']}">
              <i class="fas fa-{get_trend_icon(stats['trends']['tris']['direction'])}"></i> {stats['trends']['tris']['direction'].title()}
            </span>
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
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Frame Time Analysis</h2>
      <p class="body-text">
        Frame time deltas between consecutive captures. Anomalies are frame times exceeding 3x the median 
        (potential hitches or performance spikes).
      </p>
      
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
    </section>
    
    <section class="panel" style="margin-top: 20px;">
      <h2>Full Sample Table</h2>
      <p class="body-text">
        Complete capture list for traceability and detailed analysis.
      </p>
      
      <div style="max-height: 500px; overflow: auto; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); margin-top: 8px;">
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
{full_table}
          </tbody>
        </table>
      </div>
    </section>
    
    <div class="footer">
      Generated by BobReview - <a href="index.html">Back to Home</a>
    </div>
"""
    
    return get_html_template(f"{config.title} - Statistics", body_content, include_chartjs=False, linked_css=config.linked_css)


# Register this page
register_page(PageDefinition(
    id='stats',
    filename='stats.html',
    nav_label='Statistics',
    nav_order=60,
    llm_section='Statistical Interpretation',
    page_generator=generate_stats_page,
    requires_images=True,
    requires_data_points=True
))

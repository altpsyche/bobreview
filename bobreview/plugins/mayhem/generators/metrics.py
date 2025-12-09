"""Metric deep dive generator."""

import statistics
from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from bobreview.core.utils import format_number, log_warning
from bobreview.services.llm.client import call_llm_chunked


def generate_metric_deep_dive(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate metric deep dive sections using LLM."""
    results: Dict[str, str] = {}
    
    if not data_points:
        log_warning("No data points for metric deep dive", config)
        return results
    
    # Draw calls analysis
    draw_samples = []
    for idx, _ in stats['draws']['outliers_high'][:5]:
        if idx < len(data_points):
            draw_samples.append(data_points[idx])
    for idx, _ in stats['draws']['outliers_low'][:2]:
        if idx < len(data_points):
            draw_samples.append(data_points[idx])
    
    prompt = f"""Analyze draw call performance (2-3 paragraphs):

Statistics:
- Samples: {stats['count']}, Min: {stats['draws']['min']}, Max: {stats['draws']['max']}
- Q1: {format_number(stats['draws']['q1'], 0)}, Median: {format_number(stats['draws']['median'], 0)}, Q3: {format_number(stats['draws']['q3'], 0)}
- P90: {format_number(stats['draws']['p90'], 0)}, P95: {format_number(stats['draws']['p95'], 0)}, P99: {format_number(stats['draws']['p99'], 0)}
- CV: {format_number(stats['draws']['cv'], 1)}%, Trend: {stats['trends']['draws']['direction']}

Outliers:
- Sigma method: {len(stats['draws']['outliers_high'])} high, {len(stats['draws']['outliers_low'])} low
- IQR method: {len(stats['outliers_iqr']['draws'])}, MAD method: {len(stats['outliers_mad']['draws'])}

Cover performance expectations, variability, and outlier significance. Use HTML <p> tags."""

    results['draws'] = call_llm_chunked(prompt, draw_samples, config)
    
    # Triangle count analysis
    tri_samples = []
    for idx, _ in stats['tris']['outliers_high'][:5]:
        if idx < len(data_points):
            tri_samples.append(data_points[idx])
    
    prompt = f"""Analyze triangle count performance (2-3 paragraphs):

Statistics:
- Samples: {stats['count']}, Min: {format_number(stats['tris']['min'])}, Max: {format_number(stats['tris']['max'])}
- Q1: {format_number(stats['tris']['q1'])}, Median: {format_number(stats['tris']['median'])}, Q3: {format_number(stats['tris']['q3'])}
- P90: {format_number(stats['tris']['p90'], 0)}, P95: {format_number(stats['tris']['p95'], 0)}, P99: {format_number(stats['tris']['p99'], 0)}
- CV: {format_number(stats['tris']['cv'], 1)}%, Trend: {stats['trends']['tris']['direction']}

Cover distribution, variability, and geometry complexity. Use HTML <p> tags."""

    results['tris'] = call_llm_chunked(prompt, tri_samples, config)
    
    # Temporal correlation
    sorted_by_draws = sorted(data_points, key=lambda x: x['draws'])
    low_draw_tris = statistics.mean([p['tris'] for p in sorted_by_draws[:10]])
    high_draw_tris = statistics.mean([p['tris'] for p in sorted_by_draws[-10:]])
    
    corr_samples = sorted_by_draws[:5] + sorted_by_draws[-5:]
    
    prompt = f"""Analyze temporal behavior and correlation (2-3 paragraphs):

Frame Time:
- Mean: {format_number(stats['frame_times']['mean'], 1)}s, Median: {format_number(stats['frame_times']['median'], 1)}s
- Anomalies: {len(stats['frame_times']['anomalies'])}

Correlation:
- Low draw frames (bottom 10): avg {format_number(low_draw_tris, 0)} triangles
- High draw frames (top 10): avg {format_number(high_draw_tris, 0)} triangles

Include heading <h3>Temporal & Correlation Analysis</h3>. Use HTML <p> tags."""

    results['temporal'] = call_llm_chunked(prompt, corr_samples, config)
    
    return results

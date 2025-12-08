"""Executive summary generator."""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from bobreview.core.utils import format_number, log_warning
from bobreview.llm.client import call_llm_chunked


def generate_executive_summary(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> str:
    """Generate executive summary using LLM."""
    critical_idx, critical_point = stats['critical']
    
    # Gather sample data points
    sample_data: List[Dict[str, Any]] = []
    seen_indices: set[int] = set()
    
    # Include critical hotspot
    if 0 <= critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
        seen_indices.add(critical_idx)
        critical_valid = True
    else:
        log_warning(f"Critical index {critical_idx} out of range", config)
        critical_valid = False
    
    # Include high-load and low-load samples
    for idx, _ in stats['high_load'][:2]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    for idx, _ in stats['low_load'][:1]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    peak_desc = (
        f"Index {critical_idx} with {critical_point['draws']} draws and {format_number(critical_point['tris'])} triangles"
        if critical_valid else "Data not available"
    )
    
    prompt = f"""You are analyzing a performance report for a game level/scene. Generate a concise executive summary (2-3 paragraphs):

Location: {config.location}
Total samples: {stats['count']}

Draw Calls:
- Mean: {format_number(stats['draws']['mean'], 0)}, Median: {format_number(stats['draws']['median'], 0)}
- P90: {format_number(stats['draws']['p90'], 0)}, P95: {format_number(stats['draws']['p95'], 0)}, P99: {format_number(stats['draws']['p99'], 0)}
- CV: {format_number(stats['draws']['cv'], 1)}%
- Trend: {stats['trends']['draws']['direction']}

Triangles:
- Mean: {format_number(stats['tris']['mean'], 0)}, Median: {format_number(stats['tris']['median'], 0)}
- P90: {format_number(stats['tris']['p90'], 0)}, P95: {format_number(stats['tris']['p95'], 0)}, P99: {format_number(stats['tris']['p99'], 0)}
- CV: {format_number(stats['tris']['cv'], 1)}%
- Trend: {stats['trends']['tris']['direction']}

Peak hotspot: {peak_desc}
High-load frames: {len(stats['high_load'])}
Low-load frames: {len(stats['low_load'])}

Cover:
1. Overall performance health (2-3 points)
2. Key concerns (3-4 points)
3. Peak hotspot impact (3-4 points)

Use HTML paragraph tags (<p>). Be concise and data-driven."""

    return call_llm_chunked(prompt, sample_data, config)

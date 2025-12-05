"""Visual analysis generator."""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.config import ReportConfig

from ...core.utils import format_number
from ..client import call_llm


def generate_visual_analysis(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> str:
    """Generate visual analysis interpretation for distribution charts."""
    
    prompt = f"""Analyze distribution patterns (2 paragraphs):

Draw Calls:
- Mean: {format_number(stats['draws']['mean'], 0)}, Median: {format_number(stats['draws']['median'], 0)}
- P90: {format_number(stats['draws']['p90'], 0)}, P95: {format_number(stats['draws']['p95'], 0)}, P99: {format_number(stats['draws']['p99'], 0)}
- Range: {format_number(stats['draws']['min'], 0)} to {format_number(stats['draws']['max'], 0)}
- CV: {format_number(stats['draws']['cv'], 1)}%, Trend: {stats['trends']['draws']['direction']}

Triangles:
- Mean: {format_number(stats['tris']['mean'], 0)}, Median: {format_number(stats['tris']['median'], 0)}
- P90: {format_number(stats['tris']['p90'], 0)}, P95: {format_number(stats['tris']['p95'], 0)}, P99: {format_number(stats['tris']['p99'], 0)}
- Range: {format_number(stats['tris']['min'])} to {format_number(stats['tris']['max'])}
- CV: {format_number(stats['tris']['cv'], 1)}%, Trend: {stats['trends']['tris']['direction']}

Cover:
1. Distribution shape (normal, skewed, bimodal)
2. Percentile interpretation (tail behavior)
3. Consistency (using CV)
4. Trend implications

Use HTML <p> tags. Reference specific metrics."""

    return call_llm(prompt, data_table=None, config=config)

"""Statistical interpretation generator."""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.config import ReportConfig

from ...core.utils import format_number
from ..client import call_llm


def generate_statistical_interpretation(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> str:
    """Generate interpretation of advanced statistical metrics."""
    
    prompt = f"""Interpret advanced performance statistics (2 paragraphs):

Variability:
- Draw Calls CV: {format_number(stats['draws']['cv'], 1)}% (<10% consistent, 10-30% moderate, >30% high)
- Triangles CV: {format_number(stats['tris']['cv'], 1)}%

Confidence (95%):
- Draw Calls: [{format_number(stats['confidence_intervals']['draws'][0], 0)}, {format_number(stats['confidence_intervals']['draws'][1], 0)}]
- Triangles: [{format_number(stats['confidence_intervals']['tris'][0], 0)}, {format_number(stats['confidence_intervals']['tris'][1], 0)}]

Trends:
- Draw Calls: {stats['trends']['draws']['direction']} (slope: {format_number(stats['trends']['draws']['slope'], 3)})
- Triangles: {stats['trends']['tris']['direction']} (slope: {format_number(stats['trends']['tris']['slope'], 1)})

Frame Time:
- Mean: {format_number(stats['frame_times']['mean'], 1)}s, Anomalies: {len(stats['frame_times']['anomalies'])}

Outlier Consensus:
- Draws: Sigma({len(stats['draws']['outliers_high']) + len(stats['draws']['outliers_low'])}), IQR({len(stats['outliers_iqr']['draws'])}), MAD({len(stats['outliers_mad']['draws'])})
- Tris: Sigma({len(stats['tris']['outliers_high']) + len(stats['tris']['outliers_low'])}), IQR({len(stats['outliers_iqr']['tris'])}), MAD({len(stats['outliers_mad']['tris'])})

Cover consistency, trajectory, frame stability, and outlier reliability. Use HTML <p> tags."""

    return call_llm(prompt, data_table=None, config=config)

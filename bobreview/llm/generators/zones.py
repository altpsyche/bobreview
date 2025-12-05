"""Zones and hotspots generator."""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.config import ReportConfig

from ...core.utils import format_number
from ..client import call_llm_chunked


def generate_zones_hotspots(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate zones and hotspots analysis using LLM."""
    results = {}
    
    # High-load analysis
    high_load_samples = []
    for idx, _ in stats['high_load']:
        if idx < len(data_points):
            high_load_samples.append(data_points[idx])
    
    high_load_details = "\n".join([
        f"Index {i}: {p['draws']} draws, {format_number(p['tris'])} tris" 
        for i, p in stats['high_load'][:5]
    ])
    
    prompt = f"""Analyze high-load performance frames (1-2 paragraphs):

{len(stats['high_load'])} frames exceed thresholds (≥{config.high_load_draw_threshold} draws or ≥{format_number(config.high_load_tri_threshold, 0)} tris)

Top frames:
{high_load_details}

Cover patterns, draw-call vs geometry dominance, and common characteristics. Use HTML <p> tags."""
    
    results['high_load'] = call_llm_chunked(prompt, high_load_samples, config)
    
    # Low-load analysis
    low_load_samples = []
    for idx, _ in stats['low_load']:
        if idx < len(data_points):
            low_load_samples.append(data_points[idx])
    
    prompt = f"""Analyze low-load baseline frames (1 paragraph):

{len(stats['low_load'])} frames below thresholds (<{config.low_load_draw_threshold} draws and <{format_number(config.low_load_tri_threshold, 0)} tris)

Explain their significance as performance baselines. Use HTML <p> tags."""
    
    results['low_load'] = call_llm_chunked(prompt, low_load_samples, config)
    
    return results

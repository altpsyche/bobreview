"""Optimization checklist generator."""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from bobreview.core.utils import format_number, log_warning
from bobreview.llm.client import call_llm_chunked


def generate_optimization_checklist(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    _images_dir_rel: str,
) -> Dict[str, str]:
    """Generate optimization checklist using LLM."""
    results = {}
    
    critical_idx, critical_point = stats['critical']
    
    # Critical hotspot
    critical_samples: List[Dict[str, Any]] = []
    if 0 <= critical_idx < len(data_points):
        critical_samples.append(data_points[critical_idx])
    else:
        log_warning(f"Critical index {critical_idx} out of range", config)
    
    prompt = f"""Generate optimization recommendations for critical hotspot:

Index {critical_idx}: {critical_point['draws']} draws, {format_number(critical_point['tris'])} triangles
Test case: {critical_point['testcase']}
Thresholds: {config.draw_hard_cap} draws, {format_number(config.tri_hard_cap, 0)} tris

Generate:
1. Inspection steps (3-4 bullet points)
2. Optimization actions by category (geometry, draw calls, lighting)

Format as HTML <ul> and <li> tags. Be specific and actionable."""

    results['critical'] = call_llm_chunked(prompt, critical_samples, config)
    
    # High-geometry hotspots
    high_geo_samples = []
    for idx, point in stats['high_load']:
        if point['tris'] >= config.high_load_tri_threshold and idx < len(data_points):
            high_geo_samples.append(data_points[idx])
    
    prompt = f"""Generate geometry optimization recommendations:

{len(high_geo_samples)} frames above {format_number(config.high_load_tri_threshold, 0)} triangles
Target: below {format_number(config.tri_hard_cap, 0)}

Generate 4-5 actionable points for geometry/LOD optimization. Format as HTML <ul> with <li> tags."""

    results['high_geometry'] = call_llm_chunked(prompt, high_geo_samples, config)
    
    # High-draw hotspots
    high_draw_samples = []
    for idx, point in stats['high_load']:
        if point['draws'] >= config.high_load_draw_threshold and idx < len(data_points):
            high_draw_samples.append(data_points[idx])
    
    prompt = f"""Generate draw call optimization recommendations:

Focus: frames with draws ≥ {config.high_load_draw_threshold}
Target: below {config.draw_soft_cap}

Generate 4-5 points for batching and material consolidation. Format as HTML <ul> with <li> tags."""

    results['high_draw'] = call_llm_chunked(prompt, high_draw_samples, config)
    
    return results

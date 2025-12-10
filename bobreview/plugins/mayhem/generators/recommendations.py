"""System recommendations generator."""

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from bobreview.core.utils import format_number, log_warning
from bobreview.services.llm.client import call_llm_chunked


def generate_system_recommendations(
    data_points: List[Dict[str, Any]],
    stats: Dict[str, Any],
    config: "ReportConfig",
    context: Dict[str, Any],
) -> Dict[str, str]:
    """Generate system-level recommendations using LLM."""
    results = {}
    
    # Gather representative samples
    sample_data: List[Dict[str, Any]] = []
    seen_indices: set[int] = set()
    
    critical_idx = stats['critical'][0]
    if 0 <= critical_idx < len(data_points):
        sample_data.append(data_points[critical_idx])
        seen_indices.add(critical_idx)
    else:
        log_warning(f"Critical index {critical_idx} out of range", config)
    
    for idx, _ in stats['high_load'][:3]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    for idx, _ in stats['low_load'][:2]:
        if idx < len(data_points) and idx not in seen_indices:
            sample_data.append(data_points[idx])
            seen_indices.add(idx)
    
    # Get location from extensions.mayhem (plugin-specific) or extract from data
    # Priority: 1) JSON config (extensions.mayhem.location), 2) Extract from testcase field
    location = None
    if isinstance(context, dict):
        # First try direct location (from context builder)
        location = context.get('location')
        # Fallback: try extensions.mayhem.location
        if not location:
            extensions = context.get('extensions', {})
            mayhem_ext = extensions.get('mayhem', {})
            if mayhem_ext and 'location' in mayhem_ext:
                location = mayhem_ext['location']
    
    # Fall back to extracting from testcase field if not in JSON
    if not location and data_points and 'testcase' in data_points[0]:
        testcases = [dp.get('testcase', '') for dp in data_points if dp.get('testcase')]
        if testcases:
            location = testcases[0]  # Use first testcase as location indicator
    
    location_line = f"Location: {location}\n" if location else ""
    
    prompt = f"""Generate system-level performance recommendations:

{location_line}Samples: {stats['count']}

Performance:
- Draw Calls: Mean {format_number(stats['draws']['mean'], 0)}, P95 {format_number(stats['draws']['p95'], 0)}
- Triangles: Mean {format_number(stats['tris']['mean'], 0)}, P95 {format_number(stats['tris']['p95'], 0)}
- Trends: Draws {stats['trends']['draws']['direction']}, Tris {stats['trends']['tris']['direction']}

Critical:
- Peak: {stats['critical'][1]['draws']} draws, {format_number(stats['critical'][1]['tris'])} tris
- High-load frames: {len(stats['high_load'])}
- Frame time anomalies: {len(stats['frame_times']['anomalies'])}

Generate recommendations by category:
1. LOD & Detail Management (3-4 points)
2. Occlusion & Culling (3-4 points)
3. Draw Call Batching (3-4 points)
4. Shader & Material (3-4 points)
5. Priority & Planning (3-4 points)

Format as:
<h3>Category Name</h3>
<ul class="body-text">
  <li>Recommendation 1</li>
</ul>"""

    results['full'] = call_llm_chunked(prompt, sample_data, config)
    
    return results

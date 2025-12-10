"""
LLM generator for chart explanations.

Generates contextual explanations for each chart type in the report.
Returns a single HTML string with all explanations.
"""

from typing import List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig


def generate_chart_explanations(
    data_points: List[Any],
    stats: Any,
    config: "ReportConfig",
    context: Any
) -> str:
    """
    Generate explanations for all chart types.
    
    Returns a single HTML string containing explanations for all chart types.
    """
    # Extract stats for analysis
    draws = stats.get('draws', {})
    tris = stats.get('tris', {})
    
    explanations = []
    
    # Draw Calls Timeline explanation
    draws_median = draws.get('median', 0)
    draws_p90 = draws.get('p90', 0)
    draws_p95 = draws.get('p95', 0)
    draws_stdev = draws.get('stdev', 0)
    
    if draws_stdev > draws_median * 0.5:
        draws_stability = "significant variability"
    elif draws_stdev > draws_median * 0.2:
        draws_stability = "moderate fluctuations"
    else:
        draws_stability = "relatively stable performance"
    
    explanations.append(
        f"<div data-chart=\"draws_timeline\">"
        f"<p>This timeline shows draw call counts per frame over time. "
        f"The data shows {draws_stability} with typical values around {int(draws_median)} calls. "
        f"Heavy load scenarios reach {int(draws_p90)}-{int(draws_p95)} draw calls, "
        f"which may indicate batching opportunities.</p></div>"
    )
    
    # Triangles Timeline explanation
    tris_median = tris.get('median', 0)
    tris_p90 = tris.get('p90', 0)
    tris_p95 = tris.get('p95', 0)
    tris_stdev = tris.get('stdev', 0)
    
    if tris_stdev > tris_median * 0.5:
        tris_stability = "high variability suggesting dynamic geometry"
    elif tris_stdev > tris_median * 0.2:
        tris_stability = "moderate variation in scene complexity"
    else:
        tris_stability = "consistent geometry load"
    
    explanations.append(
        f"<div data-chart=\"tris_timeline\">"
        f"<p>Triangle counts track GPU geometry workload over time. "
        f"The data indicates {tris_stability} with typical frames around {int(tris_median):,} triangles. "
        f"Peak loads reach {int(tris_p90):,}-{int(tris_p95):,} triangles, "
        f"which can impact vertex processing.</p></div>"
    )
    
    # Scatter Plot explanation
    # Analyze correlation between draws and triangles
    if draws_median > 0 and tris_median > 0:
        tris_per_draw = tris_median / draws_median
        if tris_per_draw > 5000:
            batch_assessment = "well-batched geometry with many triangles per draw call"
        elif tris_per_draw > 1000:
            batch_assessment = "reasonable batching efficiency"
        else:
            batch_assessment = "potential for additional draw call batching"
    else:
        batch_assessment = "unknown batching efficiency"
    
    explanations.append(
        f"<div data-chart=\"scatter\">"
        f"<p>This scatter plot reveals the relationship between draw calls and triangles per frame. "
        f"Each point represents a frame, color-coded by performance zone. "
        f"The pattern suggests {batch_assessment}. "
        f"Clustered points indicate consistent behavior, while outliers may warrant investigation.</p></div>"
    )
    
    # Draw Calls Histogram explanation
    draws_q1 = draws.get('q1', 0)
    draws_q3 = draws.get('q3', 0)
    
    explanations.append(
        f"<div data-chart=\"draws_histogram\">"
        f"<p>The distribution shows how frequently different draw call counts occur. "
        f"Most frames fall between {int(draws_q1)} and {int(draws_q3)} draw calls, "
        f"with the typical frame at {int(draws_median)}. "
        f"A tight distribution suggests consistent rendering, while a wide spread may indicate scene-dependent behavior.</p></div>"
    )
    
    # Triangles Histogram explanation
    tris_q1 = tris.get('q1', 0)
    tris_q3 = tris.get('q3', 0)
    
    explanations.append(
        f"<div data-chart=\"tris_histogram\">"
        f"<p>This histogram displays the frequency of triangle count ranges across all frames. "
        f"The bulk of frames process {int(tris_q1):,} to {int(tris_q3):,} triangles, "
        f"centered around {int(tris_median):,}. "
        f"Outliers in the high range may indicate specific heavy scenes to optimize.</p></div>"
    )
    
    return ''.join(explanations)

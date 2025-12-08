"""
Performance analysis LLM generators for MayhemAutomation plugin.

Each generator produces specific content sections for performance reports.
These are MayhemAutomation-specific and registered by the plugin.
"""

from .executive import generate_executive_summary
from .metrics import generate_metric_deep_dive
from .zones import generate_zones_hotspots
from .optimization import generate_optimization_checklist
from .recommendations import generate_system_recommendations
from .visuals import generate_visual_analysis
from .stats import generate_statistical_interpretation

__all__ = [
    'generate_executive_summary',
    'generate_metric_deep_dive', 
    'generate_zones_hotspots',
    'generate_optimization_checklist',
    'generate_system_recommendations',
    'generate_visual_analysis',
    'generate_statistical_interpretation',
]

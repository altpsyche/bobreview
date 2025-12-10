"""
LLM Generator Adapters for MayhemAutomation.

These adapter classes wrap the generator functions to implement LLMGeneratorInterface
from core.api, making them compatible with the core API.
"""

from typing import Dict, List, Any, TYPE_CHECKING

from bobreview.core.api import LLMGeneratorInterface

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from .executive import generate_executive_summary
from .metrics import generate_metric_deep_dive
from .zones import generate_zones_hotspots
from .optimization import generate_optimization_checklist
from .recommendations import generate_system_recommendations
from .visuals import generate_visual_analysis
from .stats import generate_statistical_interpretation
from .chart_explanations import generate_chart_explanations


class ExecutiveSummaryGenerator(LLMGeneratorInterface):
    """Adapter for executive summary generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate executive summary."""
        # Ensure context is a dict
        if not isinstance(context, dict):
            context = {'images_dir_rel': str(context) if context else ''}
        return generate_executive_summary(data_points, stats, config, context)


class MetricDeepDiveGenerator(LLMGeneratorInterface):
    """Adapter for metric deep dive generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate metric deep dive."""
        if not isinstance(context, dict):
            context = {}
        return generate_metric_deep_dive(data_points, stats, config, context)


class ZonesHotspotsGenerator(LLMGeneratorInterface):
    """Adapter for zones and hotspots generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate zones and hotspots analysis."""
        if not isinstance(context, dict):
            context = {}
        return generate_zones_hotspots(data_points, stats, config, context)


class OptimizationChecklistGenerator(LLMGeneratorInterface):
    """Adapter for optimization checklist generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate optimization checklist."""
        if not isinstance(context, dict):
            context = {}
        return generate_optimization_checklist(data_points, stats, config, context)


class SystemRecommendationsGenerator(LLMGeneratorInterface):
    """Adapter for system recommendations generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate system recommendations."""
        if not isinstance(context, dict):
            context = {}
        return generate_system_recommendations(data_points, stats, config, context)


class VisualAnalysisGenerator(LLMGeneratorInterface):
    """Adapter for visual analysis generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate visual analysis."""
        if not isinstance(context, dict):
            context = {}
        return generate_visual_analysis(data_points, stats, config, context)


class StatisticalInterpretationGenerator(LLMGeneratorInterface):
    """Adapter for statistical interpretation generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate statistical interpretation."""
        if not isinstance(context, dict):
            context = {}
        return generate_statistical_interpretation(data_points, stats, config, context)


class ChartExplanationsGenerator(LLMGeneratorInterface):
    """Adapter for chart explanations generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate chart explanations as HTML string."""
        if not isinstance(context, dict):
            context = {}
        return generate_chart_explanations(data_points, stats, config, context)


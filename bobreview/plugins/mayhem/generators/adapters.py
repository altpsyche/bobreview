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
        return generate_executive_summary(data_points, stats, config, context.get('images_dir_rel', ''))


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
        return generate_metric_deep_dive(data_points, stats, config, context.get('images_dir_rel', ''))


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
        return generate_zones_hotspots(data_points, stats, config, context.get('images_dir_rel', ''))


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
        return generate_optimization_checklist(data_points, stats, config, context.get('images_dir_rel', ''))


class SystemRecommendationsGenerator(LLMGeneratorInterface):
    """Adapter for system recommendations generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate system recommendations."""
        return generate_system_recommendations(data_points, stats, config, context.get('images_dir_rel', ''))


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
        return generate_visual_analysis(data_points, stats, config, context.get('images_dir_rel', ''))


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
        return generate_statistical_interpretation(data_points, stats, config, context.get('images_dir_rel', ''))


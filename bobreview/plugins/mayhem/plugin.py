"""
MayhemAutomation Plugin.

This plugin provides:
- LLM Generators (executive summary, metrics, zones, etc.)
- Data Parsers (filename pattern parser)
- Themes (registers all 7 built-in themes)
- Service implementations
- Report systems and templates

Without this plugin, BobReview is just an empty shell.
Other plugins can override any of these components.
"""

from pathlib import Path
from ...core.plugin_system import BasePlugin, PluginHelper
from ...services import get_container, DataService, AnalyticsService, ChartService, LLMService


class MayhemAutomationPlugin(BasePlugin):
    """
    MayhemAutomation - performance analysis plugin.
    
    Provides LLM generators, chart generators, context builders,
    themes, and templates for performance analysis reports.
    """
    
    name = "MayhemAutomation"
    version = "1.0.0"
    author = "BobReview Team"
    description = "Full-featured automation: LLM generators, themes, services, templates"
    dependencies = []
    
    def __init__(self):
        super().__init__()
    
    def on_load(self, registry) -> None:
        """Register all components using PluginHelper."""
        config = self.get_config()
        helper = PluginHelper(registry, self.name)
        
        # 1. Register LLM generators (custom wrappers needed)
        if config.get('register_generators', True):
            self._register_generators(registry)
        
        # 2. Register data parser
        from .parsers import MayhemParser
        helper.add_data_parser('filename_pattern', MayhemParser)
        
        # 3. Register all 7 built-in themes
        if config.get('register_themes', True):
            helper.add_builtin_themes()
        
        # 4. Register services
        if config.get('register_services', True):
            helper.register_default_services()
        
        # 5. Register analyzer function (specialized)
        self._register_analyzer()
        
        # 6. Register report systems from JSON files
        if config.get('register_report_systems', True):
            report_systems_dir = Path(__file__).parent / 'report_systems'
            helper.add_report_systems_from_dir(report_systems_dir)
        
        # 7. Register templates
        if config.get('register_templates', True):
            template_dir = Path(__file__).parent / 'templates'
            helper.add_templates(template_dir)
        
        # 8. Register chart generator
        if config.get('register_chart_generators', True):
            from .charts import PerformanceChartGenerator
            helper.add_chart_generator('png_data_points', PerformanceChartGenerator)
        
        # 9. Register context builder
        if config.get('register_context_builders', True):
            from .context import PerformanceContextBuilder
            helper.add_context_builder('png_data_points', PerformanceContextBuilder)
    
    def _register_generators(self, registry) -> None:
        """Register all built-in LLM generators."""
        from .generators.adapters import (
            ExecutiveSummaryGenerator,
            MetricDeepDiveGenerator,
            ZonesHotspotsGenerator,
            OptimizationChecklistGenerator,
            SystemRecommendationsGenerator,
            VisualAnalysisGenerator,
            StatisticalInterpretationGenerator,
            ChartExplanationsGenerator
        )
        
        generators = [
            ('executive_summary', ExecutiveSummaryGenerator),
            ('metric_deep_dive', MetricDeepDiveGenerator),
            ('zones_hotspots', ZonesHotspotsGenerator),
            ('optimization_checklist', OptimizationChecklistGenerator),
            ('system_recommendations', SystemRecommendationsGenerator),
            ('visual_analysis', VisualAnalysisGenerator),
            ('statistical_interpretation', StatisticalInterpretationGenerator),
            ('chart_explanations', ChartExplanationsGenerator),
        ]
        
        for gen_id, gen_class in generators:
            wrapper = self._create_generator_wrapper(gen_id, gen_class)
            registry.llm_generators.register(wrapper, plugin_name=self.name)
    
    def _create_generator_wrapper(self, name: str, gen_class):
        """Create a wrapper class for registering generator classes."""
        # Cache the generator instance at wrapper creation time
        # This avoids creating a new instance on every generate() call
        # All current generators are stateless, so reusing the instance is safe
        generator_instance = gen_class()
        
        class GeneratorWrapper:
            generator_name = name
            _instance = generator_instance  # Store instance as class attribute
            
            # Explicit signature required for LLM service to pass full context
            @staticmethod
            def generate(data_points, stats, config, context):
                return GeneratorWrapper._instance.generate(data_points, stats, config, context)
        
        return GeneratorWrapper
    
    def _register_analyzer(self) -> None:
        """Register the performance analyzer function."""
        from ...core.plugin_system.registries import get_analyzer_registry
        from .analysis import analyze_performance_data
        
        analyzer_registry = get_analyzer_registry()
        analyzer_registry.register(
            'performance', 
            analyze_performance_data, 
            default=True
        )
    
    def on_unload(self) -> None:
        """Clean up when plugin is unloaded."""
        pass  # Services remain - other plugins may depend on them

"""
MayhemAutomation Plugin.

This plugin provides all the default/built-in functionality:
- LLM Generators (executive summary, metrics, zones, etc.)
- Data Parsers (filename pattern parser)
- Themes (dark, light, high contrast)
- Default service implementations
- Report systems and templates

Without this plugin, BobReview is just an empty shell.
Other plugins can override any of these components.
"""

from ...core.plugin_system import BasePlugin
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
        """Register all built-in components."""
        config = self.get_config()
        
        # Register LLM generators
        if config.get('register_generators', True):
            self._register_generators(registry)
        
        # Register data parsers
        self._register_parsers(registry)
        
        # Register themes
        if config.get('register_default_theme', True):
            self._register_themes(registry)
        
        # Register default services
        if config.get('register_services', True):
            self._register_services()
        
        # Register analyzer function
        self._register_analyzer()
        
        # Register report systems
        if config.get('register_report_systems', True):
            self._register_report_systems(registry)
        
        # Register templates
        if config.get('register_templates', True):
            self._register_templates(registry)
        
        # Register chart generators
        if config.get('register_chart_generators', True):
            self._register_chart_generators(registry)
        
        # Register context builders
        if config.get('register_context_builders', True):
            self._register_context_builders(registry)
    
    def _register_generators(self, registry) -> None:
        """Register all built-in LLM generators."""
        from .generators.adapters import (
            ExecutiveSummaryGenerator,
            MetricDeepDiveGenerator,
            ZonesHotspotsGenerator,
            OptimizationChecklistGenerator,
            SystemRecommendationsGenerator,
            VisualAnalysisGenerator,
            StatisticalInterpretationGenerator
        )
        
        generators = [
            ('executive_summary', ExecutiveSummaryGenerator),
            ('metric_deep_dive', MetricDeepDiveGenerator),
            ('zones_hotspots', ZonesHotspotsGenerator),
            ('optimization_checklist', OptimizationChecklistGenerator),
            ('system_recommendations', SystemRecommendationsGenerator),
            ('visual_analysis', VisualAnalysisGenerator),
            ('statistical_interpretation', StatisticalInterpretationGenerator),
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
            
            @staticmethod
            def generate(*args, **kwargs):
                return GeneratorWrapper._instance.generate(*args, **kwargs)
        
        return GeneratorWrapper
    
    def _register_parsers(self, registry) -> None:
        """Register MayhemAutomation data parsers."""
        from .parsers import MayhemParser
        
        # Register MayhemParser as the filename_pattern parser for this plugin
        class MayhemParserWrapper:
            parser_name = "filename_pattern"
            parser_class = MayhemParser
        
        registry.data_parsers.register(MayhemParserWrapper, plugin_name=self.name)
    
    def _register_themes(self, registry) -> None:
        """Register built-in themes."""
        from ...core.themes import BUILTIN_THEMES
        
        # Register each theme with plugin registry
        for theme in BUILTIN_THEMES:
            registry.themes.register(theme, plugin_name=self.name)
    
    def _register_services(self) -> None:
        """Register default service implementations."""
        container = get_container()
        
        # Only register if not already present (allows other plugins to override)
        if not container.has('data'):
            container.register('data', DataService())
        
        if not container.has('analytics'):
            container.register('analytics', AnalyticsService())
        
        if not container.has('charts'):
            container.register('charts', ChartService())
        
        # LLM service is registered by executor with config
        # Don't register a default here
    
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
    
    def _register_report_systems(self, registry) -> None:
        """Register built-in report systems."""
        import json
        from pathlib import Path
        
        # Load report systems from plugin's report_systems directory
        report_systems_dir = Path(__file__).parent / 'report_systems'
        
        if report_systems_dir.exists():
            for json_file in report_systems_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        system_def = json.load(f)
                    
                    system_name = json_file.stem  # e.g., 'png_data_points'
                    registry.report_systems.register(
                        name=system_name,
                        system_def=system_def,
                        plugin_name=self.name
                    )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(
                        f"Failed to load report system {json_file}: {e}"
                    )
    
    def _register_templates(self, registry) -> None:
        """Register built-in templates."""
        from pathlib import Path
        
        template_dir = Path(__file__).parent / 'templates'
        if template_dir.exists():
            # Priority 1000 = low priority (user and other plugins can override)
            registry.template_paths.register(
                template_dir, 
                plugin_name=self.name,
                priority=1000
            )
    
    def _register_chart_generators(self, registry) -> None:
        """Register chart generators for our report systems."""
        from .charts import PerformanceChartGenerator
        
        # Chart generator needs config and thresholds at generation time,
        # not at registration time -- we register a factory
        registry.chart_generators.register(
            report_system_id='png_data_points',
            generator=PerformanceChartGenerator,  # Pass class, not instance
            plugin_name=self.name
        )
    
    def _register_context_builders(self, registry) -> None:
        """Register context builders for our report systems."""
        from .context import PerformanceContextBuilder
        
        # Context builder adds images/critical/metrics to template context
        registry.context_builders.register(
            report_system_id='png_data_points',
            builder=PerformanceContextBuilder,  # Pass class, not instance
            plugin_name=self.name
        )
    
    def on_unload(self) -> None:
        """Clean up when plugin is unloaded."""
        pass  # Services remain - other plugins may depend on them

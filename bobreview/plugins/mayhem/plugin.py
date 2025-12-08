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

from ...plugins import BasePlugin
from ...services import get_container, DataService, AnalyticsService, ChartService, LLMService


class CorePlugin(BasePlugin):
    """
    MayhemAutomation - the default plugin providing all built-in functionality.
    
    This is loaded automatically and provides default implementations
    that other plugins can override.
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
        from ...llm.generators import (
            generate_executive_summary,
            generate_metric_deep_dive,
            generate_zones_hotspots,
            generate_optimization_checklist,
            generate_system_recommendations,
            generate_visual_analysis,
            generate_statistical_interpretation
        )
        
        generators = [
            ('executive_summary', generate_executive_summary),
            ('metric_deep_dive', generate_metric_deep_dive),
            ('zones_hotspots', generate_zones_hotspots),
            ('optimization_checklist', generate_optimization_checklist),
            ('system_recommendations', generate_system_recommendations),
            ('visual_analysis', generate_visual_analysis),
            ('statistical_interpretation', generate_statistical_interpretation),
        ]
        
        for gen_id, gen_func in generators:
            wrapper = self._create_generator_wrapper(gen_id, gen_func)
            registry.register_llm_generator(wrapper, plugin_name=self.name)
    
    def _create_generator_wrapper(self, name: str, func):
        """Create a wrapper class for registering functions."""
        class GeneratorWrapper:
            generator_name = name
            generate = staticmethod(func)
        return GeneratorWrapper
    
    def _register_parsers(self, registry) -> None:
        """Register built-in data parsers."""
        from ...report_systems.data_parser_base import FilenamePatternParser
        
        # Wrap the parser class
        class FilenamePatternParserWrapper:
            parser_name = "filename_pattern"
            parser_class = FilenamePatternParser
        
        registry.register_data_parser(FilenamePatternParserWrapper, plugin_name=self.name)
    
    def _register_themes(self, registry) -> None:
        """Register built-in themes."""
        from ...registry.themes import BUILTIN_THEMES, register_theme as legacy_register
        
        # Register each theme with both plugin registry and legacy registry
        for theme in BUILTIN_THEMES:
            registry.register_theme(theme, plugin_name=self.name)
            legacy_register(theme)  # Also register in legacy for get_theme() to work
    
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
                    registry.register_report_system(
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
        """Register built-in templates from core plugin."""
        from pathlib import Path
        
        template_dir = Path(__file__).parent / 'templates'
        if template_dir.exists():
            # Priority 1000 = low priority (user and other plugins can override)
            registry.register_template_path(
                template_dir, 
                plugin_name=self.name,
                priority=1000
            )
    
    def _register_chart_generators(self, registry) -> None:
        """Register chart generators for our report systems."""
        from .charts import PerformanceChartGenerator
        
        # Chart generator needs config and thresholds at generation time,
        # not at registration time -- we register a factory
        registry.register_chart_generator(
            report_system_id='png_data_points',
            generator=PerformanceChartGenerator,  # Pass class, not instance
            plugin_name=self.name
        )
    
    def _register_context_builders(self, registry) -> None:
        """Register context builders for our report systems."""
        from .context import PerformanceContextBuilder
        
        # Context builder adds images/critical/metrics to template context
        registry.register_context_builder(
            report_system_id='png_data_points',
            builder=PerformanceContextBuilder,  # Pass class, not instance
            plugin_name=self.name
        )
    
    def on_unload(self) -> None:
        """Clean up when plugin is unloaded."""
        pass  # Services remain - other plugins may depend on them

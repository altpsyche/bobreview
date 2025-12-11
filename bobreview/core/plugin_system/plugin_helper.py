"""
Plugin helper for simplified component registration.

Provides a facade over the various registries to make plugin development simpler.
Instead of understanding 13+ registries, plugin authors can use a single helper class.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

if TYPE_CHECKING:
    from .registry import PluginRegistry
    from ..themes import ReportTheme


class PluginHelper:
    """
    Simplified registration facade for plugin development.
    
    Wraps the PluginRegistry to provide a cleaner API for common operations.
    
    Example:
        class MyPlugin(BasePlugin):
            name = "my-plugin"
            
            def on_load(self, registry):
                helper = PluginHelper(registry, self.name)
                
                # Simple one-liners instead of understanding registries
                helper.add_data_parser("csv", MyCsvParser)
                helper.add_theme(my_theme)
                helper.add_templates(Path(__file__).parent / "templates")
                helper.add_report_system_from_json(Path(__file__).parent / "report_systems")
    """
    
    def __init__(self, registry: 'PluginRegistry', plugin_name: str):
        """
        Initialize helper with registry and plugin name.
        
        Parameters:
            registry: PluginRegistry instance from on_load()
            plugin_name: Name of the plugin (for ownership tracking)
        """
        self.registry = registry
        self.plugin_name = plugin_name
    
    # -------------------------------------------------------------------------
    # Data Parsing
    # -------------------------------------------------------------------------
    
    def add_data_parser(self, parser_id: str, parser_class: Type) -> None:
        """
        Register a data parser.
        
        The parser class should implement DataParserInterface.
        
        Parameters:
            parser_id: Unique identifier (e.g., "csv", "png_filename")
            parser_class: Class that implements DataParserInterface
        """
        # Set parser_name attribute if not already set
        if not hasattr(parser_class, 'parser_name'):
            parser_class.parser_name = parser_id
        self.registry.data_parsers.register(parser_class, plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Themes
    # -------------------------------------------------------------------------
    
    def add_theme(self, theme: 'ReportTheme') -> None:
        """
        Register a theme.
        
        Parameters:
            theme: ReportTheme instance with unique id
        """
        self.registry.themes.register(theme, plugin_name=self.plugin_name)
    
    def add_builtin_themes(self) -> None:
        """
        Register all 7 built-in themes.
        
        Themes: dark, light, high_contrast, ocean, purple, terminal, sunset
        """
        from ..themes import BUILTIN_THEMES
        for theme in BUILTIN_THEMES:
            self.registry.themes.register(theme, plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------
    
    def add_templates(self, template_dir: Union[str, Path]) -> None:
        """
        Register a directory of Jinja2 templates.
        
        Templates will be discoverable by the template engine.
        
        Parameters:
            template_dir: Path to directory containing .html.j2 templates
        """
        self.registry.template_paths.register(str(template_dir), plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Report Systems
    # -------------------------------------------------------------------------
    
    def add_report_system(self, system_id: str, system_def: Dict[str, Any]) -> None:
        """
        Register a report system from a dictionary definition.
        
        Parameters:
            system_id: Unique identifier for the report system
            system_def: Report system definition dict (same structure as JSON)
        """
        self.registry.report_systems.register(system_id, system_def, plugin_name=self.plugin_name)
    
    def add_report_systems_from_dir(self, report_systems_dir: Union[str, Path]) -> List[str]:
        """
        Register all report systems from JSON files in a directory.
        
        Scans directory for .json files and registers each as a report system.
        
        Parameters:
            report_systems_dir: Directory containing report system JSON files
            
        Returns:
            List of registered system IDs
        """
        import json
        
        registered = []
        dir_path = Path(report_systems_dir)
        
        if not dir_path.exists():
            return registered
        
        for json_file in dir_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                system_id = data.get('id', json_file.stem)
                self.add_report_system(system_id, data)
                registered.append(system_id)
            except (json.JSONDecodeError, OSError):
                continue
        
        return registered
    
    # -------------------------------------------------------------------------
    # Context & Charts (for template rendering)
    # -------------------------------------------------------------------------
    
    def add_context_builder(self, system_id: str, builder_class: Type) -> None:
        """
        Register a context builder for a report system.
        
        Context builders add custom data to template rendering context.
        The builder class should implement ContextBuilderInterface.
        
        Parameters:
            system_id: Report system ID this builder is for
            builder_class: Class that implements ContextBuilderInterface
        """
        self.registry.context_builders.register(system_id, builder_class, plugin_name=self.plugin_name)
    
    def add_chart_generator(self, system_id: str, generator_class: Type) -> None:
        """
        Register a chart generator for a report system.
        
        Chart generators create Chart.js or other chart configurations.
        The generator class should implement ChartGeneratorInterface.
        
        Parameters:
            system_id: Report system ID this generator is for
            generator_class: Class that implements ChartGeneratorInterface
        """
        self.registry.chart_generators.register(system_id, generator_class, plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # LLM Generators
    # -------------------------------------------------------------------------
    
    def add_llm_generator(self, generator_id: str, generator_class: Type) -> None:
        """
        Register an LLM content generator.
        
        LLM generators create AI-powered content for reports.
        The generator class should implement LLMGeneratorInterface.
        
        Parameters:
            generator_id: Unique identifier for the generator
            generator_class: Class that implements LLMGeneratorInterface
        """
        self.registry.llm_generators.register(generator_id, generator_class, plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Analysis Functions
    # -------------------------------------------------------------------------
    
    def add_analyzer(self, analyzer_id: str, analyzer_func: Callable) -> None:
        """
        Register a custom analysis function.
        
        Analysis functions compute custom metrics from data points.
        
        Parameters:
            analyzer_id: Unique identifier for the analyzer
            analyzer_func: Function that takes (data_points, config) and returns results
        """
        self.registry.analyzers.register(analyzer_id, analyzer_func, plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Services
    # -------------------------------------------------------------------------
    
    def register_default_services(self, container=None) -> None:
        """
        Register default core services if not already registered.
        
        Registers: DataService, AnalyticsService, ChartService, LLMService
        
        Parameters:
            container: ServiceContainer (uses global container if not provided)
        """
        if container is None:
            from ...services import get_container
            container = get_container()
        
        from ...services import DataService, AnalyticsService, ChartService, LLMService
        
        if not container.has('data'):
            container.register('data', DataService())
        if not container.has('analytics'):
            container.register('analytics', AnalyticsService())
        if not container.has('charts'):
            container.register('charts', ChartService())
        if not container.has('llm'):
            container.register('llm', LLMService())
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    def setup_complete_report_system(
        self,
        system_id: str,
        system_def: Dict[str, Any],
        parser_class: Optional[Type] = None,
        context_builder_class: Optional[Type] = None,
        chart_generator_class: Optional[Type] = None,
        template_dir: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Convenience method to register a complete report system with all components.
        
        Parameters:
            system_id: Unique identifier for the report system
            system_def: Report system definition dict
            parser_class: Optional data parser class
            context_builder_class: Optional context builder class
            chart_generator_class: Optional chart generator class
            template_dir: Optional templates directory
        """
        # Register report system
        self.add_report_system(system_id, system_def)
        
        # Register parser if provided
        if parser_class:
            parser_type = system_def.get('data_source', {}).get('type', system_id)
            self.add_data_parser(parser_type, parser_class)
        
        # Register context builder if provided
        if context_builder_class:
            self.add_context_builder(system_id, context_builder_class)
        
        # Register chart generator if provided
        if chart_generator_class:
            self.add_chart_generator(system_id, chart_generator_class)
        
        # Register templates if provided
        if template_dir:
            self.add_templates(template_dir)

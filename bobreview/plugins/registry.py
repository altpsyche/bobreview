"""
Plugin registry for managing plugin components.

The registry provides methods to register and retrieve components
from all extension points: widgets, parsers, themes, charts, pages, etc.
"""

from typing import TYPE_CHECKING, Dict, List, Type, Any, Optional, Callable
import logging

if TYPE_CHECKING:
    from .base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all plugin components.
    
    Plugins register their components through this registry during on_load().
    The application queries the registry to discover available components.
    
    Example:
        registry = PluginRegistry()
        
        # Plugin registers a widget
        registry.register_widget(MyCustomWidget)
        
        # Application queries widgets
        widgets = registry.get_all_widgets()
    """
    
    def __init__(self):
        """Initialize empty registries for all extension points."""
        # Widget registry: type -> widget class
        self._widgets: Dict[str, Type] = {}
        
        # Data parser registry: name -> parser class
        self._data_parsers: Dict[str, Type] = {}
        
        # LLM generator registry: name -> generator class
        self._llm_generators: Dict[str, Type] = {}
        
        # Theme registry: name -> theme instance
        self._themes: Dict[str, Any] = {}
        
        # Chart type registry: type -> chart config class
        self._chart_types: Dict[str, Type] = {}
        
        # Page registry: id -> page definition
        self._pages: Dict[str, Any] = {}
        
        # Service registry: name -> service instance/factory
        self._services: Dict[str, Any] = {}
        
        # Report system registry: name -> system definition (parsed JSON)
        self._report_systems: Dict[str, Any] = {}
        
        # Chart generator registry: report_system_id -> generator class
        self._chart_generators: Dict[str, Any] = {}
        
        # Context builder registry: report_system_id -> builder class
        self._context_builders: Dict[str, Any] = {}
        
        # Template paths registered by plugins (ordered list for priority)
        self._template_paths: List[tuple] = []  # [(path, plugin_name), ...]
        
        # Track which plugin registered what
        self._component_owners: Dict[str, str] = {}  # component_key -> plugin_name
        
    # ─────────────────────────────────────────────────────────────────────────
    # Widget Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_widget(self, widget_cls: Type, plugin_name: str = "") -> None:
        """
        Register a widget class.
        
        Parameters:
            widget_cls: Widget class with `widget_type` attribute
            plugin_name: Name of the plugin registering this widget
        """
        widget_type = getattr(widget_cls, 'widget_type', None)
        if not widget_type:
            raise ValueError(f"Widget class must have 'widget_type' attribute: {widget_cls}")
        
        if widget_type in self._widgets:
            logger.warning(f"Overwriting existing widget type: {widget_type}")
        
        self._widgets[widget_type] = widget_cls
        self._component_owners[f"widget:{widget_type}"] = plugin_name
        logger.debug(f"Registered widget: {widget_type} from {plugin_name or 'core'}")
    
    def get_widget(self, widget_type: str) -> Optional[Type]:
        """Get a widget class by type."""
        return self._widgets.get(widget_type)
    
    def get_all_widgets(self) -> Dict[str, Type]:
        """Get all registered widgets."""
        return dict(self._widgets)
    
    def get_widget_types(self) -> List[str]:
        """Get list of all registered widget types."""
        return list(self._widgets.keys())
    
    # ─────────────────────────────────────────────────────────────────────────
    # Data Parser Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_data_parser(self, parser_cls: Type, plugin_name: str = "") -> None:
        """
        Register a data parser class.
        
        Parameters:
            parser_cls: Parser class with `parser_name` attribute
            plugin_name: Name of the plugin registering this parser
        """
        parser_name = getattr(parser_cls, 'parser_name', parser_cls.__name__)
        
        if parser_name in self._data_parsers:
            logger.warning(f"Overwriting existing parser: {parser_name}")
        
        self._data_parsers[parser_name] = parser_cls
        self._component_owners[f"parser:{parser_name}"] = plugin_name
        logger.debug(f"Registered parser: {parser_name} from {plugin_name or 'core'}")
    
    def get_data_parser(self, parser_name: str) -> Optional[Type]:
        """Get a data parser class by name."""
        return self._data_parsers.get(parser_name)
    
    def get_all_data_parsers(self) -> Dict[str, Type]:
        """Get all registered data parsers."""
        return dict(self._data_parsers)
    
    # ─────────────────────────────────────────────────────────────────────────
    # LLM Generator Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_llm_generator(self, generator_cls: Type, plugin_name: str = "") -> None:
        """
        Register an LLM generator class.
        
        Parameters:
            generator_cls: Generator class with `generator_name` attribute
            plugin_name: Name of the plugin registering this generator
        """
        generator_name = getattr(generator_cls, 'generator_name', generator_cls.__name__)
        
        if generator_name in self._llm_generators:
            logger.warning(f"Overwriting existing LLM generator: {generator_name}")
        
        self._llm_generators[generator_name] = generator_cls
        self._component_owners[f"llm:{generator_name}"] = plugin_name
        logger.debug(f"Registered LLM generator: {generator_name} from {plugin_name or 'core'}")
    
    def get_llm_generator(self, generator_name: str) -> Optional[Type]:
        """Get an LLM generator class by name."""
        return self._llm_generators.get(generator_name)
    
    def get_all_llm_generators(self) -> Dict[str, Type]:
        """Get all registered LLM generators."""
        return dict(self._llm_generators)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Theme Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_theme(self, theme: Any, plugin_name: str = "") -> None:
        """
        Register a theme.
        
        Parameters:
            theme: Theme instance with `name` attribute
            plugin_name: Name of the plugin registering this theme
        """
        theme_name = getattr(theme, 'name', str(theme))
        
        if theme_name in self._themes:
            logger.warning(f"Overwriting existing theme: {theme_name}")
        
        self._themes[theme_name] = theme
        self._component_owners[f"theme:{theme_name}"] = plugin_name
        logger.debug(f"Registered theme: {theme_name} from {plugin_name or 'core'}")
        
        # Also register with the existing registry module for backward compat
        try:
            from ..registry import register_theme as legacy_register_theme
            # Legacy registry expects themes with 'id' attribute
            if hasattr(theme, 'id'):
                legacy_register_theme(theme)
        except (ImportError, AttributeError, Exception) as e:
            logger.debug(f"Could not register theme with legacy registry: {e}")
    
    def get_theme(self, theme_name: str) -> Optional[Any]:
        """Get a theme by name."""
        return self._themes.get(theme_name)
    
    def get_all_themes(self) -> Dict[str, Any]:
        """Get all registered themes."""
        return dict(self._themes)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Chart Type Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_chart_type(self, chart_cls: Type, plugin_name: str = "") -> None:
        """
        Register a chart type.
        
        Parameters:
            chart_cls: Chart class with `chart_type` attribute
            plugin_name: Name of the plugin registering this chart
        """
        chart_type = getattr(chart_cls, 'chart_type', chart_cls.__name__)
        
        if chart_type in self._chart_types:
            logger.warning(f"Overwriting existing chart type: {chart_type}")
        
        self._chart_types[chart_type] = chart_cls
        self._component_owners[f"chart:{chart_type}"] = plugin_name
        logger.debug(f"Registered chart type: {chart_type} from {plugin_name or 'core'}")
    
    def get_chart_type(self, chart_type: str) -> Optional[Type]:
        """Get a chart type class by name."""
        return self._chart_types.get(chart_type)
    
    def get_all_chart_types(self) -> Dict[str, Type]:
        """Get all registered chart types."""
        return dict(self._chart_types)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Page Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_page(self, page: Any, plugin_name: str = "") -> None:
        """
        Register a page definition.
        
        Parameters:
            page: Page definition with `id` attribute
            plugin_name: Name of the plugin registering this page
        """
        page_id = getattr(page, 'id', getattr(page, 'page_id', str(page)))
        
        if page_id in self._pages:
            logger.warning(f"Overwriting existing page: {page_id}")
        
        self._pages[page_id] = page
        self._component_owners[f"page:{page_id}"] = plugin_name
        logger.debug(f"Registered page: {page_id} from {plugin_name or 'core'}")
        
        # Also register with the existing registry module for backward compat
        try:
            from ..registry import register_page as legacy_register_page
            legacy_register_page(page)
        except ImportError:
            pass
    
    def get_page(self, page_id: str) -> Optional[Any]:
        """Get a page definition by ID."""
        return self._pages.get(page_id)
    
    def get_all_pages(self) -> Dict[str, Any]:
        """Get all registered pages."""
        return dict(self._pages)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Chart Generator Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_chart_generator(self, report_system_id: str, generator: Any, plugin_name: str = "") -> None:
        """
        Register a chart generator for a report system.
        
        Parameters:
            report_system_id: ID of the report system this generator handles
            generator: Generator instance with `generate(data_points, page_id, labels)` method
            plugin_name: Name of the plugin registering this generator
        """
        if report_system_id in self._chart_generators:
            logger.warning(f"Overwriting existing chart generator: {report_system_id}")
        
        self._chart_generators[report_system_id] = generator
        self._component_owners[f"chart_generator:{report_system_id}"] = plugin_name
        logger.debug(f"Registered chart generator: {report_system_id} from {plugin_name or 'core'}")
    
    def get_chart_generator(self, report_system_id: str) -> Optional[Any]:
        """Get a chart generator for a report system."""
        return self._chart_generators.get(report_system_id)
    
    def get_all_chart_generators(self) -> Dict[str, Any]:
        """Get all registered chart generators."""
        return dict(self._chart_generators)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Context Builder Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_context_builder(self, report_system_id: str, builder: Any, plugin_name: str = "") -> None:
        """
        Register a context builder for a report system.
        
        Context builders add report-specific template context (images, critical points, etc.)
        
        Parameters:
            report_system_id: ID of the report system this builder handles
            builder: Builder class with `build(data_points, stats, config, system_def)` method
            plugin_name: Name of the plugin registering this builder
        """
        if report_system_id in self._context_builders:
            logger.warning(f"Overwriting existing context builder: {report_system_id}")
        
        self._context_builders[report_system_id] = builder
        self._component_owners[f"context_builder:{report_system_id}"] = plugin_name
        logger.debug(f"Registered context builder: {report_system_id} from {plugin_name or 'core'}")
    
    def get_context_builder(self, report_system_id: str) -> Optional[Any]:
        """Get a context builder for a report system."""
        return self._context_builders.get(report_system_id)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Service Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_service(self, name: str, service: Any, plugin_name: str = "") -> None:
        """
        Register a service.
        
        Parameters:
            name: Service name (e.g., 'analytics', 'charts')
            service: Service instance or factory callable
            plugin_name: Name of the plugin registering this service
        """
        if name in self._services:
            logger.warning(f"Overwriting existing service: {name}")
        
        self._services[name] = service
        self._component_owners[f"service:{name}"] = plugin_name
        logger.debug(f"Registered service: {name} from {plugin_name or 'core'}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name."""
        service = self._services.get(name)
        # If it's a factory/callable, call it
        if callable(service) and not isinstance(service, type):
            return service()
        return service
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        return dict(self._services)
    
    def replace_service(self, name: str, service: Any, plugin_name: str = "") -> None:
        """
        Replace an existing service (for plugins that want to override core services).
        
        Parameters:
            name: Service name to replace
            service: New service instance or factory
            plugin_name: Name of the plugin replacing this service
        """
        if name not in self._services:
            logger.warning(f"Replacing non-existent service: {name}")
        
        self._services[name] = service
        self._component_owners[f"service:{name}"] = plugin_name
        logger.info(f"Service '{name}' replaced by {plugin_name or 'unknown'}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Report System Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_report_system(
        self, 
        name: str, 
        system_def: Any, 
        plugin_name: str = ""
    ) -> None:
        """
        Register a report system definition.
        
        Parameters:
            name: System name (e.g., 'png_data_points')
            system_def: Parsed system definition (dict from JSON)
            plugin_name: Name of the plugin registering this system
        """
        if name in self._report_systems:
            logger.warning(f"Overwriting existing report system: {name}")
        
        self._report_systems[name] = system_def
        self._component_owners[f"report_system:{name}"] = plugin_name
        logger.debug(f"Registered report system: {name} from {plugin_name or 'core'}")
    
    def get_report_system(self, name: str) -> Optional[Any]:
        """Get a report system definition by name."""
        return self._report_systems.get(name)
    
    def get_all_report_systems(self) -> Dict[str, Any]:
        """Get all registered report systems."""
        return dict(self._report_systems)
    
    def get_report_system_names(self) -> List[str]:
        """Get list of all registered report system names."""
        return list(self._report_systems.keys())
    
    # ─────────────────────────────────────────────────────────────────────────
    # Template Path Registration
    # ─────────────────────────────────────────────────────────────────────────
    
    def register_template_path(
        self, 
        path: Any,  # Path or str
        plugin_name: str = "",
        priority: int = 100
    ) -> None:
        """
        Register a template directory path.
        
        Templates from registered paths are loaded in priority order
        (lower numbers = higher priority).
        
        Parameters:
            path: Path to template directory
            plugin_name: Name of the plugin registering this path
            priority: Loading priority (default 100, game-review plugin uses 1000)
        """
        from pathlib import Path as PathClass
        path = PathClass(path)
        
        if not path.exists():
            logger.warning(f"Template path does not exist: {path}")
            return
        
        self._template_paths.append((path, plugin_name, priority))
        # Keep sorted by priority (lower = higher priority)
        self._template_paths.sort(key=lambda x: x[2])
        self._component_owners[f"template_path:{path}"] = plugin_name
        logger.debug(f"Registered template path: {path} from {plugin_name or 'core'}")
    
    def get_template_paths(self) -> List[Any]:
        """
        Get all registered template paths in priority order.
        
        Returns:
            List of Path objects
        """
        return [path for path, _, _ in self._template_paths]
    
    def get_all_template_registrations(self) -> List[tuple]:
        """Get all template path registrations with metadata."""
        return list(self._template_paths)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_component_owner(self, component_key: str) -> str:
        """Get the plugin that registered a component."""
        return self._component_owners.get(component_key, "")
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """
        Unregister all components from a specific plugin.
        
        Parameters:
            plugin_name: Name of the plugin to unregister
            
        Returns:
            Number of components unregistered
        """
        count = 0
        
        # Find all components owned by this plugin
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name
        ]
        
        for key in to_remove:
            ext_type, name = key.split(':', 1)
            
            if ext_type == 'widget' and name in self._widgets:
                del self._widgets[name]
                count += 1
            elif ext_type == 'parser' and name in self._data_parsers:
                del self._data_parsers[name]
                count += 1
            elif ext_type == 'llm' and name in self._llm_generators:
                del self._llm_generators[name]
                count += 1
            elif ext_type == 'theme' and name in self._themes:
                del self._themes[name]
                count += 1
            elif ext_type == 'chart' and name in self._chart_types:
                del self._chart_types[name]
                count += 1
            elif ext_type == 'page' and name in self._pages:
                del self._pages[name]
                count += 1
            elif ext_type == 'service' and name in self._services:
                del self._services[name]
                count += 1
            
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} components from plugin: {plugin_name}")
        return count
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about registered components."""
        return {
            'widgets': len(self._widgets),
            'data_parsers': len(self._data_parsers),
            'llm_generators': len(self._llm_generators),
            'themes': len(self._themes),
            'chart_types': len(self._chart_types),
            'pages': len(self._pages),
            'services': len(self._services),
        }
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        total = sum(stats.values())
        return f"<PluginRegistry: {total} components>"


# Global registry instance
_global_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = PluginRegistry()

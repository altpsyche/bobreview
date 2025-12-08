"""
Plugin registry for managing plugin components.

This registry composes focused registries, following the Interface Segregation Principle.
Each focused registry handles a single type of component.
"""

from typing import TYPE_CHECKING, Dict, List, Type, Any, Optional, Callable
import logging

from .registries import (
    ThemeRegistry,
    WidgetRegistry,
    DataParserRegistry,
    LLMGeneratorRegistry,
    ChartTypeRegistry,
    PageRegistry,
    ServiceRegistry,
    ReportSystemRegistry,
    ChartGeneratorRegistry,
    ContextBuilderRegistry,
    TemplatePathRegistry,
)

if TYPE_CHECKING:
    from .base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all plugin components.
    
    Composes focused registries, each handling a single type of component.
    This follows the Interface Segregation Principle - clients only depend
    on the registries they need.
    
    Example:
        registry = PluginRegistry()
        
        # Plugin registers a widget (new way - direct access)
        registry.widgets.register(MyCustomWidget)
        
        # Or use backward-compatible methods
        registry.register_widget(MyCustomWidget)
        
        # Application queries widgets
        widgets = registry.widgets.get_all()
    """
    
    def __init__(self):
        """Initialize registries for all extension points."""
        # Focused registries - each handles a single responsibility
        self.themes = ThemeRegistry()
        self.widgets = WidgetRegistry()
        self.data_parsers = DataParserRegistry()
        self.llm_generators = LLMGeneratorRegistry()
        self.chart_types = ChartTypeRegistry()
        self.pages = PageRegistry()
        self.services = ServiceRegistry()
        self.report_systems = ReportSystemRegistry()
        self.chart_generators = ChartGeneratorRegistry()
        self.context_builders = ContextBuilderRegistry()
        self.template_paths = TemplatePathRegistry()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Convenience Methods (Backward Compatibility)
    # ─────────────────────────────────────────────────────────────────────────
    # These methods delegate to focused registries for backward compatibility
    
    def register_widget(self, widget_cls: Type, plugin_name: str = "") -> None:
        """Register a widget class (delegates to widgets registry)."""
        self.widgets.register(widget_cls, plugin_name)
    
    def get_widget(self, widget_type: str) -> Optional[Type]:
        """Get a widget class by type (delegates to widgets registry)."""
        return self.widgets.get(widget_type)
    
    def get_all_widgets(self) -> Dict[str, Type]:
        """Get all registered widgets (delegates to widgets registry)."""
        return self.widgets.get_all()
    
    def get_widget_types(self) -> List[str]:
        """Get list of all registered widget types (delegates to widgets registry)."""
        return self.widgets.get_types()
    
    def register_data_parser(self, parser_cls: Type, plugin_name: str = "") -> None:
        """Register a data parser class (delegates to data_parsers registry)."""
        self.data_parsers.register(parser_cls, plugin_name)
    
    def get_data_parser(self, parser_name: str) -> Optional[Type]:
        """Get a data parser class by name (delegates to data_parsers registry)."""
        return self.data_parsers.get(parser_name)
    
    def get_all_data_parsers(self) -> Dict[str, Type]:
        """Get all registered data parsers (delegates to data_parsers registry)."""
        return self.data_parsers.get_all()
    
    def register_llm_generator(self, generator_cls: Type, plugin_name: str = "") -> None:
        """Register an LLM generator class (delegates to llm_generators registry)."""
        self.llm_generators.register(generator_cls, plugin_name)
    
    def get_llm_generator(self, generator_name: str) -> Optional[Type]:
        """Get an LLM generator class by name (delegates to llm_generators registry)."""
        return self.llm_generators.get(generator_name)
    
    def get_all_llm_generators(self) -> Dict[str, Type]:
        """Get all registered LLM generators (delegates to llm_generators registry)."""
        return self.llm_generators.get_all()
    
    def register_theme(self, theme: Any, plugin_name: str = "") -> None:
        """Register a theme (delegates to themes registry)."""
        self.themes.register(theme, plugin_name)
    
    def get_theme(self, theme_id: Optional[str] = None) -> Optional[Any]:
        """Get a theme by ID (delegates to themes registry)."""
        return self.themes.get(theme_id)
    
    def get_all_themes(self) -> Dict[str, Any]:
        """Get all registered themes (delegates to themes registry)."""
        return self.themes.get_all()
    
    def register_chart_type(self, chart_cls: Type, plugin_name: str = "") -> None:
        """Register a chart type (delegates to chart_types registry)."""
        self.chart_types.register(chart_cls, plugin_name)
    
    def get_chart_type(self, chart_type: str) -> Optional[Type]:
        """Get a chart type class by name (delegates to chart_types registry)."""
        return self.chart_types.get(chart_type)
    
    def get_all_chart_types(self) -> Dict[str, Type]:
        """Get all registered chart types (delegates to chart_types registry)."""
        return self.chart_types.get_all()
    
    def register_page(self, page: Any, plugin_name: str = "") -> None:
        """Register a page definition (delegates to pages registry)."""
        self.pages.register(page, plugin_name)
    
    def get_page(self, page_id: str) -> Optional[Any]:
        """Get a page definition by ID (delegates to pages registry)."""
        return self.pages.get(page_id)
    
    def get_all_pages(self) -> Dict[str, Any]:
        """Get all registered pages (delegates to pages registry)."""
        return self.pages.get_all()
    
    def register_service(self, name: str, service: Any, plugin_name: str = "") -> None:
        """Register a service (delegates to services registry)."""
        self.services.register(name, service, plugin_name)
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name (delegates to services registry)."""
        return self.services.get(name)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services (delegates to services registry)."""
        return self.services.get_all()
    
    def replace_service(self, name: str, service: Any, plugin_name: str = "") -> None:
        """Replace an existing service (delegates to services registry)."""
        self.services.replace(name, service, plugin_name)
    
    def register_report_system(
        self,
        name: str,
        system_def: Any,
        plugin_name: str = ""
    ) -> None:
        """Register a report system definition (delegates to report_systems registry)."""
        self.report_systems.register(name, system_def, plugin_name)
    
    def get_report_system(self, name: str) -> Optional[Any]:
        """Get a report system definition by name (delegates to report_systems registry)."""
        return self.report_systems.get(name)
    
    def get_all_report_systems(self) -> Dict[str, Any]:
        """Get all registered report systems (delegates to report_systems registry)."""
        return self.report_systems.get_all()
    
    def get_report_system_names(self) -> List[str]:
        """Get list of all registered report system names (delegates to report_systems registry)."""
        return self.report_systems.get_names()
    
    def register_chart_generator(
        self,
        report_system_id: str,
        generator: Any,
        plugin_name: str = ""
    ) -> None:
        """Register a chart generator (delegates to chart_generators registry)."""
        self.chart_generators.register(report_system_id, generator, plugin_name)
    
    def get_chart_generator(self, report_system_id: str) -> Optional[Any]:
        """Get a chart generator for a report system (delegates to chart_generators registry)."""
        return self.chart_generators.get(report_system_id)
    
    def get_all_chart_generators(self) -> Dict[str, Any]:
        """Get all registered chart generators (delegates to chart_generators registry)."""
        return self.chart_generators.get_all()
    
    def register_context_builder(
        self,
        report_system_id: str,
        builder: Any,
        plugin_name: str = ""
    ) -> None:
        """Register a context builder (delegates to context_builders registry)."""
        self.context_builders.register(report_system_id, builder, plugin_name)
    
    def get_context_builder(self, report_system_id: str) -> Optional[Any]:
        """Get a context builder for a report system (delegates to context_builders registry)."""
        return self.context_builders.get(report_system_id)
    
    def register_template_path(
        self,
        path: Any,
        plugin_name: str = "",
        priority: int = 100
    ) -> None:
        """Register a template directory path (delegates to template_paths registry)."""
        self.template_paths.register(path, plugin_name, priority)
    
    def get_template_paths(self) -> List[Any]:
        """Get all registered template paths (delegates to template_paths registry)."""
        return self.template_paths.get_paths()
    
    def get_all_template_registrations(self) -> List[tuple]:
        """Get all template path registrations (delegates to template_paths registry)."""
        return self.template_paths.get_all_registrations()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_component_owner(self, component_key: str) -> str:
        """
        Get the plugin that registered a component.
        
        Searches across all focused registries.
        """
        # Try each registry
        for registry in [
            self.themes, self.widgets, self.data_parsers, self.llm_generators,
            self.chart_types, self.pages, self.services, self.report_systems,
            self.chart_generators, self.context_builders, self.template_paths
        ]:
            owner = registry.get_component_owner(component_key)
            if owner:
                return owner
        return ""
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """
        Unregister all components from a specific plugin.
        
        Parameters:
            plugin_name: Name of the plugin to unregister
        
        Returns:
            Total number of components unregistered
        """
        total = 0
        # Unregister from all focused registries
        total += self.themes.unregister_plugin_components(plugin_name)
        total += self.widgets.unregister_plugin_components(plugin_name)
        total += self.data_parsers.unregister_plugin_components(plugin_name)
        total += self.llm_generators.unregister_plugin_components(plugin_name)
        total += self.chart_types.unregister_plugin_components(plugin_name)
        total += self.pages.unregister_plugin_components(plugin_name)
        total += self.services.unregister_plugin_components(plugin_name)
        total += self.report_systems.unregister_plugin_components(plugin_name)
        total += self.chart_generators.unregister_plugin_components(plugin_name)
        total += self.context_builders.unregister_plugin_components(plugin_name)
        total += self.template_paths.unregister_plugin_components(plugin_name)
        
        logger.info(f"Unregistered {total} total components from plugin: {plugin_name}")
        return total
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about registered components."""
        return {
            'widgets': len(self.widgets.get_all()),
            'data_parsers': len(self.data_parsers.get_all()),
            'llm_generators': len(self.llm_generators.get_all()),
            'themes': len(self.themes.get_all()),
            'chart_types': len(self.chart_types.get_all()),
            'pages': len(self.pages.get_all()),
            'services': len(self.services.get_all()),
            'report_systems': len(self.report_systems.get_all()),
            'chart_generators': len(self.chart_generators.get_all()),
            'context_builders': len(self.context_builders.get_all()),
            'template_paths': len(self.template_paths.get_paths()),
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

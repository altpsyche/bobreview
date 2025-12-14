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
    AnalyzerRegistry,
    ComponentRegistry,
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
        
        # Or use convenience methods
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
        self.analyzers = AnalyzerRegistry()
        self.components = ComponentRegistry()
    
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
            self.chart_generators, self.context_builders, self.template_paths,
            self.analyzers, self.components
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
        total += self.analyzers.unregister_plugin_components(plugin_name)
        total += self.components.unregister_plugin_components(plugin_name)
        
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
            'analyzers': len(self.analyzers.get_all()),
            'components': len(self.components.get_all()),
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

"""
Plugin registry for managing plugin components.

Plugin-First Architecture:
- Most registries removed (plugins handle their own features)
- Only infrastructure registries remain
"""

from typing import TYPE_CHECKING, Dict, Optional
import logging

from .registries import (
    ThemeRegistry,
    DataParserRegistry,
    ServiceRegistry,
    ReportSystemRegistry,
    TemplatePathRegistry,
)

if TYPE_CHECKING:
    from .base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for plugin infrastructure.
    
    Plugin-first design: Only infrastructure registries remain.
    Domain-specific registries (widgets, charts, LLM, etc.) removed.
    Plugins use ComponentRegistry from core.components for features.
    """
    
    def __init__(self):
        """Initialize infrastructure registries."""
        self.themes = ThemeRegistry()
        self.data_parsers = DataParserRegistry()
        self.services = ServiceRegistry()
        self.report_systems = ReportSystemRegistry()
        self.template_paths = TemplatePathRegistry()
    
    def get_component_owner(self, component_key: str) -> str:
        """Get the plugin that registered a component."""
        for registry in [
            self.themes, self.data_parsers, self.services,
            self.report_systems, self.template_paths
        ]:
            owner = registry.get_component_owner(component_key)
            if owner:
                return owner
        return ""
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all components from a specific plugin."""
        total = 0
        total += self.themes.unregister_plugin_components(plugin_name)
        total += self.data_parsers.unregister_plugin_components(plugin_name)
        total += self.services.unregister_plugin_components(plugin_name)
        total += self.report_systems.unregister_plugin_components(plugin_name)
        total += self.template_paths.unregister_plugin_components(plugin_name)
        
        logger.info(f"Unregistered {total} components from plugin: {plugin_name}")
        return total
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about registered components."""
        return {
            'themes': len(self.themes.get_all()),
            'data_parsers': len(self.data_parsers.get_all()),
            'services': len(self.services.get_all()),
            'report_systems': len(self.report_systems.get_all()),
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

"""
Plugin registry for managing plugin components.

Plugin-First Architecture:
- Most registries removed (plugins handle their own features)
- Only infrastructure registries remain
- Themes now owned entirely by plugins
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
import logging
import threading

from .registries import (
    DataParserRegistry,
    RegistryCollisionError,
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
    Domain-specific registries (widgets, charts, LLM, themes, etc.) removed.
    Plugins use ComponentRegistry from core.components for features.
    """
    
    def __init__(self):
        """Initialize infrastructure registries."""
        self.data_parsers = DataParserRegistry()
        self.services = ServiceRegistry()
        self.report_systems = ReportSystemRegistry()
        self.template_paths = TemplatePathRegistry()
    
    def get_component_owner(self, component_key: str) -> str:
        """Get the plugin that registered a component."""
        for registry in [
            self.data_parsers, self.services,
            self.report_systems, self.template_paths
        ]:
            owner = registry.get_component_owner(component_key)
            if owner:
                return owner
        return ""
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all components from a specific plugin."""
        total = 0
        total += self.data_parsers.unregister_plugin_components(plugin_name)
        total += self.services.unregister_plugin_components(plugin_name)
        total += self.report_systems.unregister_plugin_components(plugin_name)
        total += self.template_paths.unregister_plugin_components(plugin_name)
        
        logger.info(f"Unregistered {total} components from plugin: {plugin_name}")
        return total
    
    def set_strict(self, strict: bool) -> None:
        """
        Enable or disable strict collision mode on all sub-registries.

        When strict is True, registering a component key already owned by
        a different plugin raises RegistryCollisionError.
        """
        for registry in self._all_registries():
            registry.set_strict(strict)

    def get_collision_log(self) -> List[Tuple[str, str, str]]:
        """
        Get the combined collision log from all sub-registries.

        Returns:
            List of (component_key, previous_owner, new_owner) tuples
        """
        log: List[Tuple[str, str, str]] = []
        for registry in self._all_registries():
            log.extend(registry.get_collision_log())
        return log

    def _all_registries(self):
        """Yield all sub-registries."""
        return [
            self.data_parsers, self.services,
            self.report_systems, self.template_paths,
        ]

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about registered components."""
        return {
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
_registry_lock = threading.Lock()


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance (thread-safe)."""
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = PluginRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = PluginRegistry()

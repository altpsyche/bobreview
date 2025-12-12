"""
Abstract interface for extension points.

Core code uses these interfaces instead of registry/loader directly, enabling:
- Dependency inversion (core depends on abstractions)
- Easier testing (mock implementations)
- Future flexibility (different backends)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import PluginRegistry
    from .loader import PluginLoader


class IExtensionPoint(ABC):
    """
    Abstract interface for accessing plugin-provided implementations.
    
    Core code depends on this interface, not the concrete PluginRegistry.
    """
    
    @abstractmethod
    def get_theme(self, name: str = None) -> Any:
        """Get a theme implementation by name."""
        pass
    
    @abstractmethod
    def get_llm_generator(self, name: str) -> Any:
        """Get an LLM generator by ID or name."""
        pass
    
    @abstractmethod
    def get_data_parser(self, parser_type: str) -> Any:
        """Get a data parser by type."""
        pass
    
    @abstractmethod
    def get_report_system(self, name: str) -> Any:
        """Get a report system definition."""
        pass
    
    @abstractmethod
    def get_context_builder(self, system_id: str) -> Any:
        """Get context builder for a report system."""
        pass
    
    @abstractmethod
    def get_chart_generator(self, system_id: str) -> Any:
        """Get chart generator for a report system."""
        pass
    
    @abstractmethod
    def get_template_paths(self) -> List[tuple]:
        """Get all registered template paths with priorities."""
        pass
    
    @abstractmethod
    def get_all_parsers(self) -> Dict[str, Any]:
        """Get all registered data parsers."""
        pass
    
    @abstractmethod
    def get_all_report_systems(self) -> Dict[str, Any]:
        """Get all registered report systems."""
        pass
    
    @abstractmethod
    def get_component_owner(self, key: str) -> str:
        """Get plugin name that owns a component."""
        pass


class IPluginManager(ABC):
    """
    Abstract interface for plugin lifecycle management.
    
    Core code depends on this interface, not the concrete PluginLoader.
    """
    
    @abstractmethod
    def discover(self) -> List[Any]:
        """Discover available plugins."""
        pass
    
    @abstractmethod
    def load(self, name: str) -> Any:
        """Load a plugin by name."""
        pass
    
    @abstractmethod
    def is_loaded(self, name: str) -> bool:
        """Check if a plugin is loaded."""
        pass
    
    @abstractmethod
    def get_loaded_plugins(self) -> List[Any]:
        """Get all loaded plugins."""
        pass
    
    @abstractmethod
    def get_discovered_plugins(self) -> List[Any]:
        """Get all discovered plugins."""
        pass


class ExtensionPointProvider(IExtensionPoint):
    """
    Concrete implementation backed by PluginRegistry.
    
    This is the default implementation used at runtime.
    """
    
    def __init__(self, registry: "PluginRegistry" = None):
        """
        Initialize with optional registry injection.
        
        Parameters:
            registry: PluginRegistry instance (uses global if None)
        """
        self._registry = registry
    
    @property
    def registry(self) -> "PluginRegistry":
        """Lazy-load registry on first access."""
        if self._registry is None:
            from .registry import get_registry
            self._registry = get_registry()
        return self._registry
    
    def get_theme(self, name: str = None) -> Any:
        return self.registry.themes.get(name)
    
    def get_llm_generator(self, name: str) -> Any:
        return self.registry.llm_generators.get(name)
    
    def get_data_parser(self, parser_type: str) -> Any:
        return self.registry.data_parsers.get(parser_type)
    
    def get_report_system(self, name: str) -> Any:
        return self.registry.report_systems.get(name)
    
    def get_context_builder(self, system_id: str) -> Any:
        return self.registry.context_builders.get(system_id)
    
    def get_chart_generator(self, system_id: str) -> Any:
        return self.registry.chart_generators.get(system_id)
    
    def get_template_paths(self) -> List[tuple]:
        return self.registry.template_paths.get_all_registrations()
    
    def get_all_parsers(self) -> Dict[str, Any]:
        return self.registry.data_parsers.get_all()
    
    def get_all_report_systems(self) -> Dict[str, Any]:
        return self.registry.report_systems.get_all()
    
    def get_component_owner(self, key: str) -> str:
        return self.registry.get_component_owner(key)


class PluginManagerProvider(IPluginManager):
    """
    Concrete implementation backed by PluginLoader.
    
    This is the default implementation used at runtime.
    """
    
    def __init__(self, loader: "PluginLoader" = None):
        """
        Initialize with optional loader injection.
        
        Parameters:
            loader: PluginLoader instance (uses global if None)
        """
        self._loader = loader
    
    @property
    def loader(self) -> "PluginLoader":
        """Lazy-load loader on first access."""
        if self._loader is None:
            from .loader import get_loader
            self._loader = get_loader()
        return self._loader
    
    def discover(self) -> List[Any]:
        return self.loader.discover()
    
    def load(self, name: str) -> Any:
        return self.loader.load(name)
    
    def is_loaded(self, name: str) -> bool:
        return self.loader.is_loaded(name)
    
    def get_loaded_plugins(self) -> List[Any]:
        return self.loader.get_loaded_plugins()
    
    def get_discovered_plugins(self) -> List[Any]:
        return self.loader.get_discovered_plugins()


# Global instances
_extension_point: Optional[IExtensionPoint] = None
_plugin_manager: Optional[IPluginManager] = None


def get_extension_point() -> IExtensionPoint:
    """Get the global extension point instance."""
    global _extension_point
    if _extension_point is None:
        _extension_point = ExtensionPointProvider()
    return _extension_point


def get_plugin_manager() -> IPluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManagerProvider()
    return _plugin_manager


def reset_extension_point() -> None:
    """Reset the global extension point (for testing)."""
    global _extension_point
    _extension_point = None


def reset_plugin_manager() -> None:
    """Reset the global plugin manager (for testing)."""
    global _plugin_manager
    _plugin_manager = None

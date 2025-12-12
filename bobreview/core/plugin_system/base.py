"""
Base classes for BobReview plugins.

Plugins extend BobReview by registering components at load time.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, ClassVar

if TYPE_CHECKING:
    from .registry import PluginRegistry


@dataclass
class PluginInfo:
    """Information about a plugin for display purposes."""
    name: str
    version: str
    author: str
    description: str
    enabled: bool = True
    loaded: bool = False
    path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    provides: dict = field(default_factory=dict)


class BasePlugin(ABC):
    """
    Abstract base class for all BobReview plugins.
    
    Plugins must implement the `on_load` method to register their components.
    Other lifecycle hooks are optional.
    
    Example:
        class MyPlugin(BasePlugin):
            name = "My Plugin"
            version = "1.0.0"
            author = "Developer"
            description = "Adds custom widgets"
            
            def on_load(self, registry: PluginRegistry) -> None:
                registry.register_widget(MyCustomWidget)
    """
    
    # Required metadata (must be set by subclasses)
    name: str = ""
    version: str = "0.0.0"
    author: str = "Unknown"
    description: str = ""
    
    # Optional metadata
    dependencies: ClassVar[List[str]] = []
    
    def __init__(self):
        self._config = {}
    
    def get_config(self) -> dict:
        """Get plugin configuration."""
        return self._config
    
    def set_config(self, config: dict) -> None:
        """Set plugin configuration."""
        self._config = config or {}
    
    @abstractmethod
    def on_load(self, registry: 'PluginRegistry') -> None:
        """
        Called when the plugin is loaded.
        
        Register all plugin components here (widgets, parsers, themes, etc.).
        
        Parameters:
            registry: The plugin registry to register components with
        """
        ...
    
    def on_unload(self) -> None:
        """
        Called when the plugin is unloaded.
        
        Override to cleanup resources (close connections, etc.).
        """
        pass
    
    def on_report_start(self, context: dict) -> None:
        """
        Called when report generation begins.
        
        Override to perform setup before report generation.
        
        Parameters:
            context: Report context with config, data source, etc.
        """
        pass
    
    def on_report_complete(self, result: dict) -> None:
        """
        Called when report generation completes.
        
        Override to perform cleanup or post-processing.
        
        Parameters:
            result: Report result with pages, stats, etc.
        """
        pass
    
    def get_info(self, loaded: bool = False) -> PluginInfo:
        """Get plugin information for display."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            author=self.author,
            description=self.description,
            dependencies=self.dependencies,
            loaded=loaded,
        )
    
    def __repr__(self) -> str:
        return f"<Plugin: {self.name} v{self.version}>"

"""
Analyzer registry for plugin-provided data analyzers.

Plugins register their analyzer functions here. The AnalyticsService
looks up the registered analyzer instead of importing directly from plugins.
"""

from typing import Callable, Dict, Any, List, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


# Type alias for analyzer functions
AnalyzerFunc = Callable[[List[Dict[str, Any]], Any, List[str], Any], Dict[str, Any]]


class AnalyzerRegistry(BaseRegistry):
    """
    Registry for plugin-provided analyzer functions.
    
    Plugins register their analyzer functions here during initialization.
    The AnalyticsService uses this registry to find the appropriate analyzer.
    
    Example:
        # In plugin.py (preferred - via PluginHelper)
        helper = PluginHelper(registry, self.name)
        helper.add_analyzer('performance', analyze_performance_data)
        
        # Or direct registry access
        registry.analyzers.register('performance', analyze_fn, plugin_name='my-plugin')
        
        # In AnalyticsService
        analyzer = registry.analyzers.get('performance')
        if analyzer:
            stats = analyzer(data_points, config, metrics, metrics_config)
    """
    
    def __init__(self):
        super().__init__()
        self._analyzers: Dict[str, AnalyzerFunc] = {}
        self._default: Optional[str] = None
    
    def register(
        self,
        name: str,
        analyzer: AnalyzerFunc,
        plugin_name: str = "",
        default: bool = False
    ) -> None:
        """
        Register an analyzer function.
        
        Parameters:
            name: Unique name for this analyzer
            analyzer: The analyzer function
            plugin_name: Name of the plugin registering this analyzer
            default: If True, set as the default analyzer
        """
        self._analyzers[name] = analyzer
        self._register_component(f"analyzer:{name}", plugin_name)
        logger.debug(f"Registered analyzer: {name} (plugin: {plugin_name or 'core'})")
        
        if default or self._default is None:
            self._default = name
            logger.debug(f"Set default analyzer: {name}")
    
    def get(self, name: Optional[str] = None) -> Optional[AnalyzerFunc]:
        """
        Get an analyzer by name, or the default analyzer.
        
        Parameters:
            name: Analyzer name. If None, returns the default.
            
        Returns:
            The analyzer function, or None if not found.
        """
        if name:
            return self._analyzers.get(name)
        
        if self._default:
            return self._analyzers.get(self._default)
        
        return None
    
    def get_all(self) -> Dict[str, AnalyzerFunc]:
        """Get all registered analyzers."""
        return dict(self._analyzers)
    
    def list(self) -> List[str]:
        """List all registered analyzer names."""
        return list(self._analyzers.keys())
    
    def has(self, name: str) -> bool:
        """Check if an analyzer is registered."""
        return name in self._analyzers
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """
        Unregister all analyzers from a specific plugin.
        
        Parameters:
            plugin_name: Name of the plugin to unregister
        
        Returns:
            Number of analyzers unregistered
        """
        # Find analyzers owned by this plugin
        to_remove = [
            name for name, owner in self._component_owners.items()
            if owner == plugin_name and name.startswith('analyzer:')
        ]
        
        # Remove from analyzers dict
        for name in to_remove:
            analyzer_name = name.split(':', 1)[1]
            if analyzer_name in self._analyzers:
                del self._analyzers[analyzer_name]
            if self._default == analyzer_name:
                self._default = next(iter(self._analyzers), None)
        
        # Call parent to clean up ownership tracking
        return super().unregister_plugin_components(plugin_name)
    
    def clear(self) -> None:
        """Clear all registered analyzers (for testing)."""
        self._analyzers.clear()
        self._component_owners.clear()
        self._default = None

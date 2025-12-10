"""
Analyzer registry for plugin-provided data analyzers.

Plugins register their analyzer functions here. The AnalyticsService
looks up the registered analyzer instead of importing directly from plugins.
"""

from typing import Callable, Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# Type alias for analyzer functions
AnalyzerFunc = Callable[[List[Dict[str, Any]], Any, List[str], Any], Dict[str, Any]]


class AnalyzerRegistry:
    """
    Registry for plugin-provided analyzer functions.
    
    Plugins register their analyzer functions here during initialization.
    The AnalyticsService uses this registry to find the appropriate analyzer.
    
    Example:
        # In plugin.py
        from bobreview.core.plugin_system.registries import analyzer_registry
        
        analyzer_registry.register('performance', analyze_performance_data)
        
        # In AnalyticsService
        analyzer = analyzer_registry.get('performance')
        if analyzer:
            stats = analyzer(data_points, config, metrics, metrics_config)
    """
    
    def __init__(self):
        self._analyzers: Dict[str, AnalyzerFunc] = {}
        self._default: Optional[str] = None
    
    def register(self, name: str, analyzer: AnalyzerFunc, default: bool = False) -> None:
        """
        Register an analyzer function.
        
        Parameters:
            name: Unique name for this analyzer
            analyzer: The analyzer function
            default: If True, set as the default analyzer
        """
        self._analyzers[name] = analyzer
        logger.debug(f"Registered analyzer: {name}")
        
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
    
    def list(self) -> List[str]:
        """List all registered analyzer names."""
        return list(self._analyzers.keys())
    
    def has(self, name: str) -> bool:
        """Check if an analyzer is registered."""
        return name in self._analyzers
    
    def clear(self) -> None:
        """Clear all registered analyzers (for testing)."""
        self._analyzers.clear()
        self._default = None


# Global registry instance
_analyzer_registry = AnalyzerRegistry()


def get_analyzer_registry() -> AnalyzerRegistry:
    """Get the global analyzer registry."""
    return _analyzer_registry

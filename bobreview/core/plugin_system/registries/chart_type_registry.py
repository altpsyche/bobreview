"""
Chart type registry for managing chart types.
"""

from typing import Dict, Type, Optional, Any
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ChartTypeRegistry(BaseRegistry):
    """
    Registry for chart types.
    
    Single Responsibility: Chart type registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the chart type registry."""
        super().__init__()
        self._chart_types: Dict[str, Any] = {}
    
    def register(self, chart_type_id: str, chart_config: Any, plugin_name: str = "") -> None:
        """
        Register a chart type.
        
        Parameters:
            chart_type_id: Unique identifier for the chart type
            chart_config: Chart configuration (dict or class)
            plugin_name: Name of the plugin registering this chart type
        """
        if chart_type_id in self._chart_types:
            logger.warning(f"Overwriting existing chart type: {chart_type_id}")
        
        self._chart_types[chart_type_id] = chart_config
        self._register_component(f"chart:{chart_type_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered chart type: {chart_type_id} from {plugin_name or 'core'}")
    
    def get(self, chart_type: str) -> Optional[Any]:
        """Get a chart type class by name."""
        return self._chart_types.get(chart_type)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered chart types."""
        return dict(self._chart_types)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all chart types from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('chart:')
        ]
        
        for key in to_remove:
            chart_type = key.split(':', 1)[1]
            if chart_type in self._chart_types:
                del self._chart_types[chart_type]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} chart types from plugin: {plugin_name}")
        return count


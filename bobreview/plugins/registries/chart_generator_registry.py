"""
Chart generator registry for managing chart generators per report system.
"""

from typing import Dict, Any, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ChartGeneratorRegistry(BaseRegistry):
    """
    Registry for chart generators.
    
    Single Responsibility: Chart generator registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the chart generator registry."""
        super().__init__()
        self._generators: Dict[str, Any] = {}
    
    def register(self, report_system_id: str, generator: Any, plugin_name: str = "") -> None:
        """
        Register a chart generator for a report system.
        
        Parameters:
            report_system_id: ID of the report system this generator handles
            generator: Generator instance with `generate(data_points, page_id, labels)` method
            plugin_name: Name of the plugin registering this generator
        """
        if report_system_id in self._generators:
            logger.warning(f"Overwriting existing chart generator: {report_system_id}")
        
        self._generators[report_system_id] = generator
        self._register_component(f"chart_generator:{report_system_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered chart generator: {report_system_id} from {plugin_name or 'core'}")
    
    def get(self, report_system_id: str) -> Optional[Any]:
        """Get a chart generator for a report system."""
        return self._generators.get(report_system_id)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered chart generators."""
        return dict(self._generators)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all chart generators from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('chart_generator:')
        ]
        
        for key in to_remove:
            system_id = key.split(':', 1)[1]
            if system_id in self._generators:
                del self._generators[system_id]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} chart generators from plugin: {plugin_name}")
        return count


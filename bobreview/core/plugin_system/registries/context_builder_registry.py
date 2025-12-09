"""
Context builder registry for managing context builders per report system.
"""

from typing import Dict, Any, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ContextBuilderRegistry(BaseRegistry):
    """
    Registry for context builders.
    
    Single Responsibility: Context builder registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the context builder registry."""
        super().__init__()
        self._builders: Dict[str, Any] = {}
    
    def register(self, report_system_id: str, builder: Any, plugin_name: str = "") -> None:
        """
        Register a context builder for a report system.
        
        Context builders add report-specific template context (images, critical points, etc.)
        
        Parameters:
            report_system_id: ID of the report system this builder handles
            builder: Builder class with `build(data_points, stats, config, system_def)` method
            plugin_name: Name of the plugin registering this builder
        """
        if report_system_id in self._builders:
            logger.warning(f"Overwriting existing context builder: {report_system_id}")
        
        self._builders[report_system_id] = builder
        self._register_component(f"context_builder:{report_system_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered context builder: {report_system_id} from {plugin_name or 'core'}")
    
    def get(self, report_system_id: str) -> Optional[Any]:
        """Get a context builder for a report system."""
        return self._builders.get(report_system_id)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered context builders."""
        return dict(self._builders)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all context builders from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('context_builder:')
        ]
        
        for key in to_remove:
            system_id = key.split(':', 1)[1]
            if system_id in self._builders:
                del self._builders[system_id]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} context builders from plugin: {plugin_name}")
        return count


"""
Report system registry for managing report system definitions.
"""

from typing import Dict, Any, Optional, List
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ReportSystemRegistry(BaseRegistry):
    """
    Registry for report system definitions.
    
    Single Responsibility: Report system registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the report system registry."""
        super().__init__()
        self._report_systems: Dict[str, Any] = {}
    
    def register(self, name: str, system_def: Any, plugin_name: str = "") -> None:
        """
        Register a report system definition.
        
        Parameters:
            name: System name (e.g., 'png_data_points')
            system_def: Parsed system definition (dict from JSON)
            plugin_name: Name of the plugin registering this system
        """
        if name in self._report_systems:
            logger.warning(f"Overwriting existing report system: {name}")
        
        self._report_systems[name] = system_def
        self._register_component(f"report_system:{name}", plugin_name, overwrite=True)
        logger.debug(f"Registered report system: {name} from {plugin_name or 'core'}")
    
    def get(self, name: str) -> Optional[Any]:
        """Get a report system definition by name."""
        return self._report_systems.get(name)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered report systems."""
        return dict(self._report_systems)
    
    def get_names(self) -> List[str]:
        """Get list of all registered report system names."""
        return list(self._report_systems.keys())
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all report systems from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('report_system:')
        ]
        
        for key in to_remove:
            system_name = key.split(':', 1)[1]
            if system_name in self._report_systems:
                del self._report_systems[system_name]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} report systems from plugin: {plugin_name}")
        return count


"""
Base registry class for shared functionality.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseRegistry:
    """
    Base class for component registries.
    
    Provides common functionality for tracking component owners.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._component_owners: Dict[str, str] = {}  # component_key -> plugin_name
    
    def _register_component(
        self,
        component_key: str,
        plugin_name: str = "",
        overwrite: bool = False
    ) -> None:
        """
        Register component ownership.
        
        Parameters:
            component_key: Unique key for the component
            plugin_name: Name of the plugin registering this component
            overwrite: Whether to allow overwriting existing registrations
        """
        if component_key in self._component_owners and not overwrite:
            logger.warning(f"Component already registered: {component_key}")
        
        self._component_owners[component_key] = plugin_name
    
    def get_component_owner(self, component_key: str) -> Optional[str]:
        """
        Get the plugin that registered a component.
        
        Parameters:
            component_key: Component key
        
        Returns:
            Plugin name or None
        """
        return self._component_owners.get(component_key)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """
        Unregister all components from a specific plugin.
        
        Parameters:
            plugin_name: Name of the plugin to unregister
        
        Returns:
            Number of components unregistered
        """
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name
        ]
        
        for key in to_remove:
            del self._component_owners[key]
        
        return len(to_remove)


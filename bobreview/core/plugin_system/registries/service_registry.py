"""
Service registry for managing services.
"""

from typing import Dict, Any, Optional, Callable
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ServiceRegistry(BaseRegistry):
    """
    Registry for services.
    
    Single Responsibility: Service registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the service registry."""
        super().__init__()
        self._services: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any, plugin_name: str = "") -> None:
        """
        Register a service.
        
        Parameters:
            name: Service name (e.g., 'analytics', 'charts')
            service: Service instance or factory callable
            plugin_name: Name of the plugin registering this service
        """
        if name in self._services:
            logger.warning(f"Overwriting existing service: {name}")
        
        self._services[name] = service
        self._register_component(f"service:{name}", plugin_name, overwrite=True)
        logger.debug(f"Registered service: {name} from {plugin_name or 'core'}")
    
    def get(self, name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        If the service is a factory/callable, it will be called.
        """
        service = self._services.get(name)
        # If it's a factory/callable, call it
        if callable(service) and not isinstance(service, type):
            return service()
        return service
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered services."""
        return dict(self._services)
    
    def replace(self, name: str, service: Any, plugin_name: str = "") -> None:
        """
        Replace an existing service (for plugins that want to override core services).
        
        Parameters:
            name: Service name to replace
            service: New service instance or factory
            plugin_name: Name of the plugin replacing this service
        """
        if name not in self._services:
            logger.warning(f"Replacing non-existent service: {name}")
        
        self._services[name] = service
        self._register_component(f"service:{name}", plugin_name, overwrite=True)
        logger.info(f"Service '{name}' replaced by {plugin_name or 'unknown'}")
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all services from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('service:')
        ]
        
        for key in to_remove:
            service_name = key.split(':', 1)[1]
            if service_name in self._services:
                del self._services[service_name]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} services from plugin: {plugin_name}")
        return count


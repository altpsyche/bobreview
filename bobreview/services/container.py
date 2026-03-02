"""
Service container for dependency injection.

The ServiceContainer manages service instances and allows plugins
to register or replace services at runtime.
"""

from typing import Dict, Any, Optional, Callable, Type
import logging
import threading

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Dependency injection container for BobReview services.
    
    Services can be registered as:
    - Instances: Directly usable objects
    - Factories: Callables that create instances on demand
    - Classes: Types that will be instantiated on first access
    
    Example:
        container = ServiceContainer()
        
        # Register instance
        container.register('analytics', AnalyticsService())
        
        # Register factory
        container.register_factory('charts', lambda: ChartService(theme='dark'))
        
        # Get service
        analytics = container.get('analytics')
        
        # Plugin can replace service
        container.replace('analytics', CustomAnalyticsService())
    """
    
    def __init__(self):
        """Initialize empty service container."""
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._classes: Dict[str, Type] = {}
        self._singletons: Dict[str, bool] = {}  # Track which should be singletons
    
    def register(self, name: str, service: Any, singleton: bool = True) -> None:
        """
        Register a service instance.
        
        Parameters:
            name: Service name (e.g., 'analytics', 'charts')
            service: Service instance
            singleton: If True, same instance returned on every get()
        """
        self._instances[name] = service
        self._singletons[name] = singleton
        logger.debug(f"Registered service: {name}")
    
    def register_factory(
        self, 
        name: str, 
        factory: Callable[[], Any],
        singleton: bool = True
    ) -> None:
        """
        Register a factory function that creates service instances.
        
        Parameters:
            name: Service name
            factory: Callable that returns a service instance
            singleton: If True, factory called once and instance cached
        """
        self._factories[name] = factory
        self._singletons[name] = singleton
        # Remove any existing instance
        if name in self._instances:
            del self._instances[name]
        logger.debug(f"Registered factory for: {name}")
    
    def register_class(
        self, 
        name: str, 
        cls: Type,
        singleton: bool = True
    ) -> None:
        """
        Register a class to be instantiated on first access.
        
        Parameters:
            name: Service name
            cls: Class to instantiate
            singleton: If True, class instantiated once and cached
        """
        self._classes[name] = cls
        self._singletons[name] = singleton
        # Remove any existing instance
        if name in self._instances:
            del self._instances[name]
        logger.debug(f"Registered class for: {name}")
    
    def get(self, name: str) -> Any:
        """
        Get a service by name.
        
        Parameters:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
        """
        # Check for cached instance
        if name in self._instances:
            return self._instances[name]
        
        # Check for factory
        if name in self._factories:
            instance = self._factories[name]()
            if self._singletons.get(name, True):
                self._instances[name] = instance
                del self._factories[name]
            return instance
        
        # Check for class
        if name in self._classes:
            instance = self._classes[name]()
            if self._singletons.get(name, True):
                self._instances[name] = instance
                del self._classes[name]
            return instance
        
        raise KeyError(f"Service not found: {name}")
    
    def get_optional(self, name: str) -> Optional[Any]:
        """Get a service or None if not registered."""
        try:
            return self.get(name)
        except KeyError:
            return None
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return (
            name in self._instances or 
            name in self._factories or 
            name in self._classes
        )
    
    def replace(self, name: str, service: Any) -> None:
        """
        Replace an existing service.
        
        This is the primary method for plugins to override core services.
        
        Parameters:
            name: Service name to replace
            service: New service instance
        """
        old_existed = self.has(name)
        
        # Clear any factories/classes
        if name in self._factories:
            del self._factories[name]
        if name in self._classes:
            del self._classes[name]
        
        self._instances[name] = service
        
        if old_existed:
            logger.info(f"Replaced service: {name}")
        else:
            logger.warning(f"Replacing non-existent service: {name}")
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a service.
        
        Parameters:
            name: Service name to remove
            
        Returns:
            True if service was removed, False if not found
        """
        removed = False
        
        if name in self._instances:
            del self._instances[name]
            removed = True
        if name in self._factories:
            del self._factories[name]
            removed = True
        if name in self._classes:
            del self._classes[name]
            removed = True
        if name in self._singletons:
            del self._singletons[name]
        
        return removed
    
    def list_services(self) -> Dict[str, str]:
        """
        List all registered services with their types.
        
        Returns:
            Dict mapping service name to type ('instance', 'factory', 'class')
        """
        services = {}
        
        for name in self._instances:
            services[name] = 'instance'
        for name in self._factories:
            if name not in services:
                services[name] = 'factory'
        for name in self._classes:
            if name not in services:
                services[name] = 'class'
        
        return services
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._instances.clear()
        self._factories.clear()
        self._classes.clear()
        self._singletons.clear()
    
    def __contains__(self, name: str) -> bool:
        return self.has(name)
    
    def __repr__(self) -> str:
        count = len(self.list_services())
        return f"<ServiceContainer: {count} services>"


# Global service container
_global_container: Optional[ServiceContainer] = None
_container_lock = threading.Lock()


def get_container() -> ServiceContainer:
    """Get the global service container (thread-safe)."""
    global _global_container
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = ServiceContainer()
    return _global_container


def reset_container() -> None:
    """Reset the global service container."""
    global _global_container
    _global_container = ServiceContainer()

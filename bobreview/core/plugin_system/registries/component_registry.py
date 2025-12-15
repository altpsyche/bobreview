"""
Component registry for managing UI components.

Plugins register reusable UI components that templates can render dynamically.
"""

from typing import Dict, Type, Optional, List, Any
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ComponentRegistry(BaseRegistry):
    """
    Registry for UI components.
    
    Components are reusable UI elements that plugins define and templates render.
    
    Example:
        registry.components.register('stat_card', StatCardComponent, 'my_plugin')
        component_cls = registry.components.get('stat_card')
        component = component_cls()
        html = component.render({'title': 'Total', 'value': 42}, context)
    """
    
    def __init__(self):
        """Initialize the component registry."""
        super().__init__()
        self._components: Dict[str, Type] = {}
        self._instances: Dict[str, Any] = {}  # Cached instances
    
    def register(self, component_id: str, component_cls: Type, plugin_name: str = "") -> None:
        """
        Register a component class.
        
        Parameters:
            component_id: Unique identifier for the component (e.g., 'stat_card')
            component_cls: Class implementing ComponentInterface
            plugin_name: Name of the plugin registering this component
        """
        if component_id in self._components:
            logger.warning(f"Overwriting existing component: {component_id}")
        
        self._components[component_id] = component_cls
        self._instances.pop(component_id, None)  # Clear cached instance
        self._register_component(f"component:{component_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered component: {component_id} from {plugin_name or 'core'}")
    
    def get(self, component_id: str) -> Optional[Type]:
        """Get a component class by ID."""
        return self._components.get(component_id)
    
    def get_instance(self, component_id: str) -> Optional[Any]:
        """
        Get a component instance (cached).
        
        Creates the instance on first access and caches it.
        """
        if component_id not in self._instances:
            component_cls = self._components.get(component_id)
            if component_cls:
                self._instances[component_id] = component_cls()
        return self._instances.get(component_id)
    
    def get_all(self) -> Dict[str, Type]:
        """Get all registered components."""
        return dict(self._components)
    
    def get_ids(self) -> List[str]:
        """Get list of all registered component IDs."""
        return list(self._components.keys())
    
    def render(self, component_id: str, props: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Render a component by ID.
        
        Parameters:
            component_id: Component type ID
            props: Properties to pass to the component
            context: Template context
        
        Returns:
            Rendered HTML string, or error message if component not found
        """
        instance = self.get_instance(component_id)
        if not instance:
            logger.warning(f"Component not found: {component_id}")
            return f"<!-- Component '{component_id}' not found -->"
        
        try:
            return instance.render(props, context)
        except Exception as e:
            logger.exception(f"Error rendering component {component_id}: {e}")
            return f"<!-- Error rendering '{component_id}': {e} -->"
    
    async def render_async(self, component_id: str, props: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Render a component asynchronously.
        
        For components that need to fetch data, this method calls render_async.
        For sync components, falls back to the sync render method.
        """
        instance = self.get_instance(component_id)
        if not instance:
            logger.warning(f"Component not found: {component_id}")
            return f"<!-- Component '{component_id}' not found -->"
        
        try:
            if hasattr(instance, 'is_async') and instance.is_async:
                return await instance.render_async(props, context)
            return instance.render(props, context)
        except Exception as e:
            logger.exception(f"Error rendering component {component_id}: {e}")
            return f"<!-- Error rendering '{component_id}': {e} -->"

    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all components from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('component:')
        ]
        
        for key in to_remove:
            component_id = key.replace('component:', '')
            if component_id in self._components:
                del self._components[component_id]
                self._instances.pop(component_id, None)
                del self._component_owners[key]
                count += 1
        
        return count

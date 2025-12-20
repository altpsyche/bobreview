"""
Component Registry for Property Controls.

This module provides the component registration system that allows
plugins to register their components with schemas.

Example:
    from bobreview.core.components import register_component, PropTypes
    
    @register_component("chart")
    class ChartComponent:
        props = {
            "id": PropTypes.string(required=True),
            "chart": PropTypes.choice(["bar", "line", "pie"]),
        }
        template = "components/chart.html.j2"
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, Callable
import logging

from .prop_types import PropDef

logger = logging.getLogger(__name__)


@dataclass
class ComponentDefinition:
    """
    Registered component definition.
    
    Attributes:
        type_name: The component type name (e.g., "chart", "widget")
        component_class: The component class
        props: Property schema dict
        template: Optional component-specific template path
        plugin: Plugin that registered this component
    """
    type_name: str
    component_class: Type
    props: Dict[str, PropDef]
    template: Optional[str] = None
    plugin: Optional[str] = None
    
    @property
    def description(self) -> str:
        """Get component description from docstring."""
        return self.component_class.__doc__ or ""


class ComponentRegistry:
    """
    Central registry for all component types.
    
    Components are registered by plugins and looked up during
    YAML processing to validate props and get templates.
    """
    
    _instance: Optional['ComponentRegistry'] = None
    
    def __init__(self):
        self._components: Dict[str, ComponentDefinition] = {}
        self._pending_registrations: list = []
    
    @classmethod
    def get_instance(cls) -> 'ComponentRegistry':
        """Get the singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the registry (useful for testing)."""
        cls._instance = None
    
    def register(
        self,
        type_name: str,
        component_class: Type,
        plugin: Optional[str] = None
    ) -> None:
        """
        Register a component type.
        
        Parameters:
            type_name: Unique identifier for this component type
            component_class: The component class with props and optional template
            plugin: Name of the plugin registering this component
            
        Raises:
            ValueError: If component type is already registered
        """
        if type_name in self._components:
            existing = self._components[type_name]
            logger.warning(
                f"Component '{type_name}' already registered by {existing.plugin}. "
                f"Overwriting with registration from {plugin}."
            )
        
        # Extract props schema from class
        props = getattr(component_class, 'props', {})
        template = getattr(component_class, 'template', None)
        
        self._components[type_name] = ComponentDefinition(
            type_name=type_name,
            component_class=component_class,
            props=props,
            template=template,
            plugin=plugin
        )
        
        logger.debug(f"Registered component '{type_name}' from plugin '{plugin}'")
    
    def get(self, type_name: str) -> Optional[ComponentDefinition]:
        """
        Get a component definition by type name.
        
        Parameters:
            type_name: The component type to look up
            
        Returns:
            ComponentDefinition if found, None otherwise
        """
        return self._components.get(type_name)
    
    def has(self, type_name: str) -> bool:
        """Check if a component type is registered."""
        return type_name in self._components
    
    def list_components(self) -> Dict[str, ComponentDefinition]:
        """Get all registered components."""
        return dict(self._components)
    
    def list_by_plugin(self, plugin: str) -> Dict[str, ComponentDefinition]:
        """Get all components registered by a specific plugin."""
        return {
            name: defn for name, defn in self._components.items()
            if defn.plugin == plugin
        }
    
    def unregister_plugin(self, plugin: str) -> None:
        """Remove all components registered by a plugin."""
        to_remove = [
            name for name, defn in self._components.items()
            if defn.plugin == plugin
        ]
        for name in to_remove:
            del self._components[name]
            logger.debug(f"Unregistered component '{name}' from plugin '{plugin}'")


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry."""
    return ComponentRegistry.get_instance()


def register_component(
    type_name: str,
    plugin: Optional[str] = None
) -> Callable[[Type], Type]:
    """
    Decorator to register a component class.
    
    Usage:
        @register_component("chart")
        class ChartComponent:
            props = {
                "id": PropTypes.string(required=True),
            }
    
    Parameters:
        type_name: Unique identifier for this component type
        plugin: Optional plugin name (auto-detected if not provided)
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type) -> Type:
        registry = get_component_registry()
        
        # Try to detect plugin from module name
        detected_plugin = plugin
        if detected_plugin is None:
            module = getattr(cls, '__module__', '')
            if 'plugins.' in module:
                # Extract plugin name from module path
                parts = module.split('plugins.')
                if len(parts) > 1:
                    detected_plugin = parts[1].split('.')[0]
        
        registry.register(type_name, cls, detected_plugin)
        return cls
    
    return decorator

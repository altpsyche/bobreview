"""
Widget registry for managing UI widgets.
"""

from typing import Dict, Type, Optional, List
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class WidgetRegistry(BaseRegistry):
    """
    Registry for UI widgets.
    
    Single Responsibility: Widget registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the widget registry."""
        super().__init__()
        self._widgets: Dict[str, Type] = {}
    
    def register(self, widget_id: str, widget_cls: Type, plugin_name: str = "") -> None:
        """
        Register a widget class.
        
        Parameters:
            widget_id: Unique identifier for the widget
            widget_cls: Widget implementation class
            plugin_name: Name of the plugin registering this widget
        """
        if widget_id in self._widgets:
            logger.warning(f"Overwriting existing widget type: {widget_id}")
        
        self._widgets[widget_id] = widget_cls
        self._register_component(f"widget:{widget_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered widget: {widget_id} from {plugin_name or 'core'}")
    
    def get(self, widget_type: str) -> Optional[Type]:
        """Get a widget class by type."""
        return self._widgets.get(widget_type)
    
    def get_all(self) -> Dict[str, Type]:
        """Get all registered widgets."""
        return dict(self._widgets)
    
    def get_types(self) -> List[str]:
        """Get list of all registered widget types."""
        return list(self._widgets.keys())
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all widgets from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('widget:')
        ]
        
        for key in to_remove:
            widget_type = key.split(':', 1)[1]
            if widget_type in self._widgets:
                del self._widgets[widget_type]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} widgets from plugin: {plugin_name}")
        return count


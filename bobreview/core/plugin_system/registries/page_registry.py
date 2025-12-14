"""
Page registry for managing page definitions.
"""

from typing import Dict, Any, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class PageRegistry(BaseRegistry):
    """
    Registry for page definitions.
    
    Single Responsibility: Page registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the page registry."""
        super().__init__()
        self._pages: Dict[str, Any] = {}
    
    def register(self, page_id: str, page_def: Any, plugin_name: str = "") -> None:
        """
        Register a page definition.
        
        Parameters:
            page_id: Unique identifier for the page
            page_def: Page definition (dict or object with attributes)
            plugin_name: Name of the plugin registering this page
        """
        if page_id in self._pages:
            logger.warning(f"Overwriting existing page: {page_id}")
        
        self._pages[page_id] = page_def
        self._register_component(f"page:{page_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered page: {page_id} from {plugin_name or 'core'}")
    
    def get(self, page_id: str) -> Optional[Any]:
        """Get a page definition by ID."""
        return self._pages.get(page_id)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered pages."""
        return dict(self._pages)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all pages from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('page:')
        ]
        
        for key in to_remove:
            page_id = key.split(':', 1)[1]
            if page_id in self._pages:
                del self._pages[page_id]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} pages from plugin: {plugin_name}")
        return count


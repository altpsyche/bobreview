"""
Theme registry for managing report themes.
"""

from typing import Dict, Any, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class ThemeRegistry(BaseRegistry):
    """
    Registry for report themes.
    
    Single Responsibility: Theme registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the theme registry."""
        super().__init__()
        self._themes: Dict[str, Any] = {}
    
    def register(self, theme: Any, plugin_name: str = "") -> None:
        """
        Register a theme.
        
        Parameters:
            theme: Theme instance with `id` or `name` attribute
            plugin_name: Name of the plugin registering this theme
        """
        theme_id = getattr(theme, 'id', getattr(theme, 'name', str(theme)))
        
        if theme_id in self._themes:
            logger.warning(f"Overwriting existing theme: {theme_id}")
        
        self._themes[theme_id] = theme
        self._register_component(f"theme:{theme_id}", plugin_name, overwrite=True)
        logger.debug(f"Registered theme: {theme_id} from {plugin_name or 'core'}")
    
    def get(self, theme_id: Optional[str] = None) -> Optional[Any]:
        """
        Get a theme by ID.
        
        Parameters:
            theme_id: Theme ID (e.g., 'dark', 'light'). If None, returns first available theme.
        
        Returns:
            Theme object or None if not found
        """
        if theme_id is None:
            if self._themes:
                return next(iter(self._themes.values()))
            return None
        
        # Try direct lookup by ID
        theme = self._themes.get(theme_id)
        if theme:
            return theme
        
        # Try lookup by theme.id attribute
        for theme in self._themes.values():
            if hasattr(theme, 'id') and theme.id == theme_id:
                return theme
        
        return None
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered themes."""
        return dict(self._themes)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all themes from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('theme:')
        ]
        
        for key in to_remove:
            theme_id = key.split(':', 1)[1]
            if theme_id in self._themes:
                del self._themes[theme_id]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} themes from plugin: {plugin_name}")
        return count


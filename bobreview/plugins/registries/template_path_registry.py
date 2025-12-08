"""
Template path registry for managing template directory paths.
"""

from typing import List, Any, Optional
from pathlib import Path
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class TemplatePathRegistry(BaseRegistry):
    """
    Registry for template directory paths.
    
    Single Responsibility: Template path registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the template path registry."""
        super().__init__()
        self._template_paths: List[tuple] = []  # [(path, plugin_name, priority), ...]
    
    def register(
        self,
        path: Any,  # Path or str
        plugin_name: str = "",
        priority: int = 100
    ) -> None:
        """
        Register a template directory path.
        
        Templates from registered paths are loaded in priority order
        (lower numbers = higher priority).
        
        Parameters:
            path: Path to template directory
            plugin_name: Name of the plugin registering this path
            priority: Loading priority (default 100, game-review plugin uses 1000)
        """
        path = Path(path)
        
        if not path.exists():
            logger.warning(f"Template path does not exist: {path}")
            return
        
        self._template_paths.append((path, plugin_name, priority))
        # Keep sorted by priority (lower = higher priority)
        self._template_paths.sort(key=lambda x: x[2])
        self._register_component(f"template_path:{path}", plugin_name, overwrite=True)
        logger.debug(f"Registered template path: {path} from {plugin_name or 'core'}")
    
    def get_paths(self) -> List[Path]:
        """
        Get all registered template paths in priority order.
        
        Returns:
            List of Path objects
        """
        return [path for path, _, _ in self._template_paths]
    
    def get_all_registrations(self) -> List[tuple]:
        """Get all template path registrations with metadata."""
        return list(self._template_paths)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all template paths from a specific plugin."""
        count = 0
        to_remove = [
            (path, pname, priority)
            for path, pname, priority in self._template_paths
            if pname == plugin_name
        ]
        
        for path, _, priority in to_remove:
            self._template_paths.remove((path, plugin_name, priority))
            del self._component_owners[f"template_path:{path}"]
            count += 1
        
        logger.info(f"Unregistered {count} template paths from plugin: {plugin_name}")
        return count


"""
Data parser registry for managing data parsers.
"""

from typing import Dict, Type, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class DataParserRegistry(BaseRegistry):
    """
    Registry for data parsers.
    
    Single Responsibility: Data parser registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the data parser registry."""
        super().__init__()
        self._parsers: Dict[str, Type] = {}
    
    def register(self, parser_cls: Type, plugin_name: str = "") -> None:
        """
        Register a data parser class.
        
        Parameters:
            parser_cls: Parser class with `parser_name` attribute
            plugin_name: Name of the plugin registering this parser
        """
        parser_name = getattr(parser_cls, 'parser_name', parser_cls.__name__)
        
        if parser_name in self._parsers:
            logger.warning(f"Overwriting existing parser: {parser_name}")
        
        self._parsers[parser_name] = parser_cls
        self._register_component(f"parser:{parser_name}", plugin_name, overwrite=True)
        logger.debug(f"Registered parser: {parser_name} from {plugin_name or 'core'}")
    
    def get(self, parser_name: str) -> Optional[Type]:
        """Get a data parser class by name."""
        return self._parsers.get(parser_name)
    
    def get_all(self) -> Dict[str, Type]:
        """Get all registered data parsers."""
        return dict(self._parsers)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all parsers from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('parser:')
        ]
        
        for key in to_remove:
            parser_name = key.split(':', 1)[1]
            if parser_name in self._parsers:
                del self._parsers[parser_name]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} parsers from plugin: {plugin_name}")
        return count


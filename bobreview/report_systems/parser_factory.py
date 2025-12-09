"""
Parser factory for creating parser instances from configuration.

Provides a clean interface for instantiating parsers based on
data source type, using the plugin registry.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Type, Union
import logging

from .schema import DataSourceConfig
from .data_parser_base import DataParser
from ..core.api import DataParserInterface
from ..core.plugin_system import get_extension_point

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory for creating DataParser instances.
    
    Uses the plugin registry to find parser classes by type.
    Falls back to built-in parsers if not found in registry.
    """
    
    def __init__(self, extension_point=None):
        """
        Initialize parser factory.
        
        Parameters:
            extension_point: IExtensionPoint instance (optional, uses global if None)
        """
        self._extension_point = extension_point  # Will use global if None
        self._builtin_parsers: Dict[str, Type[DataParser]] = {}
        self._register_builtin_parsers()
    
    @property
    def extension_point(self):
        """Get extension point, using global if not injected."""
        if self._extension_point is None:
            self._extension_point = get_extension_point()
        return self._extension_point
    
    def _register_builtin_parsers(self) -> None:
        """Register built-in parser types."""
        from .data_parser_base import FilenamePatternParser
        self._builtin_parsers['filename_pattern'] = FilenamePatternParser
    
    def create(self, config: DataSourceConfig) -> DataParserInterface:
        """
        Create a parser instance from configuration.
        
        Parameters:
            config: DataSourceConfig with type and settings
        
        Returns:
            DataParser instance
        
        Raises:
            ValueError: If parser type is not found
        """
        parser_type = config.type
        
        # Try plugin extension point first
        parser_cls = self.extension_point.get_data_parser(parser_type)
        
        # Fall back to built-in parsers
        if parser_cls is None:
            parser_cls = self._builtin_parsers.get(parser_type)
        
        if parser_cls is None:
            available = list(self._builtin_parsers.keys())
            try:
                available.extend(self.extension_point.get_all_parsers().keys())
            except Exception:
                pass  # Ignore errors getting plugin parsers
            raise ValueError(
                f"Unknown parser type: {parser_type}. "
                f"Available types: {', '.join(sorted(set(available)))}"
            )
        
        # Extract parser_class from wrapper if needed
        if hasattr(parser_cls, 'parser_class'):
            parser_cls = parser_cls.parser_class
        
        # Instantiate parser
        try:
            return parser_cls(config)
        except Exception as e:
            raise ValueError(f"Failed to create parser {parser_type}: {e}") from e
    
    def get_available_types(self) -> list[str]:
        """Get list of available parser types."""
        types = set(self._builtin_parsers.keys())
        try:
            types.update(self.extension_point.get_all_parsers().keys())
        except Exception:
            pass  # Ignore errors getting plugin parsers
        return sorted(types)


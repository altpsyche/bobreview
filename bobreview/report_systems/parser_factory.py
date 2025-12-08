"""
Parser factory for creating parser instances from configuration.

Provides a clean interface for instantiating parsers based on
data source type, using the plugin registry.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Type
import logging

from .schema import DataSourceConfig
from .data_parser_base import DataParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory for creating DataParser instances.
    
    Uses the plugin registry to find parser classes by type.
    Falls back to built-in parsers if not found in registry.
    """
    
    def __init__(self, registry=None):
        """
        Initialize parser factory.
        
        Parameters:
            registry: PluginRegistry instance (optional, uses lazy import if None)
        """
        self.registry = registry  # Will be lazily loaded if needed
        self._builtin_parsers: Dict[str, Type[DataParser]] = {}
        self._register_builtin_parsers()
    
    def _get_registry(self):
        """Lazily get registry to avoid import errors if plugins aren't available."""
        if self.registry is None:
            try:
                from ..plugins import get_registry
                self.registry = get_registry()
            except ImportError:
                # Plugins not available - factory will only use built-in parsers
                self.registry = None
        return self.registry
    
    def _register_builtin_parsers(self) -> None:
        """Register built-in parser types."""
        from .data_parser_base import FilenamePatternParser
        self._builtin_parsers['filename_pattern'] = FilenamePatternParser
    
    def create(self, config: DataSourceConfig) -> DataParser:
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
        
        # Try plugin registry first (if available)
        parser_cls = None
        registry = self._get_registry()
        if registry:
            parser_cls = registry.data_parsers.get(parser_type)
        
        # Fall back to built-in parsers
        if parser_cls is None:
            parser_cls = self._builtin_parsers.get(parser_type)
        
        if parser_cls is None:
            available = list(self._builtin_parsers.keys())
            if registry:
                try:
                    available.extend(registry.data_parsers.get_all().keys())
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
        registry = self._get_registry()
        if registry:
            try:
                types.update(registry.data_parsers.get_all().keys())
            except Exception:
                pass  # Ignore errors getting plugin parsers
        return sorted(types)


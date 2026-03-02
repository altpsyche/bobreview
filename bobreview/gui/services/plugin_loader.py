"""
Plugin Loader - Centralized plugin module loading with caching.

Provides a single point for loading plugin modules (executor, theme) with:
- Proper handling of relative imports
- Module caching to avoid repeated imports
- Clean API for accessing plugin attributes
"""

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Any
from types import ModuleType


class PluginLoader:
    """
    Centralized plugin module loader with caching.

    Use this class instead of direct importlib calls to:
    - Avoid code duplication
    - Enable module caching
    - Handle relative imports properly
    """

    # Module cache: {plugin_name: {module_type: module}}
    _cache: ClassVar[Dict[str, Dict[str, ModuleType]]] = {}

    # Plugin path cache: {plugin_name: Path}
    _path_cache: ClassVar[Dict[str, Path]] = {}
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached modules and sys.modules entries for hot-reload."""
        # Remove stale sys.modules entries for cached plugins so Python
        # reimports fresh code on the next load.
        for plugin_name in list(cls._cache):
            safe_name = plugin_name.replace('-', '_')
            stale_prefixes = (safe_name + '.', f'bobreview.plugins.{safe_name}.')
            stale_keys = [
                key for key in list(sys.modules)
                if key == safe_name
                or key == f'bobreview.plugins.{safe_name}'
                or key.startswith(stale_prefixes)
            ]
            for key in stale_keys:
                del sys.modules[key]
        cls._cache.clear()
        cls._path_cache.clear()
    
    @classmethod
    def _get_plugin_dir(cls, plugin_name: str) -> Optional[Path]:
        """Get plugin directory path, with caching."""
        if plugin_name in cls._path_cache:
            return cls._path_cache[plugin_name]

        # Import here to avoid circular imports.
        # Use get_loader() to reuse the existing global loader instead of
        # init_loader() which replaces it on every call.
        from bobreview.core.plugin_system import get_loader

        loader = get_loader()
        # Discover only if not already discovered
        if not loader.get_discovered_plugins():
            loader.discover()
        plugins = loader.get_discovered_plugins()
        
        plugin = next((p for p in plugins if p.name == plugin_name), None)
        
        if plugin and plugin.path:
            plugin_dir = Path(plugin.path)
            if plugin_dir.is_file():
                plugin_dir = plugin_dir.parent
            cls._path_cache[plugin_name] = plugin_dir
            return plugin_dir
        
        return None
    
    @classmethod
    def _import_module(cls, plugin_name: str, module_name: str) -> Optional[ModuleType]:
        """
        Import a module from a plugin using spec_from_file_location.

        Uses importlib.util.spec_from_file_location directly instead of
        manipulating sys.path, which avoids interference with the core
        loader's persistent sys.path entries.

        Args:
            plugin_name: Name of the plugin
            module_name: Name of module to import (e.g., 'executor', 'theme')

        Returns:
            Imported module or None if not found
        """
        # Check cache first
        if plugin_name in cls._cache and module_name in cls._cache[plugin_name]:
            return cls._cache[plugin_name][module_name]

        plugin_dir = cls._get_plugin_dir(plugin_name)
        if not plugin_dir:
            return None

        module_path = plugin_dir / f'{module_name}.py'
        if not module_path.exists():
            return None

        try:
            safe_name = plugin_name.replace('-', '_')
            full_module_name = f"{safe_name}.{module_name}"

            # Ensure the package is registered so relative imports work
            if safe_name not in sys.modules:
                init_path = plugin_dir / "__init__.py"
                if init_path.exists():
                    pkg_spec = importlib.util.spec_from_file_location(
                        safe_name, init_path,
                        submodule_search_locations=[str(plugin_dir)],
                    )
                    if pkg_spec and pkg_spec.loader:
                        pkg_mod = importlib.util.module_from_spec(pkg_spec)
                        pkg_mod.__path__ = [str(plugin_dir)]
                        pkg_mod.__package__ = safe_name
                        sys.modules[safe_name] = pkg_mod
                        pkg_spec.loader.exec_module(pkg_mod)

            spec = importlib.util.spec_from_file_location(
                full_module_name, module_path,
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                module.__package__ = safe_name
                sys.modules[full_module_name] = module
                spec.loader.exec_module(module)

                # Cache the module
                if plugin_name not in cls._cache:
                    cls._cache[plugin_name] = {}
                cls._cache[plugin_name][module_name] = module
                return module
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to import %s from plugin %s: %s", module_name, plugin_name, e
            )

        return None
    
    @classmethod
    def get_executor(cls, plugin_name: str) -> Optional[ModuleType]:
        """Get the executor module for a plugin."""
        return cls._import_module(plugin_name, 'executor')
    
    @classmethod
    def get_theme_module(cls, plugin_name: str) -> Optional[ModuleType]:
        """Get the theme module for a plugin."""
        return cls._import_module(plugin_name, 'theme')
    
    @classmethod
    def get_components(cls, plugin_name: str) -> List[dict]:
        """
        Get COMPONENT_TYPES from plugin's executor.
        
        Returns empty list if not defined.
        """
        executor = cls.get_executor(plugin_name)
        if executor and hasattr(executor, 'COMPONENT_TYPES'):
            return executor.COMPONENT_TYPES
        return []
    
    @classmethod
    def get_data_fields(cls, plugin_name: str) -> List[str]:
        """
        Get DATA_FIELDS from plugin's executor.
        
        Returns empty list if not defined.
        """
        executor = cls.get_executor(plugin_name)
        if executor and hasattr(executor, 'DATA_FIELDS'):
            return executor.DATA_FIELDS
        return []
    
    @classmethod
    def get_themes(cls, plugin_name: str) -> List[str]:
        """
        Get THEME_NAMES from plugin's theme module.
        
        Returns empty list if not defined.
        """
        theme_module = cls.get_theme_module(plugin_name)
        if theme_module and hasattr(theme_module, 'THEME_NAMES'):
            return theme_module.THEME_NAMES
        return []
    
    @classmethod
    def get_attribute(cls, plugin_name: str, module: str, attribute: str, default: Any = None) -> Any:
        """
        Generic method to get any attribute from a plugin module.
        
        Args:
            plugin_name: Name of the plugin
            module: Module name ('executor', 'theme', etc.)
            attribute: Attribute name to get
            default: Default value if not found
        """
        mod = cls._import_module(plugin_name, module)
        if mod and hasattr(mod, attribute):
            return getattr(mod, attribute)
        return default

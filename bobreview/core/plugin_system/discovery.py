"""
Plugin discovery system for BobReview.

Provides configurable plugin path discovery without hardcoded paths.
Plugins can be loaded from multiple sources in priority order.
"""

import os
from importlib.resources import files
from pathlib import Path
from typing import List, Optional


# Package resources - loaded at module level (no lazy imports)
_BOBREVIEW_PKG = files('bobreview')


class PluginDiscovery:
    """
    Configurable plugin path discovery.
    
    Discovers plugins from multiple sources in priority order:
    1. CLI/extra dirs (highest priority)
    2. Environment variable BOBREVIEW_PLUGIN_DIRS
    3. User plugins ~/.bobreview/plugins/
    4. Local plugins ./plugins/
    5. Bundled plugins (shipped with package)
    """
    
    @staticmethod
    def get_bundled_plugins_dir() -> Optional[Path]:
        """
        Get bundled plugins directory (shipped with package).
        
        Returns:
            Path to bundled plugins directory, or None if not found
        """
        bundled = _BOBREVIEW_PKG / 'plugins'
        # Convert Traversable to Path if it exists
        try:
            # For importlib.resources, we need to check if the path exists
            bundled_path = Path(str(bundled))
            if bundled_path.is_dir():
                return bundled_path
        except (TypeError, ValueError):
            pass
        return None
    
    @staticmethod
    def get_user_plugins_dir() -> Path:
        """Get user plugins directory (~/.bobreview/plugins/)."""
        return Path.home() / '.bobreview' / 'plugins'
    
    @staticmethod
    def get_local_plugins_dir() -> Path:
        """Get local plugins directory (./plugins/)."""
        return Path.cwd() / 'plugins'
    
    @staticmethod
    def get_env_plugin_dirs() -> List[Path]:
        """
        Get plugin directories from environment variable.
        
        Reads BOBREVIEW_PLUGIN_DIRS environment variable.
        Paths are separated by os.pathsep (: on Unix, ; on Windows).
        
        Returns:
            List of paths from environment variable
        """
        env_dirs = os.environ.get('BOBREVIEW_PLUGIN_DIRS', '')
        if not env_dirs:
            return []
        return [Path(d).expanduser().resolve() for d in env_dirs.split(os.pathsep) if d]
    
    @staticmethod
    def get_plugin_dirs(
        extra_dirs: Optional[List[str]] = None,
        include_bundled: bool = True
    ) -> List[Path]:
        """
        Get all plugin directories in priority order.
        
        Priority order (first wins for conflicts):
        1. extra_dirs (CLI --plugin-dirs)
        2. BOBREVIEW_PLUGIN_DIRS environment variable
        3. ~/.bobreview/plugins/ (user plugins)
        4. ./plugins/ (local plugins)
        5. Bundled plugins (package data)
        
        Parameters:
            extra_dirs: Additional directories from CLI
            include_bundled: Whether to include bundled plugins
        
        Returns:
            List of existing plugin directories
        """
        dirs: List[Path] = []
        seen: set = set()
        
        def add_dir(path: Path) -> None:
            """Add directory if it exists and not already added."""
            resolved = path.expanduser().resolve()
            if resolved not in seen and resolved.exists() and resolved.is_dir():
                dirs.append(resolved)
                seen.add(resolved)
        
        # 1. CLI/extra dirs (highest priority)
        if extra_dirs:
            for d in extra_dirs:
                add_dir(Path(d))
        
        # 2. Environment variable
        for d in PluginDiscovery.get_env_plugin_dirs():
            add_dir(d)
        
        # 3. User plugins
        add_dir(PluginDiscovery.get_user_plugins_dir())
        
        # 4. Local plugins
        add_dir(PluginDiscovery.get_local_plugins_dir())
        
        # 5. Bundled plugins
        if include_bundled:
            bundled = PluginDiscovery.get_bundled_plugins_dir()
            if bundled:
                add_dir(bundled)
        
        return dirs

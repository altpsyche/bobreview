"""
Plugin loader for discovering and loading plugins.

The loader handles:
- Discovery of plugins from configured directories
- Loading plugins by importing their entry points
- Dependency resolution
- Hot reload for development
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
import importlib
import importlib.util
import logging
import sys
import threading

from .base import BasePlugin, PluginInfo
from .manifest import PluginManifest, validate_manifest
from .registry import PluginRegistry, get_registry

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin fails to load."""
    pass


class PluginDependencyError(Exception):
    """Raised when plugin dependencies cannot be resolved."""
    pass


class PluginLoader:
    """
    Discovers and loads plugins from configured directories.
    
    Plugins are Python packages with a manifest.json file that describes
    the plugin and specifies the entry point class.
    
    Example:
        loader = PluginLoader([Path("~/.bobreview/plugins")])
        
        # Discover available plugins
        manifests = loader.discover()
        
        # Load a specific plugin
        plugin = loader.load("my-plugin")
        
        # Load all enabled plugins
        loader.load_all_enabled(enabled=["my-plugin", "other-plugin"])
    """
    
    def __init__(
        self,
        plugin_dirs: Optional[List[Path]] = None,
        registry: Optional[PluginRegistry] = None
    ):
        """
        Initialize the plugin loader.
        
        Parameters:
            plugin_dirs: List of directories to search for plugins
                         (defaults to PluginDiscovery.get_plugin_dirs())
            registry: Plugin registry to use (defaults to global registry)
        """
        # Import here to avoid circular imports
        from .discovery import PluginDiscovery
        
        self.plugin_dirs = plugin_dirs if plugin_dirs is not None else PluginDiscovery.get_plugin_dirs()
        self.registry = registry or get_registry()
        
        # Loaded plugins: name -> plugin instance
        self._loaded: Dict[str, BasePlugin] = {}

        # Discovered manifests: name -> manifest
        self._manifests: Dict[str, PluginManifest] = {}

        # Track load order for proper unloading
        self._load_order: List[str] = []

        # Track sys.path entries added per plugin so they can be
        # removed on unload, preventing long-lived path pollution.
        self._added_sys_paths: Dict[str, List[str]] = {}  # plugin_name -> [paths]
    
    def add_plugin_dir(self, directory: Path) -> None:
        """Add a directory to search for plugins."""
        directory = Path(directory).expanduser().resolve()
        if directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.debug(f"Added plugin directory: {directory}")
    
    def discover(self) -> List[PluginManifest]:
        """
        Discover all plugins in configured directories.
        
        Scans plugin directories for subdirectories containing manifest.json.
        
        Returns:
            List of discovered plugin manifests
        """
        self._manifests.clear()
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            plugin_dir = Path(plugin_dir).expanduser().resolve()
            
            if not plugin_dir.exists():
                logger.debug(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            if not plugin_dir.is_dir():
                logger.warning(f"Plugin path is not a directory: {plugin_dir}")
                continue
            
            # Look for subdirectories with manifest.json
            for item in plugin_dir.iterdir():
                if not item.is_dir():
                    continue
                
                manifest_path = item / "manifest.json"
                if not manifest_path.exists():
                    continue
                
                try:
                    manifest = PluginManifest.from_file(manifest_path)
                    
                    # Validate manifest
                    issues = validate_manifest(manifest)
                    if issues:
                        logger.warning(
                            f"Plugin '{manifest.name}' has manifest issues: {issues}"
                        )
                    
                    self._manifests[manifest.name] = manifest
                    discovered.append(manifest)
                    logger.debug(f"Discovered plugin: {manifest.name} at {item}")
                    
                except Exception as e:
                    logger.error(f"Failed to load manifest from {manifest_path}: {e}")
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    def get_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """Get the manifest for a discovered plugin."""
        return self._manifests.get(plugin_name)
    
    def is_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is currently loaded."""
        return plugin_name in self._loaded
    
    def get_loaded_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a loaded plugin by name."""
        return self._loaded.get(plugin_name)
    
    def load(self, plugin_name: str, resolve_deps: bool = True) -> BasePlugin:
        """
        Load a plugin by name.
        
        Parameters:
            plugin_name: Name of the plugin to load
            resolve_deps: Whether to load dependencies first
            
        Returns:
            Loaded plugin instance
            
        Raises:
            PluginLoadError: If the plugin cannot be loaded
            PluginDependencyError: If dependencies cannot be resolved
        """
        # Check if already loaded
        if plugin_name in self._loaded:
            logger.debug(f"Plugin already loaded: {plugin_name}")
            return self._loaded[plugin_name]
        
        # Get manifest
        manifest = self._manifests.get(plugin_name)
        if not manifest:
            raise PluginLoadError(
                f"Plugin not found: {plugin_name}. "
                f"Run discover() first or check plugin directories."
            )
        
        # Resolve dependencies first
        if resolve_deps and manifest.dependencies:
            self._resolve_dependencies(plugin_name, manifest.dependencies)
        
        # Load the plugin
        try:
            plugin = self._load_plugin(manifest)
            
            # Call on_load
            plugin.on_load(self.registry)
            
            # Track as loaded
            self._loaded[plugin_name] = plugin
            self._load_order.append(plugin_name)
            
            logger.info(f"Loaded plugin: {plugin_name} v{manifest.version}")
            return plugin
            
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin '{plugin_name}': {e}") from e
    
    def _resolve_dependencies(
        self,
        plugin_name: str,
        dependencies: List[str],
        loading: Optional[Set[str]] = None
    ) -> None:
        """
        Resolve and load plugin dependencies.
        
        Parameters:
            plugin_name: Plugin that has dependencies
            dependencies: List of dependency plugin names
            loading: Set of plugins currently being loaded (for cycle detection)
        """
        if loading is None:
            loading = set()
        
        if plugin_name in loading:
            raise PluginDependencyError(
                f"Circular dependency detected: {plugin_name}"
            )
        
        loading.add(plugin_name)
        
        for dep_name in dependencies:
            if dep_name in self._loaded:
                continue
            
            if dep_name not in self._manifests:
                raise PluginDependencyError(
                    f"Plugin '{plugin_name}' depends on '{dep_name}' which was not found"
                )
            
            dep_manifest = self._manifests[dep_name]
            
            # Recursively resolve dependencies
            if dep_manifest.dependencies:
                self._resolve_dependencies(dep_name, dep_manifest.dependencies, loading)
            
            # Load the dependency
            self.load(dep_name, resolve_deps=False)
        
        loading.remove(plugin_name)
    
    def _load_plugin(self, manifest: PluginManifest) -> BasePlugin:
        """
        Load a plugin from its manifest.
        
        Parameters:
            manifest: Plugin manifest
            
        Returns:
            Plugin instance
        """
        if not manifest.plugin_path:
            raise PluginLoadError(f"Plugin path not set for: {manifest.name}")
        
        module_name, class_name = manifest.get_module_and_class()
        
        # Check if this is a built-in plugin (in bobreview.plugins package)
        # by comparing resolved paths
        from .discovery import PluginDiscovery
        bundled_dir = PluginDiscovery.get_bundled_plugins_dir()
        is_builtin = False
        if bundled_dir:
            try:
                # Check if plugin path is under bundled plugins directory
                manifest_resolved = manifest.plugin_path.resolve()
                bundled_resolved = bundled_dir.resolve()
                is_builtin = bundled_resolved in manifest_resolved.parents or manifest_resolved.parent == bundled_resolved
            except Exception as e:
                logger.debug(f"Could not determine if plugin is builtin: {e}")

        try:
            if is_builtin:
                # Built-in plugins: import from package
                # e.g., bobreview.plugins.<plugin-name>.plugin:PluginClass
                # Extract the subdirectory name
                plugin_dir_name = manifest.plugin_path.name
                
                # Handle hyphens in directory names (Python modules can't have hyphens)
                # Use importlib.util.spec_from_file_location for directories with hyphens
                if '-' in plugin_dir_name:
                    module_path = manifest.plugin_path / f"{module_name}.py"
                    if module_path.exists():
                        # Create a module name with underscores instead of hyphens
                        safe_dir_name = plugin_dir_name.replace('-', '_')
                        package_name = f"bobreview.plugins.{safe_dir_name}"
                        safe_module_name = f"{package_name}.{module_name}"
                        
                        # Register parent package if not already registered
                        if package_name not in sys.modules:
                            package_spec = importlib.util.spec_from_file_location(
                                package_name,
                                manifest.plugin_path / "__init__.py"
                            )
                            if package_spec is not None and package_spec.loader is not None:
                                package_module = importlib.util.module_from_spec(package_spec)
                                sys.modules[package_name] = package_module
                                # Set __path__ so Python knows this is a package
                                package_module.__path__ = [str(manifest.plugin_path)]
                                package_spec.loader.exec_module(package_module)
                        
                        # Also register generators subpackage if it exists
                        generators_dir = manifest.plugin_path / "generators"
                        if generators_dir.exists() and generators_dir.is_dir():
                            generators_package_name = f"{package_name}.generators"
                            if generators_package_name not in sys.modules:
                                generators_init = generators_dir / "__init__.py"
                                if generators_init.exists():
                                    generators_spec = importlib.util.spec_from_file_location(
                                        generators_package_name,
                                        generators_init
                                    )
                                    if generators_spec is not None and generators_spec.loader is not None:
                                        generators_module = importlib.util.module_from_spec(generators_spec)
                                        sys.modules[generators_package_name] = generators_module
                                        generators_module.__path__ = [str(generators_dir)]
                                        generators_module.__package__ = generators_package_name
                                        generators_spec.loader.exec_module(generators_module)
                        
                        spec = importlib.util.spec_from_file_location(
                            safe_module_name,
                            module_path
                        )
                        if spec is None or spec.loader is None:
                            raise ImportError(f"Cannot create spec for: {module_path}")
                        
                        module = importlib.util.module_from_spec(spec)
                        # Set __package__ so relative imports work
                        module.__package__ = package_name
                        # Register in sys.modules so relative imports work
                        sys.modules[safe_module_name] = module
                        spec.loader.exec_module(module)
                    else:
                        raise ImportError(f"Module file not found: {module_path}")
                else:
                    package_module = f"bobreview.plugins.{plugin_dir_name}.{module_name}"
                    module = importlib.import_module(package_module)
            else:
                # External plugins: load from file system
                # Need to set up package structure for relative imports
                plugin_dir = manifest.plugin_path
                safe_name = manifest.name.replace('-', '_')
                
                # Add parent directory to path if needed and track it
                # so it can be cleaned up on unload.
                parent_dir = str(plugin_dir.parent)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                    paths_added = self._added_sys_paths.setdefault(manifest.name, [])
                    paths_added.append(parent_dir)
                
                # Register the plugin as a package in sys.modules
                package_name = safe_name
                if package_name not in sys.modules:
                    init_path = plugin_dir / "__init__.py"
                    if init_path.exists():
                        pkg_spec = importlib.util.spec_from_file_location(
                            package_name,
                            init_path,
                            submodule_search_locations=[str(plugin_dir)]
                        )
                        if pkg_spec and pkg_spec.loader:
                            pkg_module = importlib.util.module_from_spec(pkg_spec)
                            pkg_module.__path__ = [str(plugin_dir)]
                            pkg_module.__package__ = package_name
                            sys.modules[package_name] = pkg_module
                            pkg_spec.loader.exec_module(pkg_module)
                    else:
                        # Create a dummy package module
                        import types
                        pkg_module = types.ModuleType(package_name)
                        pkg_module.__path__ = [str(plugin_dir)]
                        pkg_module.__package__ = package_name
                        sys.modules[package_name] = pkg_module
                
                # Register subpackages (e.g., parsers/)
                for subdir in plugin_dir.iterdir():
                    if subdir.is_dir() and (subdir / "__init__.py").exists():
                        sub_pkg_name = f"{package_name}.{subdir.name}"
                        if sub_pkg_name not in sys.modules:
                            sub_init = subdir / "__init__.py"
                            sub_spec = importlib.util.spec_from_file_location(
                                sub_pkg_name,
                                sub_init,
                                submodule_search_locations=[str(subdir)]
                            )
                            if sub_spec and sub_spec.loader:
                                sub_module = importlib.util.module_from_spec(sub_spec)
                                sub_module.__path__ = [str(subdir)]
                                sub_module.__package__ = sub_pkg_name
                                sys.modules[sub_pkg_name] = sub_module
                                sub_spec.loader.exec_module(sub_module)
                
                # Now load the plugin module
                module_path = plugin_dir / f"{module_name}.py"
                
                if module_path.exists():
                    full_module_name = f"{package_name}.{module_name}"
                    spec = importlib.util.spec_from_file_location(
                        full_module_name,
                        module_path
                    )
                    if spec is None or spec.loader is None:
                        raise PluginLoadError(f"Cannot load module: {module_path}")
                    
                    module = importlib.util.module_from_spec(spec)
                    module.__package__ = package_name
                    sys.modules[full_module_name] = module
                    spec.loader.exec_module(module)
                else:
                    # Try as a package
                    module = importlib.import_module(module_name)
            
            # Get the plugin class
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Module '{module_name}' has no class '{class_name}'"
                )
            
            plugin_cls = getattr(module, class_name)
            
            # Verify it's a BasePlugin subclass
            if not issubclass(plugin_cls, BasePlugin):
                raise PluginLoadError(
                    f"Class '{class_name}' is not a BasePlugin subclass"
                )
            
            # Instantiate the plugin
            plugin = plugin_cls()
            
            return plugin
            
        except ImportError as e:
            raise PluginLoadError(f"Cannot import plugin module: {e}") from e
    
    def unload(self, plugin_name: str) -> None:
        """
        Unload a plugin.

        Parameters:
            plugin_name: Name of the plugin to unload
        """
        if plugin_name not in self._loaded:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return

        plugin = self._loaded[plugin_name]

        try:
            # Call on_unload
            plugin.on_unload()

            # Unregister all components
            self.registry.unregister_plugin_components(plugin_name)

            # Clean up sys.path entries that were added during load
            for path_entry in self._added_sys_paths.pop(plugin_name, []):
                if path_entry in sys.path:
                    sys.path.remove(path_entry)
                    logger.debug(f"Removed sys.path entry: {path_entry}")

            # Clean up sys.modules entries for this plugin so reload
            # picks up fresh code instead of returning stale cached modules.
            safe_name = plugin_name.replace('-', '_')
            plugin_dir = str(manifest.plugin_path.resolve()) if manifest.plugin_path else None
            stale_prefixes = (safe_name + '.', f'bobreview.plugins.{safe_name}.')
            stale_keys = [
                key for key in list(sys.modules)
                if key == safe_name
                or key == f'bobreview.plugins.{safe_name}'
                or key.startswith(stale_prefixes)
            ]
            for key in stale_keys:
                mod = sys.modules.get(key)
                # Verify module ownership: only remove modules that belong
                # to this plugin (have a __file__ under the plugin directory)
                # or have no __file__ (namespace packages created during load).
                mod_file = getattr(mod, '__file__', None)
                if mod_file and plugin_dir:
                    try:
                        resolved_mod = str(Path(mod_file).resolve())
                        if not resolved_mod.startswith(plugin_dir):
                            logger.debug(f"Skipping sys.modules entry {key}: outside plugin dir")
                            continue
                    except (ValueError, OSError):
                        continue
                del sys.modules[key]
                logger.debug(f"Removed sys.modules entry: {key}")

            # Remove from loaded
            del self._loaded[plugin_name]
            if plugin_name in self._load_order:
                self._load_order.remove(plugin_name)

            # Clear engine caches that may reference this plugin's report
            # systems or templates.
            try:
                from ...engine.loader import clear_cache as clear_engine_cache
                clear_engine_cache()
            except Exception as e:
                logger.debug("Failed to clear engine cache: %s", e, exc_info=True)

            logger.info(f"Unloaded plugin: {plugin_name}")
            
        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {e}")
    
    def reload(self, plugin_name: str) -> BasePlugin:
        """
        Reload a plugin (for development).
        
        Parameters:
            plugin_name: Name of the plugin to reload
            
        Returns:
            Reloaded plugin instance
        """
        # Unload first
        if plugin_name in self._loaded:
            self.unload(plugin_name)
        
        # Re-discover to pick up changes
        # (only if manifest might have changed)
        if plugin_name in self._manifests:
            manifest = self._manifests[plugin_name]
            if manifest.plugin_path:
                manifest_path = manifest.plugin_path / "manifest.json"
                if manifest_path.exists():
                    self._manifests[plugin_name] = PluginManifest.from_file(manifest_path)
        
        # Load again
        return self.load(plugin_name)
    
    def load_all_enabled(
        self,
        enabled: Optional[List[str]] = None,
        disabled: Optional[List[str]] = None
    ) -> List[BasePlugin]:
        """
        Load all enabled plugins.

        After loading, the global template engine is refreshed so that
        any template paths registered by the newly loaded plugins are
        picked up immediately.

        Parameters:
            enabled: List of enabled plugin names (None = all discovered)
            disabled: List of disabled plugin names

        Returns:
            List of loaded plugins
        """
        disabled = disabled or []
        loaded = []

        # Determine which plugins to load
        if enabled is not None:
            to_load = [name for name in enabled if name not in disabled]
        else:
            to_load = [name for name in self._manifests if name not in disabled]

        # Load each plugin
        for plugin_name in to_load:
            try:
                plugin = self.load(plugin_name)
                loaded.append(plugin)
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin_name}': {e}")

        # Refresh the template engine so newly registered template paths
        # are visible.  Import lazily to avoid circular dependency.
        if loaded:
            try:
                from ..template_engine import get_template_engine
                # Preserve any previously configured custom template paths
                existing_engine = get_template_engine()
                existing_paths = None
                if hasattr(existing_engine, 'env') and hasattr(existing_engine.env, 'loader'):
                    choice_loader = existing_engine.env.loader
                    if hasattr(choice_loader, 'loaders'):
                        existing_paths = [
                            loader.searchpath[0]
                            for loader in choice_loader.loaders
                            if hasattr(loader, 'searchpath') and loader.searchpath
                        ]
                get_template_engine(force_refresh=True, custom_paths=existing_paths)
            except Exception as e:
                logger.debug(f"Template engine refresh skipped: {e}")

        return loaded
    
    def unload_all(self) -> None:
        """Unload all plugins in reverse load order."""
        for plugin_name in reversed(self._load_order.copy()):
            self.unload(plugin_name)
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """Get information about all loaded plugins."""
        return [
            plugin.get_info(loaded=True)
            for plugin in self._loaded.values()
        ]
    
    def get_discovered_plugins(self) -> List[PluginInfo]:
        """Get information about all discovered plugins."""
        return [
            PluginInfo(
                name=m.name,
                version=m.version,
                author=m.author,
                description=m.description,
                enabled=True,
                loaded=m.name in self._loaded,
                path=str(m.plugin_path) if m.plugin_path else None,
                dependencies=m.dependencies,
                provides=m.provides,
            )
            for m in self._manifests.values()
        ]
    
    def __repr__(self) -> str:
        return f"<PluginLoader: {len(self._loaded)} loaded, {len(self._manifests)} discovered>"


# Global loader instance
_global_loader: Optional[PluginLoader] = None
_loader_lock = threading.Lock()


def get_loader() -> PluginLoader:
    """Get the global plugin loader instance (thread-safe)."""
    global _global_loader
    if _global_loader is None:
        with _loader_lock:
            if _global_loader is None:
                _global_loader = PluginLoader()
    return _global_loader


def init_loader(plugin_dirs: List[Path]) -> PluginLoader:
    """Initialize the global plugin loader with directories."""
    global _global_loader
    with _loader_lock:
        _global_loader = PluginLoader(plugin_dirs)
    return _global_loader

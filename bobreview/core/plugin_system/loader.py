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
            registry: Plugin registry to use (defaults to global registry)
        """
        self.plugin_dirs = plugin_dirs or []
        self.registry = registry or get_registry()
        
        # Loaded plugins: name -> plugin instance
        self._loaded: Dict[str, BasePlugin] = {}
        
        # Discovered manifests: name -> manifest
        self._manifests: Dict[str, PluginManifest] = {}
        
        # Track load order for proper unloading
        self._load_order: List[str] = []
    
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
        plugin_path_str = str(manifest.plugin_path)
        is_builtin = 'bobreview' in plugin_path_str and 'plugins' in plugin_path_str
        
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
                # Add plugin directory to path if needed
                plugin_dir = str(manifest.plugin_path)
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)
                
                # Import the module
                module_path = manifest.plugin_path / f"{module_name}.py"
                
                if module_path.exists():
                    # Load from file
                    spec = importlib.util.spec_from_file_location(
                        f"bobreview_plugins.{manifest.name}.{module_name}",
                        module_path
                    )
                    if spec is None or spec.loader is None:
                        raise PluginLoadError(f"Cannot load module: {module_path}")
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
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
            
            # Remove from loaded
            del self._loaded[plugin_name]
            if plugin_name in self._load_order:
                self._load_order.remove(plugin_name)
            
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


def get_loader() -> PluginLoader:
    """Get the global plugin loader instance."""
    global _global_loader
    if _global_loader is None:
        _global_loader = PluginLoader()
    return _global_loader


def init_loader(plugin_dirs: List[Path]) -> PluginLoader:
    """Initialize the global plugin loader with directories."""
    global _global_loader
    _global_loader = PluginLoader(plugin_dirs)
    return _global_loader

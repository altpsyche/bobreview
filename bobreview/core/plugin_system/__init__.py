"""
BobReview Plugin System Infrastructure.

This package provides the infrastructure for extending BobReview with plugins.
Plugins can register widgets, data parsers, LLM generators, themes, charts,
pages, and services.

Quick Start:
    from bobreview.core.plugin_system import BasePlugin, get_registry, get_loader

    # Create a plugin
    class MyPlugin(BasePlugin):
        name = "My Plugin"
        version = "1.0.0"
        
        def on_load(self, registry):
            registry.widgets.register(MyWidget)

    # Load plugins at startup
    loader = get_loader()
    loader.add_plugin_dir(Path("~/.bobreview/plugins"))
    loader.discover()
    loader.load_all_enabled()

Extension Points:
    - Widgets: Custom UI components
    - Data Parsers: New file format support
    - LLM Generators: Custom AI prompts
    - Themes: Visual styling
    - Charts: New chart types
    - Pages: Custom report sections
    - Services: Processing pipelines
"""

from .base import BasePlugin, PluginInfo
from .manifest import PluginManifest, validate_manifest
from .registry import (
    PluginRegistry,
    get_registry,
    reset_registry,
)
from .loader import (
    PluginLoader,
    PluginLoadError,
    PluginDependencyError,
    get_loader,
    init_loader,
)

__all__ = [
    # Base classes
    'BasePlugin',
    'PluginInfo',
    
    # Manifest
    'PluginManifest',
    'validate_manifest',
    
    # Registry
    'PluginRegistry',
    'get_registry',
    'reset_registry',
    
    # Loader
    'PluginLoader',
    'PluginLoadError',
    'PluginDependencyError',
    'get_loader',
    'init_loader',
]

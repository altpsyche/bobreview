"""
BobReview Plugin System Infrastructure.

This package provides the infrastructure for extending BobReview with plugins.
Plugins can register widgets, data parsers, LLM generators, themes, charts,
pages, and services.

Quick Start:
    from bobreview.core.plugin_system import get_extension_point, get_plugin_manager

    # Access plugin-provided implementations
    extension_point = get_extension_point()
    theme = extension_point.get_theme('dark')

    # Manage plugin lifecycle
    plugin_manager = get_plugin_manager()
    plugin_manager.discover()
    plugin_manager.load('my-plugin')

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
from .interface import (
    IExtensionPoint,
    IPluginManager,
    ExtensionPointProvider,
    PluginManagerProvider,
    get_extension_point,
    get_plugin_manager,
    reset_extension_point,
    reset_plugin_manager,
)
from .discovery import PluginDiscovery

__all__ = [
    # Abstract interfaces (preferred for core code)
    'IExtensionPoint',
    'IPluginManager',
    'get_extension_point',
    'get_plugin_manager',
    'reset_extension_point',
    'reset_plugin_manager',
    
    # Concrete implementations (for advanced use)
    'ExtensionPointProvider',
    'PluginManagerProvider',
    
    # Base classes
    'BasePlugin',
    'PluginInfo',
    
    # Manifest
    'PluginManifest',
    'validate_manifest',
    
    # Registry (internal - prefer IExtensionPoint)
    'PluginRegistry',
    'get_registry',
    'reset_registry',
    
    # Loader (internal - prefer IPluginManager)
    'PluginLoader',
    'PluginLoadError',
    'PluginDependencyError',
    'get_loader',
    'init_loader',
    
    # Discovery
    'PluginDiscovery',
]

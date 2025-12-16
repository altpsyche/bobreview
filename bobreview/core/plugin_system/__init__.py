"""
BobReview Plugin System Infrastructure.

This package provides the infrastructure for extending BobReview with plugins.
Plugins can register data parsers, report systems, templates, and services.

Quick Start:
    from bobreview.core.plugin_system import get_registry, get_loader

    # Access plugin registry
    registry = get_registry()
    parser = registry.data_parsers.get('csv')

    # Manage plugin lifecycle
    loader = get_loader()
    loader.discover()
    loader.load('my-plugin')
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
from .discovery import PluginDiscovery
from .plugin_helper import PluginHelper

__all__ = [
    # Registry (direct access)
    'PluginRegistry',
    'get_registry',
    'reset_registry',
    
    # Loader (direct access)
    'PluginLoader',
    'PluginLoadError',
    'PluginDependencyError',
    'get_loader',
    'init_loader',
    
    # Base classes
    'BasePlugin',
    'PluginInfo',
    
    # Plugin Helper (simplified registration)
    'PluginHelper',
    
    # Manifest
    'PluginManifest',
    'validate_manifest',
    
    # Discovery
    'PluginDiscovery',
]

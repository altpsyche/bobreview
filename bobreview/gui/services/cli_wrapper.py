"""
CLI Wrapper Service - Direct integration with BobReview core.

Provides functions to interact with the plugin system without subprocess calls.
"""

from pathlib import Path
from typing import List, Optional


def list_plugins(extra_dirs: Optional[List[str]] = None):
    """
    Get list of discovered plugins.
    
    Returns:
        List of PluginManifest objects with name, version, description, path, loaded
    """
    from bobreview.core.plugin_system import PluginDiscovery, init_loader
    
    dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=extra_dirs or [])
    loader = init_loader(dirs)
    loader.discover()
    return loader.get_discovered_plugins()


def get_plugin_info(name: str, extra_dirs: Optional[List[str]] = None):
    """
    Get detailed info about a specific plugin.
    
    Returns:
        PluginManifest or None if not found
    """
    plugins = list_plugins(extra_dirs)
    for p in plugins:
        if p.name == name or p.name.replace('_', '-') == name:
            return p
    return None


def create_plugin(
    name: str,
    output_dir: Optional[Path] = None,
    template: str = 'full'
) -> Path:
    """
    Create a new plugin using the scaffolder.
    
    Parameters:
        name: Plugin name (e.g., "my-plugin")
        output_dir: Where to create (default: ~/.bobreview/plugins/)
        template: 'minimal' or 'full'
    
    Returns:
        Path to created plugin directory
    """
    from bobreview.core.plugin_system.scaffolder.core import create_plugin as scaffold_create
    
    if output_dir is None:
        output_dir = Path.home() / ".bobreview" / "plugins"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return scaffold_create(name, output_dir, template)


def generate_report(
    plugin_name: str,
    data_dir: str,
    output_dir: str,
    config_path: Optional[str] = None,
    dry_run: bool = False,
    no_cache: bool = False,
    extra_plugin_dirs: Optional[List[str]] = None,
    llm_provider: Optional[str] = None,
    llm_api_key: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_temperature: Optional[float] = None,
) -> str:
    """
    Generate a report using the specified plugin.
    
    Parameters:
        plugin_name: Name of the plugin to use
        data_dir: Path to data directory
        output_dir: Path to output directory
        config_path: Optional path to custom config YAML
        dry_run: Skip LLM calls if True
        extra_plugin_dirs: Additional plugin search directories
        llm_provider: LLM provider (openai, anthropic, ollama)
        llm_api_key: API key for the LLM provider
        llm_model: Model name (e.g., gpt-4, claude-3-opus)
        llm_temperature: Temperature for LLM (0.0-2.0)
    
    Returns:
        Path to generated report
    
    Raises:
        ValueError: If plugin not found
        RuntimeError: If generation fails
    """
    import sys
    import os
    from bobreview.core.plugin_system import PluginDiscovery, init_loader, PluginLoadError
    
    # Initialize plugin system
    dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=extra_plugin_dirs or [])
    loader = init_loader(dirs)
    loader.discover()
    
    # Find the plugin
    plugins = loader.get_discovered_plugins()
    found = None
    for p in plugins:
        if p.name == plugin_name or p.name.replace('_', '-') == plugin_name:
            found = p
            break
    
    if not found:
        raise ValueError(f"Plugin '{plugin_name}' not found")
    
    # Load plugin if needed
    if not found.loaded:
        try:
            plugin_instance = loader.load(found.name)
        except PluginLoadError as e:
            raise RuntimeError(f"Failed to load plugin: {e}")
    else:
        plugin_instance = loader.get_loaded_plugin(found.name)
    
    if not plugin_instance:
        raise RuntimeError(f"Plugin loaded but no instance available")
    
    # Find generate_report function
    safe_name = found.name.replace('-', '_')
    plugin_module = None
    for mod_name in [f"bobreview.plugins.{safe_name}", f"plugins.{safe_name}", safe_name, f"user_plugins.{safe_name}"]:
        if mod_name in sys.modules:
            plugin_module = sys.modules[mod_name]
            break
    
    # Build kwargs
    kwargs = {"dry_run": dry_run, "no_cache": no_cache}
    if config_path:
        kwargs["config_path"] = config_path
    
    # LLM configuration - use passed values or fall back to environment
    if llm_provider:
        kwargs["llm_provider"] = llm_provider
    if llm_api_key:
        kwargs["llm_api_key"] = llm_api_key
    elif os.environ.get("OPENAI_API_KEY"):
        kwargs["llm_api_key"] = os.environ.get("OPENAI_API_KEY")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        kwargs["llm_api_key"] = os.environ.get("ANTHROPIC_API_KEY")
    if llm_model:
        kwargs["llm_model"] = llm_model
    if llm_temperature is not None:
        kwargs["llm_temperature"] = llm_temperature
    
    # Try module-level function first
    if plugin_module and hasattr(plugin_module, 'generate_report'):
        return plugin_module.generate_report(data_dir, output_dir, **kwargs)
    
    # Try instance method
    if hasattr(plugin_instance, 'generate_report'):
        return plugin_instance.generate_report(data_dir, output_dir, **kwargs)
    
    raise RuntimeError(f"Plugin '{plugin_name}' does not have a generate_report function")


"""
Report system loader for discovering and loading JSON report system definitions.

This module handles:
- Loading report systems from built-in and user directories
- Discovering available report systems
- Merging JSON definitions with CLI overrides
- Caching loaded definitions
"""

import copy
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from .schema import ReportSystemDefinition, parse_report_system_definition
from ..core.plugin_system import get_extension_point, get_plugin_manager


# Cache for loaded report systems
_report_system_cache: Dict[str, ReportSystemDefinition] = {}


def get_builtin_report_systems_dir() -> Path:
    """Get the path to the built-in report systems directory."""
    return Path(__file__).parent / 'builtin'


def get_user_report_systems_dir() -> Path:
    """Get the path to the user's custom report systems directory."""
    home = Path.home()
    return home / '.bobreview' / 'report_systems'


def _discover_systems_in_directory(
    directory: Path,
    source: str,
    logger: logging.Logger
) -> List[Dict[str, Any]]:
    """
    Discover report systems in a given directory.
    
    Parameters:
        directory: Directory to search for JSON report system files
        source: Source identifier ('builtin' or 'user')
        logger: Logger instance for warnings
    
    Returns:
        List of discovered system dictionaries
    """
    systems = []
    if directory.exists():
        for json_file in directory.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    systems.append({
                        'id': data.get('id', json_file.stem),
                        'name': data.get('name', json_file.stem),
                        'version': data.get('version', 'unknown'),
                        'description': data.get('description', ''),
                        'path': str(json_file),
                        'source': source
                    })
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Skipping invalid %s report system %s: %s", source, json_file, e)
    
    return systems


def discover_report_systems() -> List[Dict[str, Any]]:
    """
    Discover all available report systems (plugin-registered, built-in, and user custom).
    
    Uses lazy discovery - checks plugin directories for report_systems/ subdirectories
    without loading the plugins, then also checks loaded plugins in the registry.
    
    Returns:
        List of dictionaries with 'id', 'name', 'version', 'path', 'source' keys
    """
    logger = logging.getLogger(__name__)
    systems = []
    
    # First, discover report systems from plugin directories (without loading plugins)
    # Check plugin directories for report_systems/ subdirectories
    plugin_manager = get_plugin_manager()
    # Get discovered plugin manifests (not loaded plugins)
    manifests = plugin_manager.get_discovered_plugins() if hasattr(plugin_manager, 'get_discovered_plugins') else []
    if not manifests:
        # Try discovering if not done yet
        try:
            plugin_manager.discover()
            manifests = plugin_manager.get_discovered_plugins()
        except:
            pass
    
    # Check each plugin's directory for report_systems/ subdirectory
    for plugin_info in manifests:
        plugin_path = Path(plugin_info.path) if plugin_info.path else None
        if plugin_path and plugin_path.exists():
            report_systems_dir = plugin_path / 'report_systems'
            if report_systems_dir.exists():
                for system in _discover_systems_in_directory(report_systems_dir, 'plugin', logger):
                    # Don't duplicate
                    if not any(s['id'] == system['id'] for s in systems):
                        systems.append(system)
    
    # Also check plugin registry for report systems from already-loaded plugins
    extension_point = get_extension_point()
    for name, system_def in extension_point.get_all_report_systems().items():
        # Don't duplicate if already discovered from filesystem
        if not any(s['id'] == (system_def.get('id', name) if isinstance(system_def, dict) else getattr(system_def, 'id', name)) for s in systems):
            systems.append({
                'id': system_def.get('id', name) if isinstance(system_def, dict) else getattr(system_def, 'id', name),
                'name': system_def.get('name', name) if isinstance(system_def, dict) else getattr(system_def, 'name', name),
                'version': system_def.get('version', 'unknown') if isinstance(system_def, dict) else getattr(system_def, 'version', 'unknown'),
                'description': system_def.get('description', '') if isinstance(system_def, dict) else getattr(system_def, 'description', ''),
                'path': f'plugin:{name}',  # Indicate it's from a plugin
                'source': 'plugin'
            })
    
    # Discover built-in systems (filesystem fallback)
    builtin_dir = get_builtin_report_systems_dir()
    for system in _discover_systems_in_directory(builtin_dir, 'builtin', logger):
        # Don't duplicate if already registered by plugin
        if not any(s['id'] == system['id'] for s in systems):
            systems.append(system)
    
    # Discover user custom systems
    user_dir = get_user_report_systems_dir()
    systems.extend(_discover_systems_in_directory(user_dir, 'user', logger))
    
    # Return systems in deterministic order (sorted by source priority, then id)
    source_priority = {'plugin': 0, 'user': 1, 'builtin': 2}
    return sorted(systems, key=lambda s: (source_priority.get(s["source"], 99), s["id"]))


def list_available_systems() -> List[Dict[str, Any]]:
    """
    List all available report systems with their metadata.
    
    Returns:
        List of system info dictionaries
    """
    return discover_report_systems()


def find_report_system_path(id_or_path: str, plugin_name: Optional[str] = None) -> Optional[Path]:
    """
    Find the path to a report system JSON file.
    
    Search order:
    1. If id_or_path is a valid file path, use it directly
    2. If plugin_name is specified, look in that plugin's report_systems/ directory first
    3. Look in plugin directories (without loading plugins)
    4. Look in user directory (~/.bobreview/report_systems/)
    5. Look in built-in directory (bobreview/engine/builtin/)
    
    Parameters:
        id_or_path: Report system ID (e.g., 'png_data_points') or full path to JSON file
        plugin_name: Optional plugin name to search in first
    
    Returns:
        Path to the JSON file, or None if not found
    """
    # Check if it's a direct path to a file
    direct_path = Path(id_or_path)
    if direct_path.exists() and direct_path.is_file():
        return direct_path.resolve()
    
    # If it's a bare filename like "foo.json", also try its stem as an ID
    candidate_id = direct_path.stem if direct_path.suffix == ".json" and direct_path.parent == Path("") else id_or_path
    
    # If plugin_name is specified, try that plugin first
    if plugin_name:
        plugin_manager = get_plugin_manager()
        if not plugin_manager.get_discovered_plugins():
            plugin_manager.discover()
        
        for manifest in plugin_manager.get_discovered_plugins():
            if manifest.name == plugin_name or manifest.name.replace('-', '_') == plugin_name.replace('-', '_'):
                plugin_path = Path(manifest.path) if manifest.path else None
                if plugin_path and plugin_path.exists():
                    plugin_json_path = plugin_path / 'report_systems' / f"{candidate_id}.json"
                    if plugin_json_path.exists():
                        return plugin_json_path.resolve()
                break
    
    # Try in plugin directories (check filesystem without loading plugins)
    plugin_manager = get_plugin_manager()
    manifests = plugin_manager.get_discovered_plugins() if hasattr(plugin_manager, 'get_discovered_plugins') else []
    if not manifests:
        # Try discovering if not done yet
        try:
            plugin_manager.discover()
            manifests = plugin_manager.get_discovered_plugins()
        except:
            pass
    
    # Check each plugin's report_systems/ directory
    for plugin_info in manifests:
        plugin_path = Path(plugin_info.path) if plugin_info.path else None
        if plugin_path and plugin_path.exists():
            plugin_json_path = plugin_path / 'report_systems' / f"{candidate_id}.json"
            if plugin_json_path.exists():
                return plugin_json_path.resolve()
    
    # Try as ID in user directory
    user_dir = get_user_report_systems_dir()
    user_path = user_dir / f"{candidate_id}.json"
    if user_path.exists():
        return user_path.resolve()
    
    # Try as ID in built-in directory
    builtin_dir = get_builtin_report_systems_dir()
    builtin_path = builtin_dir / f"{candidate_id}.json"
    if builtin_path.exists():
        return builtin_path.resolve()
    
    return None


def load_report_system_json(path: Path) -> Dict[str, Any]:
    """
    Load and parse a report system JSON file.
    
    Parameters:
        path: Path to JSON file
    
    Returns:
        Parsed JSON data as dictionary
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Report system file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_cli_overrides(
    system_data: Dict[str, Any],
    cli_overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge CLI argument overrides into report system definition.
    
    CLI arguments can override certain fields from the JSON, such as:
    - thresholds (draw_hard_cap, tri_hard_cap, etc.)
    - llm_config (model, temperature, etc.)
    - output settings (embed_images, linked_css, etc.)
    
    Parameters:
        system_data: Base report system data from JSON
        cli_overrides: Dictionary of CLI override values
    
    Returns:
        Merged report system data
    """
    if not cli_overrides:
        return system_data
    
    # Create a deep copy to avoid modifying original (including nested dicts)
    merged = copy.deepcopy(system_data)
    
    # Merge thresholds
    if 'thresholds' in cli_overrides:
        if 'thresholds' not in merged:
            merged['thresholds'] = {}
        merged['thresholds'].update(cli_overrides['thresholds'])
    
    # Merge LLM config
    if 'llm_config' in cli_overrides:
        if 'llm_config' not in merged:
            merged['llm_config'] = {}
        merged['llm_config'].update(cli_overrides['llm_config'])
    
    # Merge output config
    if 'output' in cli_overrides:
        if 'output' not in merged:
            merged['output'] = {}
        merged['output'].update(cli_overrides['output'])
    
    # Merge theme
    if 'theme' in cli_overrides:
        if 'theme' not in merged:
            merged['theme'] = {}
        merged['theme'].update(cli_overrides['theme'])
    
    # Handle page disabling
    if 'disabled_pages' in cli_overrides:
        disabled_ids = cli_overrides['disabled_pages']
        if 'pages' in merged:
            for page in merged['pages']:
                if page.get('id') in disabled_ids:
                    page['enabled'] = False
        # Remove CLI-only key from merged dict
        merged.pop('disabled_pages', None)
    
    return merged


def load_report_system(
    id_or_path: str,
    cli_overrides: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    plugin_name: Optional[str] = None
) -> ReportSystemDefinition:
    """
    Load a report system definition.
    
    Search order:
    1. If plugin_name is specified, search in that plugin first
    2. Plugin registry (systems registered by plugins)
    3. User directory (~/.bobreview/report_systems/)
    4. Built-in directory (bobreview/engine/builtin/)
    5. Direct file path
    
    Automatically loads required plugins if the report system is provided by a plugin.
    
    Parameters:
        id_or_path: Report system ID or path to JSON file
        cli_overrides: Optional CLI argument overrides
        use_cache: Whether to use cached definitions
        plugin_name: Optional plugin name to prioritize search in
    
    Returns:
        ReportSystemDefinition object
    
    Raises:
        FileNotFoundError: If report system not found
        ValueError: If JSON validation fails
    """
    # Check cache first
    if cli_overrides is None:
        overrides_key = ""
    else:
        # Normalize overrides so equivalent dicts share the same cache key
        # Use default=str to handle non-JSON-serializable types (e.g., Path, Enum)
        overrides_key = json.dumps(cli_overrides, sort_keys=True, default=str)
    cache_key = f"{id_or_path}:{overrides_key}"
    if use_cache and cache_key in _report_system_cache:
        # Return a deep copy to prevent mutation of cached instances
        return copy.deepcopy(_report_system_cache[cache_key])
    
    system_data = None
    source_description = None
    found_plugin_name = None
    
    # First, check plugin registry for the system
    extension_point = get_extension_point()
    plugin_system = extension_point.get_report_system(id_or_path)
    if plugin_system is not None:
        system_data = copy.deepcopy(plugin_system)
        source_description = f"plugin:{id_or_path}"
        
        # Find which plugin provides this report system
        component_key = f"report_system:{id_or_path}"
        found_plugin_name = extension_point.get_component_owner(component_key)
        
        # Auto-load the plugin if not already loaded
        if found_plugin_name:
            plugin_manager = get_plugin_manager()
            if not plugin_manager.is_loaded(found_plugin_name):
                _logger = logging.getLogger(__name__)
                _logger.info(f"Auto-loading required plugin: {found_plugin_name}")
                try:
                    plugin_manager.load(found_plugin_name)
                except Exception as e:
                    _logger.warning(
                        f"Failed to auto-load plugin '{found_plugin_name}' for report system '{id_or_path}': {e}"
                    )
    
    # If not found in registry, try filesystem
    if system_data is None:
        json_path = find_report_system_path(id_or_path, plugin_name=plugin_name)
        if json_path is None:
            available = [s['id'] for s in list_available_systems()]
            raise FileNotFoundError(
                f"Report system not found: {id_or_path}\n"
                f"Available systems: {', '.join(available) if available else 'none'}\n"
                f"Search paths:\n"
                f"  - Plugin registry\n"
                f"  - User: {get_user_report_systems_dir()}\n"
                f"  - Built-in: {get_builtin_report_systems_dir()}"
            )
        
        # Load JSON data from filesystem
        try:
            system_data = load_report_system_json(json_path)
            source_description = str(json_path)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in report system file {json_path}: {e}") from e
    
    # Merge CLI overrides
    if cli_overrides:
        system_data = merge_cli_overrides(system_data, cli_overrides)
    
    # Parse into ReportSystemDefinition
    try:
        system_def = parse_report_system_definition(system_data)
    except ValueError as e:
        raise ValueError(f"Failed to load report system from {source_description}: {e}") from e
    
    # Cache the result (deep copy to prevent mutation)
    if use_cache:
        _report_system_cache[cache_key] = copy.deepcopy(system_def)
    
    return system_def


def clear_cache():
    """Clear the report system cache."""
    _report_system_cache.clear()


def ensure_user_directory() -> Path:
    """
    Ensure the user's report systems directory exists.
    
    Returns:
        Path to the user directory
    """
    user_dir = get_user_report_systems_dir()
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


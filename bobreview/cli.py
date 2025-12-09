#!/usr/bin/env python3
"""
Command-line interface for BobReview.
"""

import argparse
import os
import sys
import time
import random
from pathlib import Path

from . import __version__
from .core import ReportConfig, validate_config, log_info, log_success, log_warning, log_error, log_verbose, format_number
from .core import init_cache, get_cache, analyze_data
from .core.config import LLMConfig, CacheConfig, ExecutionConfig, OutputConfig

# Import report systems framework
from .engine import load_report_system, list_available_systems
from .engine.executor import ReportSystemExecutor

# Import provider listing
from .services.llm.providers import list_providers, get_provider_info

# Import plugin system
from .core.plugin_system import get_loader, init_loader

# Check for tqdm availability
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    class tqdm:
        def __init__(self, iterable=None, desc=None, total=None, **kwargs):
            self.iterable = iterable
        def __iter__(self):
            return iter(self.iterable)


def _get_default_plugin_dirs():
    """Get default plugin directories."""
    dirs = []
    
    # Built-in plugins directory (highest priority)
    from . import plugins
    builtin_dir = Path(plugins.__file__).parent
    if builtin_dir.exists():
        dirs.append(builtin_dir)
    
    # User plugin directory: ~/.bobreview/plugins
    user_dir = Path.home() / ".bobreview" / "plugins"
    if user_dir.exists():
        dirs.append(user_dir)
    
    # Current directory plugins: ./plugins
    local_dir = Path.cwd() / "plugins"
    if local_dir.exists():
        dirs.append(local_dir)
    
    return dirs


def _load_plugins(extra_dirs, config):
    """
    Load plugins from default and extra directories.
    
    All plugins (built-in and external) are discovered and loaded through
    the unified plugin discovery mechanism.
    """
    dirs = _get_default_plugin_dirs()
    
    # Add extra directories from CLI
    for d in extra_dirs:
        path = Path(d).expanduser().resolve()
        if path.exists() and path not in dirs:
            dirs.append(path)
    
    if not dirs:
        log_verbose("No plugin directories configured", config)
        return
    
    loader = init_loader(dirs)
    discovered = loader.discover()
    
    if discovered:
        log_verbose(f"Discovered {len(discovered)} plugins (will load on-demand)", config)
        
        # Don't load all plugins upfront - let load_report_system() lazy-load
        # only the plugin needed for the requested report system.
        # This improves startup time and prevents errors from broken plugins
        # that aren't actually needed.


# Removed _load_core_plugin() - built-in plugins are now discovered and loaded
# through the unified plugin discovery mechanism in _load_plugins()


def handle_plugin_command(args):
    """Handle plugin subcommands."""
    from .core.plugin_system import init_loader
    
    # Initialize loader with default directories
    dirs = _get_default_plugin_dirs()
    loader = init_loader(dirs)
    loader.discover()
    
    if args.plugin_command == 'list':
        plugins = loader.get_discovered_plugins()
        if not plugins:
            print("No plugins found.")
            print(f"\nPlugin directories searched:")
            for d in dirs:
                print(f"  - {d}")
            print("\nTo add plugins, place them in ~/.bobreview/plugins/")
            return 0
        
        print("Installed plugins:\n")
        for p in plugins:
            status = "✓ loaded" if p.loaded else "○ available"
            print(f"  {p.name} v{p.version} [{status}]")
            if args.verbose:
                print(f"    Author: {p.author}")
                print(f"    {p.description}")
                if p.provides:
                    provides_str = ", ".join(f"{k}: {len(v)}" for k, v in p.provides.items())
                    print(f"    Provides: {provides_str}")
                print()
        return 0
    
    elif args.plugin_command == 'install':
        plugin_path = Path(args.path).expanduser().resolve()
        
        if not plugin_path.exists():
            print(f"Error: Path does not exist: {plugin_path}")
            return 1
        
        manifest_path = plugin_path / "manifest.json"
        if not manifest_path.exists():
            print(f"Error: No manifest.json found in {plugin_path}")
            return 1
        
        # Copy to user plugin directory
        user_plugins = Path.home() / ".bobreview" / "plugins"
        user_plugins.mkdir(parents=True, exist_ok=True)
        
        import shutil
        dest = user_plugins / plugin_path.name
        if dest.exists():
            print(f"Plugin already installed at: {dest}")
            print("Use 'bob plugins uninstall' first to reinstall.")
            return 1
        
        shutil.copytree(plugin_path, dest)
        print(f"✓ Installed plugin to: {dest}")
        
        # Reload and show info
        loader.add_plugin_dir(user_plugins)
        loader.discover()
        
        from .core.plugin_system import PluginManifest
        manifest = PluginManifest.from_file(manifest_path)
        print(f"  Name: {manifest.name} v{manifest.version}")
        print(f"  Author: {manifest.author}")
        return 0
    
    elif args.plugin_command == 'uninstall':
        user_plugins = Path.home() / ".bobreview" / "plugins"
        
        # Find the plugin
        found = None
        for p in loader.get_discovered_plugins():
            if p.name == args.name and p.path:
                found = Path(p.path)
                break
        
        if not found:
            print(f"Error: Plugin not found: {args.name}")
            return 1
        
        # Only allow uninstalling from user directory
        try:
            found.relative_to(user_plugins)
        except ValueError:
            print(f"Cannot uninstall built-in plugin: {args.name}")
            return 1
        
        import shutil
        shutil.rmtree(found)
        print(f"✓ Uninstalled plugin: {args.name}")
        return 0
    
    elif args.plugin_command == 'info':
        plugins = loader.get_discovered_plugins()
        found = None
        for p in plugins:
            if p.name == args.name:
                found = p
                break
        
        if not found:
            print(f"Plugin not found: {args.name}")
            return 1
        
        print(f"Plugin: {found.name}")
        print(f"  Version: {found.version}")
        print(f"  Author: {found.author}")
        print(f"  Description: {found.description}")
        print(f"  Path: {found.path}")
        print(f"  Status: {'loaded' if found.loaded else 'not loaded'}")
        if found.dependencies:
            print(f"  Dependencies: {', '.join(found.dependencies)}")
        if found.provides:
            print("  Provides:")
            for ext_type, items in found.provides.items():
                print(f"    {ext_type}: {', '.join(items)}")
        return 0
    
    else:
        print("Usage: bob plugins <list|install|uninstall|info>")
        return 1


def main():
    """
    Parse CLI arguments, analyze PNG-captured performance data, optionally call an LLM, and write an HTML performance report.
    
    Returns:
        exit_code (int): 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        prog='bobreview',
        description='BobReview - Performance Analysis and Review Tool for Game Development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with plugin (required)
  bobreview --plugin <plugin-name> --dir ./screenshots

  # Use Anthropic Claude
  bobreview --plugin <plugin-name> --dir ./screenshots --llm-provider anthropic --llm-model claude-3-sonnet-20240229

  # Use local Ollama
  bobreview --plugin <plugin-name> --dir ./screenshots --llm-provider ollama --llm-model llama2

  # Custom title
  bobreview --plugin <plugin-name> --dir ./screenshots --title "My Analysis"

  # Explicit report system from plugin (required if plugin has multiple systems)
  bobreview --plugin <plugin-name> --report-system <system-id> --dir ./screenshots

  # Dry run to test without calling LLM
  bobreview --plugin <plugin-name> --dir ./screenshots --dry-run

  # List available plugins and report systems
  bobreview plugins list
  bobreview --list-plugins
  bobreview --list-report-systems

  # List available LLM providers
  bobreview --list-providers
        """
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--dir', type=str, default='.',
        help='Directory containing PNG files (default: current directory)'
    )
    parser.add_argument(
        '--output', type=str, default='performance_report.html',
        help='Output directory/file path (creates index.html and additional pages)'
    )
    parser.add_argument(
        '--title', type=str, default=None,
        help='Report title (can also be extracted from parsed data, e.g., game.json)'
    )
    
    parser.add_argument(
        '--no-recommendations', action='store_true',
        help='Disable system-level recommendations section'
    )
    
    # LLM Provider arguments (unified)
    parser.add_argument(
        '--llm-provider', type=str, default='openai',
        choices=['openai', 'anthropic', 'ollama'],
        help='LLM provider to use (default: openai)'
    )
    parser.add_argument(
        '--llm-api-key', type=str, default=None,
        help='API key for LLM provider (or use OPENAI_API_KEY, ANTHROPIC_API_KEY env vars)'
    )
    parser.add_argument(
        '--llm-api-base', type=str, default=None,
        help='Custom API base URL (e.g., for Ollama: http://localhost:11434)'
    )
    parser.add_argument(
        '--llm-model', type=str, default=None,
        help='Model to use (default depends on provider: gpt-4o, claude-3-5-sonnet-20241022, llama2)'
    )
    parser.add_argument(
        '--llm-temperature', type=float, default=0.7,
        help='LLM temperature for generation (default: 0.7)'
    )
    parser.add_argument(
        '--llm-max-tokens', type=int, default=2000,
        help='Maximum tokens for LLM responses (default: 2000)'
    )
    parser.add_argument(
        '--llm-chunk-size', type=int, default=10,
        help='Number of data samples to send per LLM call (default: 10)'
    )
    parser.add_argument(
        '--llm-combine-warning-threshold', type=int, default=100000,
        help='Character count threshold for warning when combining chunks (default: 100000)'
    )
    parser.add_argument(
        '--list-providers', action='store_true',
        help='List available LLM providers and exit'
    )
    
    # Caching options
    parser.add_argument(
        '--cache-dir', type=str, default='.bobreview_cache',
        help='Directory for caching LLM responses (default: .bobreview_cache)'
    )
    parser.add_argument(
        '--use-cache', action='store_true', default=True,
        help='Use cached LLM responses when available (default: enabled)'
    )
    parser.add_argument(
        '--no-cache', action='store_false', dest='use_cache',
        help='Disable caching and always call LLM'
    )
    parser.add_argument(
        '--clear-cache', action='store_true',
        help='Clear all cached responses before running'
    )
    
    # Execution options
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Analyze data but skip LLM calls (generates placeholder content)'
    )
    parser.add_argument(
        '--sample', type=int, default=None, dest='sample_size',
        help='Process only N random samples (for testing)'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose output (debug information)'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Suppress all output except errors'
    )
    parser.add_argument(
        '--no-embed-images', action='store_false', dest='embed_images', default=True,
        help='Use external image files instead of embedding'
    )
    parser.add_argument(
        '--linked-css', action='store_true', default=False,
        help='Use external CSS file instead of embedding'
    )
    parser.add_argument(
        '--theme', type=str, default='dark', dest='theme_id',
        choices=['dark', 'light', 'high_contrast'],
        help='Report theme (default: dark)'
    )
    parser.add_argument(
        '--disable-page', action='append', dest='disabled_pages', default=[],
        metavar='PAGE_ID',
        help='Disable a page by ID (can be used multiple times)'
    )
    # Plugin and report system selection
    parser.add_argument(
        '--plugin', type=str, required=False,
        metavar='PLUGIN_NAME',
        help='Plugin to use. Use --list-plugins to see available plugins. Plugin name matching is case-insensitive.'
    )
    parser.add_argument(
        '--report-system', type=str, default=None,
        metavar='SYSTEM',
        help='Report system to use (system ID). Required if --plugin has multiple systems. If omitted, uses the single report system from the plugin.'
    )
    parser.add_argument(
        '--list-report-systems', action='store_true',
        help='List all available report systems and exit'
    )
    parser.add_argument(
        '--list-plugins', action='store_true',
        help='List all available plugins and exit'
    )
    
    # Plugin arguments
    parser.add_argument(
        '--plugin-dir', action='append', dest='plugin_dirs', default=[],
        metavar='DIR',
        help='Additional plugin directory (can be used multiple times)'
    )
    parser.add_argument(
        '--no-plugins', action='store_true',
        help='Disable plugin loading'
    )
    
    # Plugin subcommands
    subparsers = parser.add_subparsers(dest='command', help='Plugin management commands')
    
    # bob plugins list
    plugins_parser = subparsers.add_parser('plugins', help='Plugin management')
    plugins_subparsers = plugins_parser.add_subparsers(dest='plugin_command')
    
    plugins_list = plugins_subparsers.add_parser('list', help='List installed plugins')
    plugins_list.add_argument('--verbose', '-v', action='store_true', help='Show detailed info')
    
    plugins_install = plugins_subparsers.add_parser('install', help='Install a plugin')
    plugins_install.add_argument('path', help='Path to plugin directory')
    
    plugins_uninstall = plugins_subparsers.add_parser('uninstall', help='Uninstall a plugin')
    plugins_uninstall.add_argument('name', help='Plugin name to uninstall')
    
    plugins_info = plugins_subparsers.add_parser('info', help='Show plugin details')
    plugins_info.add_argument('name', help='Plugin name')
    
    # Parse args
    args = parser.parse_args()
    
    # Handle --list-providers
    if args.list_providers:
        print("Available LLM providers:\n")
        for provider_name in list_providers():
            info = get_provider_info(provider_name)
            key_info = f"(requires {info['env_key_name']})" if info['requires_api_key'] else "(no API key needed)"
            print(f"  {provider_name}")
            print(f"    Default model: {info['default_model']}")
            print(f"    {key_info}")
            print()
        return 0
    
    # Handle --list-report-systems
    if args.list_report_systems:
        systems = list_available_systems()
        if not systems:
            print("No report systems found.")
            return 0
        
        print("Available report systems:\n")
        for system in systems:
            source_label = "built-in" if system['source'] == 'builtin' else "custom"
            print(f"  {system['id']} ({source_label}) - v{system['version']}")
            print(f"    {system['description']}")
            print(f"    Path: {system['path']}")
            print()
        return 0
    
    # Handle --list-plugins
    if args.list_plugins:
        dirs = _get_default_plugin_dirs()
        loader = init_loader(dirs)
        loader.discover()
        plugins = loader.get_discovered_plugins()
        
        if not plugins:
            print("No plugins found.")
            print(f"\nPlugin directories searched:")
            for d in dirs:
                print(f"  - {d}")
            print("\nTo add plugins, place them in ~/.bobreview/plugins/")
            return 0
        
        print("Available plugins:\n")
        for p in plugins:
            status = "✓ loaded" if p.loaded else "○ available"
            print(f"  {p.name} v{p.version} [{status}]")
            if p.description:
                print(f"    {p.description}")
            if p.author:
                print(f"    Author: {p.author}")
            if p.provides:
                provides_str = ", ".join(f"{k}: {len(v)}" for k, v in p.provides.items())
                print(f"    Provides: {provides_str}")
            print()
        return 0
    
    # Handle plugin commands
    if args.command == 'plugins':
        return handle_plugin_command(args)
    
    # Validate that --plugin is provided if not using list commands
    if not args.plugin and not (args.list_plugins or args.list_report_systems or args.list_providers):
        parser.error("--plugin is required (unless using --list-plugins, --list-report-systems, or --list-providers)")
    
    # Handle quiet + verbose conflict
    if args.quiet and args.verbose:
        parser.error("Cannot use both --quiet and --verbose")
    
    start_time = time.time()
    
    # Get default model based on provider if not specified
    if args.llm_model is None:
        default_models = {
            'openai': 'gpt-4o',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'ollama': 'llama2'
        }
        args.llm_model = default_models.get(args.llm_provider, 'gpt-4o')
    
    # Get API key from environment if not provided
    env_key_names = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'ollama': None  # Ollama doesn't need API key
    }
    
    llm_api_key = args.llm_api_key
    if not llm_api_key and args.llm_provider != 'ollama':
        env_key = env_key_names.get(args.llm_provider)
        if env_key:
            llm_api_key = os.getenv(env_key)
    
    # Check for API key (unless dry run or Ollama)
    if not llm_api_key and not args.dry_run and args.llm_provider != 'ollama':
        env_key = env_key_names.get(args.llm_provider, 'API_KEY')
        parser.error(
            f"API key required for {args.llm_provider}. "
            f"Set {env_key} environment variable or use --llm-api-key"
        )
    
    # Build configuration
    # Note: Thresholds are defined in report system JSON files, not via CLI
    # Title can come from parsed data (e.g., game.json), so default to None if not provided
    config = ReportConfig(
        title=args.title,  # None if not provided - will be extracted from parsed data if available
        # Use default ThresholdConfig - thresholds come from report system JSON
        llm=LLMConfig(
            provider=args.llm_provider,
            api_key=llm_api_key,
            api_base=args.llm_api_base,
            model=args.llm_model,
            temperature=args.llm_temperature,
            max_tokens=args.llm_max_tokens,
            chunk_size=args.llm_chunk_size,
            combine_warning_threshold=args.llm_combine_warning_threshold,
            enable_cache=args.use_cache and not args.dry_run,
        ),
        cache=CacheConfig(
            cache_dir=Path(args.cache_dir),
            use_cache=args.use_cache and not args.dry_run,
            clear_cache=args.clear_cache,
        ),
        execution=ExecutionConfig(
            dry_run=args.dry_run,
            sample_size=args.sample_size,
            verbose=args.verbose,
            quiet=args.quiet,
            enable_recommendations=not args.no_recommendations,
        ),
        output=OutputConfig(
            embed_images=args.embed_images,
            linked_css=args.linked_css,
            theme_id=args.theme_id,
            disabled_pages=args.disabled_pages,
        )
    )
    
    # Validate configuration
    validation_errors = validate_config(config)
    if validation_errors:
        log_error("Configuration validation failed:")
        for error in validation_errors:
            log_error(f"  - {error}")
        return 1
    
    # Initialize cache
    init_cache(config)
    
    # Clear cache if requested
    if config.cache.clear_cache:
        cache = get_cache()
        if cache:
            cache.clear()
    
    if config.execution.dry_run:
        log_warning("Running in DRY RUN mode - LLM calls will be skipped", config)
    
    log_verbose(f"LLM Provider: {config.llm.provider} (model: {config.llm.model})", config)
    
    # Load plugins (unless disabled)
    # IMPORTANT: Plugins must be loaded BEFORE template engine is first accessed
    # to ensure plugin templates are available
    if not args.no_plugins:
        _load_plugins(args.plugin_dirs, config)
        
        # Refresh template engine to pick up plugin templates
        from .core.template_engine import reset_template_engine
        reset_template_engine()
    
    # Use the JSON-based report system framework
    try:
        # Plugin is required - determine which report system to use
        if args.report_system:
            # Explicit system specified
            report_system_id = args.report_system
        else:
            # No explicit system - auto-select if only one, require selection if multiple
            from .core.plugin_system import get_loader
            plugin_manager = get_loader()
            
            # Ensure plugins are discovered (if not already)
            if not plugin_manager.get_discovered_plugins():
                plugin_manager.discover()
            
            plugin_path = None
            matched_manifest = None
            plugin_name_normalized = args.plugin.lower().replace('-', '_').replace(' ', '')
            for manifest in plugin_manager.get_discovered_plugins():
                manifest_name_normalized = manifest.name.lower().replace('-', '_').replace(' ', '')
                # Exact match
                if manifest.name == args.plugin:
                    plugin_path = Path(manifest.path) if manifest.path else None
                    matched_manifest = manifest
                    break
                # Normalized match (case-insensitive, dash/underscore agnostic)
                elif manifest_name_normalized == plugin_name_normalized:
                    plugin_path = Path(manifest.path) if manifest.path else None
                    matched_manifest = manifest
                    break
                # Substring match (e.g., partial plugin name matches full plugin name)
                elif plugin_name_normalized in manifest_name_normalized or manifest_name_normalized in plugin_name_normalized:
                    plugin_path = Path(manifest.path) if manifest.path else None
                    matched_manifest = manifest
                    break
            
            # Load the plugin if found
            if matched_manifest:
                if not plugin_manager.is_loaded(matched_manifest.name):
                    try:
                        plugin_manager.load(matched_manifest.name)
                        log_info(f"Loaded plugin: {matched_manifest.name}", config)
                    except Exception as e:
                        log_warning(f"Failed to load plugin '{matched_manifest.name}': {e}", config)
                # Update args.plugin to the actual plugin name for consistency
                args.plugin = matched_manifest.name
            
            if plugin_path:
                # Find report systems in plugin
                plugin_systems_dir = plugin_path / 'report_systems'
                if plugin_systems_dir.exists():
                    json_files = sorted(plugin_systems_dir.glob('*.json'))  # Sort for deterministic order
                    if json_files:
                        if len(json_files) == 1:
                            # Only one system - auto-select it
                            report_system_id = json_files[0].stem
                            log_info(f"Using report system '{report_system_id}' from plugin '{args.plugin}'", config)
                        else:
                            # Multiple systems - require explicit selection
                            system_names = [f.stem for f in json_files]
                            log_error(
                                f"Plugin '{args.plugin}' has {len(json_files)} report systems. "
                                f"Please specify which one to use with --report-system.\n"
                                f"Available systems: {', '.join(system_names)}"
                            )
                            return 1
                    else:
                        log_error(f"Plugin '{args.plugin}' has no report systems")
                        return 1
                else:
                    log_error(f"Plugin '{args.plugin}' has no report_systems directory")
                    return 1
            else:
                # Plugin not found - provide helpful error message
                available_plugins = [m.name for m in plugin_manager.get_discovered_plugins()]
                if available_plugins:
                    # Check if user included version number
                    plugin_name_clean = args.plugin.split()[0] if ' ' in args.plugin else args.plugin
                    suggestions = [p for p in available_plugins 
                                 if plugin_name_clean.lower() in p.lower() or p.lower() in plugin_name_clean.lower()]
                    error_msg = f"Plugin '{args.plugin}' not found.\n"
                    if ' ' in args.plugin or 'v' in args.plugin.lower():
                        error_msg += "Note: Do not include version numbers in the plugin name. "
                        error_msg += f"Use just the plugin name (e.g., '{plugin_name_clean}').\n"
                    error_msg += f"Available plugins: {', '.join(available_plugins)}"
                    if suggestions:
                        error_msg += f"\nDid you mean: {', '.join(suggestions)}?"
                    log_error(error_msg)
                else:
                    log_error(f"Plugin '{args.plugin}' not found. No plugins are available.")
                return 1
        
        log_info(f"Loading report system: {report_system_id}", config)
        
        # Build CLI overrides for the JSON system
        # Note: Thresholds are defined in report system JSON files, not overridden via CLI
        cli_overrides = {
            'llm_config': {
                'provider': config.llm.provider,
                'model': config.llm.model,
                'temperature': config.llm.temperature,
                'max_tokens': config.llm.max_tokens,
                'chunk_size': config.llm.chunk_size,
                'enable_cache': config.llm.enable_cache,
            },
            'output': {
                'embed_images': config.output.embed_images,
                'linked_css': config.output.linked_css,
            },
            'theme': {
                'default': config.output.theme_id,
            },
            'disabled_pages': config.output.disabled_pages
        }
        
        # Load report system with CLI overrides, passing plugin name for prioritized search
        system_def = load_report_system(report_system_id, cli_overrides=cli_overrides, plugin_name=args.plugin)
        
        # Create executor
        executor = ReportSystemExecutor(system_def, config)
        
        # Execute
        input_dir = Path(args.dir).resolve()
        output_path = Path(args.output).resolve()
        
        if not input_dir.exists():
            log_error(f"Directory not found: {input_dir}")
            return 1
        
        if not input_dir.is_dir():
            log_error(f"Path is not a directory: {input_dir}")
            return 1
        
        executor.execute(input_dir, output_path)
        
        elapsed_time = time.time() - start_time
        log_info(f"Completed in {elapsed_time:.1f}s", config)
        
        return 0
        
    except FileNotFoundError as e:
        log_error(str(e))
        return 1
    except ValueError as e:
        log_error(f"Report system validation failed: {e}")
        return 1
    except Exception as e:
        log_error(f"Failed to execute report system: {e}")
        if config.execution.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

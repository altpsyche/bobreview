#!/usr/bin/env python3
"""
Command-line interface for BobReview.

Plugin-First Architecture:
- Core provides minimal infrastructure
- Plugins provide all features
- This CLI is a minimal skeleton for plugin management
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import Config, log_info, log_success, log_warning, log_error, log_verbose
from .core.plugin_system import get_loader, init_loader, PluginDiscovery, PluginManifest, PluginLoadError

# Import rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def print_banner():
    """Print a styled banner for BobReview."""
    if not RICH_AVAILABLE:
        print(f"\nBobReview v{__version__}")
        print("=" * 40)
        return
    
    title = Text()
    title.append("Bob", style="bold cyan")
    title.append("Review", style="bold white")
    title.append(f" v{__version__}", style="bold dim cyan")
    
    console.print()
    console.print(Panel(
        title,
        subtitle="[dim]Plugin-First Report Framework[/dim]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
    ))


def print_rich_help():
    """Print beautiful rich-formatted help instead of argparse default."""
    if not RICH_AVAILABLE:
        return False
    
    from rich.markdown import Markdown
    
    print_banner()
    console.print()
    
    # Tool description
    intro = Markdown("""
Generate beautiful HTML reports from any data using **[BobReview]** and a **plugin-based architecture**.

- **Plugin-First** - All features come from plugins  
- **Extensible** - Create plugins for any data format
- **Themeable** - Custom themes per plugin
""")
    console.print(intro)
    console.print()
    
    # Quick start
    console.print("[bold cyan]Quick Start[/bold cyan]")
    console.print(
        "  [dim]Create:[/dim]  "
        "[cyan]bobreview[/cyan] [magenta]plugins[/magenta] [green]create[/green] [cyan]<name>[/cyan]"
    )
    console.print(
        "  [dim]Use:[/dim]     "
        "[cyan]bobreview[/cyan] --plugin [magenta]<name>[/magenta] --dir [cyan]<path>[/cyan]"
    )
    console.print()
    
    # Core options
    core_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    core_table.add_column("Option", style="cyan", width=28)
    core_table.add_column("Description")
    core_table.add_row("--plugin <name>", "Plugin to use (required for reports)")
    core_table.add_row("--dir <path>", "Data directory (default: current directory)")
    core_table.add_row("--output <file>", "Output path (parent dir used, default: report.html)")
    core_table.add_row("--config <file>", "Custom report config YAML file")
    core_table.add_row("--dry-run", "Skip LLM API calls (for testing)")
    console.print(Panel(core_table, title="[bold]Core Options[/bold]", border_style="dim"))
    
    # Discovery commands (including how to make a folder a plugin folder)
    discover_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    discover_table.add_column("Option", style="cyan", width=28)
    discover_table.add_column("Description")
    discover_table.add_row("--list-plugins", "Show available plugins")
    discover_table.add_row(
        "--plugin-dir <dir>",
        "Add custom directory to plugin search path (repeatable, e.g., ./plugins)"
    )
    console.print(Panel(discover_table, title="[bold]Discovery[/bold]", border_style="dim"))
    
    # Plugin management commands
    plugin_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    plugin_table.add_column("Command", style="cyan", width=28)
    plugin_table.add_column("Description")
    plugin_table.add_row("plugins list", "Show installed plugins")
    plugin_table.add_row("plugins list --verbose", "Show plugins with detailed info")
    plugin_table.add_row("plugins create <name>", "Scaffold a new plugin")
    plugin_table.add_row("plugins info <name>", "Show plugin details")
    console.print(Panel(plugin_table, title="[bold]Plugin Management[/bold]", border_style="dim"))
    
    # Plugin create options
    create_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    create_table.add_column("Option", style="cyan", width=28)
    create_table.add_column("Description")
    create_table.add_row("--output-dir, -o <dir>", "Where to create (default: ~/.bobreview/plugins/)")
    create_table.add_row("--template, -t <type>", "Template: minimal or full (default: full)")
    console.print(Panel(create_table, title="[bold]Plugin Create Options[/bold]", border_style="dim"))
    
    # LLM Configuration
    llm_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    llm_table.add_column("Option", style="cyan", width=28)
    llm_table.add_column("Description")
    llm_table.add_row("--llm-provider <name>", "openai, anthropic, ollama (default: openai)")
    llm_table.add_row("--llm-api-key <key>", "API key (or use environment variable)")
    llm_table.add_row("--llm-model <model>", "Model name (e.g., gpt-4, llama2)")
    llm_table.add_row("--llm-temperature <0-2>", "Creativity level (default: 0.7)")
    console.print(Panel(llm_table, title="[bold]LLM Configuration[/bold]", border_style="dim"))
    
    # Output & debugging
    output_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    output_table.add_column("Option", style="cyan", width=28)
    output_table.add_column("Description")
    output_table.add_row("--verbose, -v", "Enable verbose debug output")
    output_table.add_row("--quiet, -q", "Errors only (suppress info/warnings)")
    output_table.add_row("--version", "Show version and exit")
    console.print(Panel(output_table, title="[bold]Output & Debugging[/bold]", border_style="dim"))
    
    # Examples (with colored commands and subcommands)
    examples_text = """[dim]# List plugins[/dim]
[cyan]bobreview[/cyan] [magenta]plugins[/magenta] list

[dim]# Create a plugin[/dim]
[cyan]bobreview[/cyan] [magenta]plugins[/magenta] [green]create[/green] my-plugin --template full

[dim]# Generate report[/dim]
[cyan]bobreview[/cyan] --plugin [magenta]my-plugin[/magenta] --dir [cyan]./data[/cyan] --output [cyan]./report.html[/cyan]

[dim]# Dry run (skip LLM calls)[/dim]
[cyan]bobreview[/cyan] --plugin [magenta]my-plugin[/magenta] --dir [cyan]./data[/cyan] --dry-run"""
    console.print(Panel(examples_text, title="[bold yellow]Examples[/bold yellow]", border_style="dim"))
    console.print()
    
    console.print("[dim]Full argparse help: bobreview --help --verbose[/dim]")
    console.print()
    
    return True


def handle_plugin_command(args):
    """Handle plugin subcommands."""
    dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=getattr(args, 'plugin_dirs', []))
    loader = init_loader(dirs)
    loader.discover()
    
    if args.plugin_command == 'list':
        plugins = loader.get_discovered_plugins()
        if not plugins:
            if RICH_AVAILABLE:
                console.print("[dim]No plugins found.[/dim]")
                console.print(f"\n[dim]Plugin directories searched:[/dim]")
                for d in dirs:
                    console.print(f"  [cyan]•[/cyan] {d}")
                console.print("\n[dim]To create a plugin:[/dim] bobreview plugins create my-plugin")
            else:
                print("No plugins found.")
                print("\nPlugin directories searched:")
                for d in dirs:
                    print(f"  - {d}")
            return 0
        
        if RICH_AVAILABLE:
            title = "Installed Plugins"
            if getattr(args, "verbose", False):
                title = "Installed Plugins (detailed)"

            table = Table(title=title, box=box.ROUNDED, border_style="cyan")
            table.add_column("Plugin", style="bold")
            table.add_column("Version", style="dim")
            table.add_column("Status", justify="center")
            if getattr(args, "verbose", False):
                table.add_column("Path", overflow="fold")
            
            for p in plugins:
                status = "[green]loaded[/green]" if p.loaded else "[dim]available[/dim]"
                if getattr(args, "verbose", False):
                    table.add_row(p.name, p.version, status, str(p.path))
                else:
                    table.add_row(p.name, p.version, status)
            
            console.print()
            console.print(table)
            console.print()
        else:
            print("Installed plugins:\n")
            for p in plugins:
                status = "loaded" if p.loaded else "available"
                line = f"  {p.name} v{p.version} [{status}]"
                if getattr(args, "verbose", False):
                    line += f" - {p.path}"
                print(line)
        return 0
    
    elif args.plugin_command == 'create':
        from .core.plugin_system.scaffolder.core import create_plugin
        
        if args.output_dir:
            output_dir = Path(args.output_dir).expanduser().resolve()
        else:
            output_dir = Path.home() / ".bobreview" / "plugins"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        plugin_dir = output_dir / args.name.replace('-', '_')
        if plugin_dir.exists():
            print(f"Error: Plugin directory already exists: {plugin_dir}")
            return 1
        
        try:
            created_path = create_plugin(args.name, output_dir, args.template)
            print(f"Created plugin: {args.name}")
            print(f"  Location: {created_path}")
            print(f"  Template: {args.template}")
            
            # Auto-register custom output directory
            if args.output_dir:
                user_plugins = PluginDiscovery.get_user_plugins_dir()
                local_plugins = PluginDiscovery.get_local_plugins_dir()
                
                # Only register if it's not a default location
                if output_dir != user_plugins and output_dir != local_plugins:
                    if PluginDiscovery.add_plugin_dir_to_config(output_dir):
                        print(f"  ✓ Registered {output_dir} for auto-discovery")
                    else:
                        print(f"  Note: Use --plugin-dir {output_dir} to include this location")
            
            print()
            print("Next steps:")
            print(f"  1. Edit {created_path}/manifest.json")
            print("  2. Modify parsers for your data format")
            print(f"  3. Test with: bobreview --plugin {args.name} --dir {created_path}/sample_data")
            return 0
        except (OSError, ValueError, RuntimeError) as e:
            print(f"Error creating plugin: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
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
        
        if RICH_AVAILABLE:
            info_lines = []
            info_lines.append(f"[bold]Version:[/bold] {found.version}")
            info_lines.append(f"[bold]Author:[/bold] {found.author or 'Unknown'}")
            info_lines.append(f"[bold]Description:[/bold] {found.description or 'No description'}")
            info_lines.append(f"[bold]Path:[/bold] {found.path}")
            status = "[green]loaded[/green]" if found.loaded else "[dim]not loaded[/dim]"
            info_lines.append(f"[bold]Status:[/bold] {status}")
            
            console.print()
            console.print(Panel(
                "\n".join(info_lines),
                title=f"[bold cyan]{found.name}[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
            ))
            console.print()
        else:
            print(f"Plugin: {found.name}")
            print(f"  Version: {found.version}")
            print(f"  Author: {found.author}")
            print(f"  Description: {found.description}")
            print(f"  Path: {found.path}")
            print(f"  Status: {'loaded' if found.loaded else 'not loaded'}")
        return 0
    
    else:
        print("Usage: bobreview plugins <list|create|info>")
        return 1


def main():
    """
    Parse CLI arguments and manage plugins.
    
    Plugin-First Architecture:
    - Core CLI is minimal - just plugin management
    - Report generation will be handled by plugins
    
    Returns:
        exit_code (int): 0 on success, 1 on failure.
    """
    # Show rich help for --help (intercept before argparse)
    if '--help' in sys.argv or '-h' in sys.argv:
        # Check if --verbose is also passed for full argparse help
        if '--verbose' not in sys.argv and '-v' not in sys.argv:
            if print_rich_help():
                return 0
    
    parser = argparse.ArgumentParser(
        prog='bobreview',
        description='BobReview - Plugin-First Report Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Plugin management:
    bobreview plugins list
    bobreview plugins list --verbose
    bobreview plugins create my-plugin
    bobreview plugins info my-plugin
  
  Report generation (via plugin):
    bobreview --plugin <plugin-name> --dir ./data
    bobreview --plugin <plugin-name> --dir ./data --dry-run
    bobreview --plugin <plugin-name> --dir ./data --config ./report_config.yaml

Notes:
  - Use --verbose/-v for debug output.
  - Use --quiet/-q for errors only (suppresses info/warnings).
  - The --output path controls the output *directory*; plugins typically
    write an 'index.html' file inside that directory.
        """
    )
    
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose debug output'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Errors only (suppress info and warnings)'
    )
    
    # Plugin directories
    parser.add_argument(
        '--plugin-dir', action='append', dest='plugin_dirs', default=[],
        metavar='DIR',
        help='Extra plugin search directory (repeatable)'
    )
    
    # Plugin selection (for future)
    parser.add_argument(
        '--plugin', type=str, required=False,
        metavar='PLUGIN_NAME',
        help='Plugin to use (see --list-plugins)'
    )
    parser.add_argument(
        '--dir', type=str, default='.',
        help='Data directory (default: current directory)'
    )
    parser.add_argument(
        '--output', type=str, default='report.html',
        help='Output path whose parent directory will be used for the report (HTML is usually written as index.html)'
    )
    parser.add_argument(
        '--config', '-c', type=str, default=None,
        metavar='YAML_PATH',
        help='Path to custom report config YAML'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Skip LLM API calls (for testing)'
    )
    
    # LLM Configuration
    parser.add_argument(
        '--llm-provider', type=str, default='openai',
        choices=['openai', 'anthropic', 'ollama'],
        help='LLM provider: openai, anthropic, ollama (default: openai)'
    )
    parser.add_argument(
        '--llm-api-key', type=str, default=None,
        metavar='KEY',
        help='API key for LLM provider (or use environment variable)'
    )
    parser.add_argument(
        '--llm-model', type=str, default=None,
        metavar='MODEL',
        help='LLM model name (e.g., gpt-4, claude-3-opus, llama2)'
    )
    parser.add_argument(
        '--llm-temperature', type=float, default=0.7,
        metavar='TEMP',
        help='LLM temperature 0.0-2.0 (default: 0.7)'
    )
    
    # Discovery
    parser.add_argument(
        '--list-plugins', action='store_true',
        help='Show available plugins'
    )
    
    # Plugin subcommands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    plugins_parser = subparsers.add_parser('plugins', help='Plugin management')
    plugins_parser.add_argument(
        '--plugin-dir', action='append', dest='plugin_dirs', default=[],
        metavar='DIR',
        help='Extra plugin search directory (repeatable)'
    )
    plugins_subparsers = plugins_parser.add_subparsers(dest='plugin_command')
    
    plugins_list = plugins_subparsers.add_parser('list', help='Show installed plugins')
    plugins_list.add_argument('--verbose', '-v', action='store_true', help='Include details')
    
    plugins_info = plugins_subparsers.add_parser('info', help='Show plugin info')
    plugins_info.add_argument('name', help='Plugin name')
    
    plugins_create = plugins_subparsers.add_parser('create', help='Scaffold a new plugin')
    plugins_create.add_argument('name', help='Plugin name (e.g. my-plugin)')
    plugins_create.add_argument('--output-dir', '-o', type=str, default=None,
                                help='Where to create (default: ~/.bobreview/plugins/)')
    plugins_create.add_argument('--template', '-t', type=str, default='full',
                                choices=['minimal', 'full'],
                                help='minimal = basic, full = all features (default)')
    
    # GUI subcommand
    gui_parser = subparsers.add_parser('gui', help='Launch graphical interface')
    
    args = parser.parse_args()

    # Build a simple Config object so logging respects --verbose/--quiet/--dry-run
    cli_config = Config()
    cli_config.verbose = bool(getattr(args, "verbose", False))
    cli_config.quiet = bool(getattr(args, "quiet", False))
    cli_config.dry_run = bool(getattr(args, "dry_run", False))
    
    # Auto-register any --plugin-dir paths to config for persistence
    plugin_dirs = getattr(args, 'plugin_dirs', [])
    for dir_path in plugin_dirs:
        resolved = Path(dir_path).expanduser().resolve()
        if resolved.exists() and resolved.is_dir():
            if PluginDiscovery.add_plugin_dir_to_config(resolved):
                log_verbose(f"Registered plugin directory: {resolved}", config=cli_config)
    
    # Handle --list-plugins
    if args.list_plugins:
        dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=args.plugin_dirs)
        loader = init_loader(dirs)
        loader.discover()
        plugins = loader.get_discovered_plugins()
        
        if not plugins:
            print("No plugins found.")
            print("\nTo create a plugin: bobreview plugins create my-plugin")
            return 0
        
        if RICH_AVAILABLE:
            table = Table(title="Available Plugins", box=box.ROUNDED, border_style="cyan")
            table.add_column("Plugin", style="bold")
            table.add_column("Version", style="dim")
            table.add_column("Description")
            
            for p in plugins:
                table.add_row(p.name, p.version, p.description or "")
            
            console.print()
            console.print(table)
            console.print()
        else:
            print("Available plugins:\n")
            for p in plugins:
                print(f"  {p.name} v{p.version}")
                if p.description:
                    print(f"    {p.description}")
        return 0
    
    # Handle GUI command
    if args.command == 'gui':
        try:
            from .gui import run_app
            run_app()
            return 0
        except ImportError as e:
            log_error(f"GUI requires flet. Install with: pip install flet")
            if args.verbose:
                print(f"Import error: {e}")
            return 1
    
    # Handle plugin subcommands
    if args.command == 'plugins':
        return handle_plugin_command(args)
    
    # Handle --plugin flag - Execute plugin's report generation
    if args.plugin:
        # Initialize plugin system
        dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=args.plugin_dirs)
        loader = init_loader(dirs)
        loader.discover()
        
        # Find and load the specified plugin
        plugins = loader.get_discovered_plugins()
        found = None
        for p in plugins:
            if p.name == args.plugin or p.name.replace('_', '-') == args.plugin:
                found = p
                break
        
        if not found:
            log_error(f"Plugin '{args.plugin}' not found.")
            print("\nAvailable plugins:")
            for p in plugins:
                print(f"  - {p.name}")
            if not plugins:
                print("  (none - use 'bobreview plugins create <name>' to create one)")
            return 1
        
        # Load plugin if not already loaded
        if not found.loaded:
            try:
                plugin_instance = loader.load(found.name)
            except PluginLoadError as e:
                log_error(f"Failed to load plugin '{found.name}': {e}")
                return 1
        else:
            # Get already loaded plugin instance
            plugin_instance = loader.get_loaded_plugin(found.name)
        
        if not plugin_instance:
            log_error(f"Plugin '{found.name}' loaded but no instance available.")
            return 1
        
        # Look for generate_report function in the plugin module
        safe_name = found.name.replace('-', '_')
        plugin_module = None
        for mod_name in [f"bobreview.plugins.{safe_name}", f"plugins.{safe_name}", safe_name, f"user_plugins.{safe_name}"]:
            if mod_name in sys.modules:
                plugin_module = sys.modules[mod_name]
                break
        
        data_dir = Path(args.dir)
        output_path = Path(args.output)

        # Basic validation for data directory
        if not data_dir.exists() or not data_dir.is_dir():
            log_error(f"Data directory does not exist or is not a directory: {data_dir}")
            return 1
        
        def call_generate_report(generate_func, name_desc):
            """Helper to call generate_report with consistent error handling."""
            log_info(f"Running plugin: {found.name} ({name_desc})", config=cli_config)
            log_info(f"Data directory: {data_dir}", config=cli_config)
            # We log the full output path for user visibility, but pass the parent
            # directory to the plugin's generate_report implementation.
            log_info(f"Output: {output_path}", config=cli_config)
            if args.dry_run:
                log_info("Dry run mode - LLM calls will be skipped", config=cli_config)

            # Build kwargs in a backwards-compatible way – only pass config_path
            # when the user provided --config, to avoid surprising plugins that
            # do not accept this parameter.
            kwargs = {
                "dry_run": getattr(args, "dry_run", False),
            }
            if getattr(args, "config", None):
                kwargs["config_path"] = args.config
            
            # LLM configuration - pass if specified
            if getattr(args, "llm_provider", None):
                kwargs["llm_provider"] = args.llm_provider
            if getattr(args, "llm_api_key", None):
                kwargs["llm_api_key"] = args.llm_api_key
            if getattr(args, "llm_model", None):
                kwargs["llm_model"] = args.llm_model
            if getattr(args, "llm_temperature", None) is not None:
                kwargs["llm_temperature"] = args.llm_temperature

            try:
                result = generate_func(
                    str(data_dir),
                    str(output_path.parent),
                    **kwargs,
                )
                log_success(f"Report generated: {result}", config=cli_config)
                return True, 0
            except (PluginLoadError, ValueError, OSError) as e:
                log_error(f"Report generation failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                return True, 1
        
        # Method 1: Check if plugin module has generate_report function
        if plugin_module and hasattr(plugin_module, 'generate_report'):
            handled, code = call_generate_report(plugin_module.generate_report, "module-level")
            if handled:
                return code
        
        # Method 2: Check if plugin instance has generate_report method
        if hasattr(plugin_instance, 'generate_report'):
            handled, code = call_generate_report(plugin_instance.generate_report, "instance-level")
            if handled:
                return code
        
        # No generate_report found
        log_warning(f"Plugin '{found.name}' does not have a generate_report function.", config=cli_config)
        print("\nTo add report generation, implement one of:")
        print(f"  1. A 'generate_report(data_dir, output_dir)' function in plugins/{found.name.replace('-', '_')}/__init__.py")
        print("  2. A 'generate_report(data_dir, output_dir)' method in your plugin class")
        print("\nSee the scaffolder-generated executor.py for an example.")
        return 1
    
    # Show help if no command
    if not args.command:
        print_banner()
        parser.print_help()
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

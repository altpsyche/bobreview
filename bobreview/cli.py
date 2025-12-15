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
from .core import Config, log_info, log_success, log_warning, log_error, log_verbose, format_number
from .core import init_cache, get_cache

# Import report systems framework
from .engine import load_report_system, list_available_systems
from .engine.executor import ReportSystemExecutor

# Import provider listing
from .services.llm.providers import list_providers, get_provider_info

# Import plugin system
from .core.plugin_system import get_loader, init_loader, PluginDiscovery, PluginManifest, PluginLoadError

# Import template engine
from .core.template_engine import reset_template_engine

# Import rich for beautiful CLI output
try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
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
    title.append(f" v{__version__}", style="dim")
    
    console.print()
    console.print(Panel(
        title,
        subtitle="[dim]Extensible Report Generation Framework[/dim]",
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
Generate beautiful HTML reports from any data using **LLM-powered analysis**.

- **Extensible** - Create plugins for any data format  
- **Themeable** - 7 built-in themes or create your own
- **Multi-LLM** - OpenAI, Anthropic Claude, or local Ollama
""")
    console.print(intro)
    console.print()
    
    # Quick start
    console.print("[bold cyan]Quick Start[/bold cyan]")
    console.print("  [dim]Create:[/dim]  bobreview plugins create [cyan]<name>[/cyan]")
    console.print("  [dim]Use:[/dim]     bobreview --plugin [cyan]<name>[/cyan] --dir [cyan]<path>[/cyan]")
    console.print()
    
    # Core options
    core_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    core_table.add_column("Option", style="cyan", width=25)
    core_table.add_column("Description")
    core_table.add_row("--plugin <name>", "Plugin to use (required)")
    core_table.add_row("--dir <path>", "Data directory (default: .)")
    core_table.add_row("--output <file>", "Output file (default: report.html)")
    core_table.add_row("--title <text>", "Custom report title")
    core_table.add_row("--theme <id>", "Color theme (use --list-themes)")
    console.print(Panel(core_table, title="[bold]Core Options[/bold]", border_style="dim"))
    
    # LLM options
    llm_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    llm_table.add_column("Option", style="cyan", width=25)
    llm_table.add_column("Description")
    llm_table.add_row("--llm-provider <name>", "openai, anthropic, or ollama")
    llm_table.add_row("--llm-model <model>", "Model name (provider default)")
    llm_table.add_row("--llm-api-key <key>", "API key (or use env vars)")
    llm_table.add_row("--llm-temperature <n>", "Creativity 0.0-2.0 (default: 0.7)")
    llm_table.add_row("--dry-run", "Skip LLM calls (placeholder content)")
    console.print(Panel(llm_table, title="[bold]LLM Options[/bold]", border_style="dim"))
    
    # Discovery commands
    discover_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    discover_table.add_column("Option", style="cyan", width=25)
    discover_table.add_column("Description")
    discover_table.add_row("--list-plugins", "Show available plugins")
    discover_table.add_row("--list-themes", "Show available themes")
    discover_table.add_row("--list-providers", "Show available LLM providers")
    discover_table.add_row("--list-report-systems", "Show available report systems")
    console.print(Panel(discover_table, title="[bold]Discovery[/bold]", border_style="dim"))
    
    # Plugin management
    plugin_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    plugin_table.add_column("Command", style="cyan", width=25)
    plugin_table.add_column("Description")
    plugin_table.add_row("plugins create <name>", "Scaffold a new plugin")
    plugin_table.add_row("plugins list", "Show installed plugins")
    plugin_table.add_row("plugins info <name>", "Show plugin details")
    console.print(Panel(plugin_table, title="[bold]Plugin Management[/bold]", border_style="dim"))
    
    # Other options
    console.print("[dim]Other: --verbose, --quiet, --no-cache, --sample <n>, --version[/dim]")
    console.print()
    console.print("[dim]Full help: bobreview --help --verbose[/dim]")
    console.print()
    
    return True


def handle_doctor_command(extra_dirs=None):
    """Run diagnostic checks on BobReview setup."""
    if RICH_AVAILABLE:
        from rich.markdown import Markdown
        
        print_banner()
        console.print()
        console.print("[bold]System Check[/bold]")
        console.print()
        
        checks = []
        all_ok = True
        
        # Python version
        import sys
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_ok = sys.version_info >= (3, 10)
        checks.append(("Python", py_version, py_ok, "3.10+ required" if not py_ok else ""))
        
        # Rich library
        checks.append(("Rich library", "installed", True, ""))
        
        # API Keys
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        if openai_key:
            checks.append(("OpenAI API Key", f"...{openai_key[-4:]}", True, ""))
        else:
            checks.append(("OpenAI API Key", "not set", False, "Set OPENAI_API_KEY env var"))
        
        if anthropic_key:
            checks.append(("Anthropic API Key", f"...{anthropic_key[-4:]}", True, ""))
        else:
            checks.append(("Anthropic API Key", "not set", False, "Set ANTHROPIC_API_KEY env var"))
        
        # Plugin directories
        plugin_dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=extra_dirs)
        existing_dirs = [d for d in plugin_dirs if Path(d).exists()]
        checks.append(("Plugin directories", f"{len(existing_dirs)} found", len(existing_dirs) > 0, ""))
        
        # Plugins
        loader = init_loader(plugin_dirs)
        plugins = loader.discover()
        checks.append(("Plugins discovered", str(len(plugins)), True, ""))
        
        # Display results
        table = Table(box=box.ROUNDED, border_style="cyan", show_header=False)
        table.add_column("Check", style="bold", width=20)
        table.add_column("Status", width=20)
        table.add_column("Result", justify="center", width=8)
        table.add_column("Note", style="dim")
        
        for check, status, ok, note in checks:
            result = "[green]OK[/green]" if ok else "[yellow]--[/yellow]"
            if not ok:
                all_ok = False
            table.add_row(check, status, result, note)
        
        console.print(table)
        console.print()
        
        if all_ok:
            console.print("[green]All checks passed![/green]")
        else:
            console.print("[yellow]Some checks need attention.[/yellow]")
            console.print("[dim]Note: API keys are optional if using --dry-run or Ollama.[/dim]")
        
        console.print()
        return 0
    else:
        print("Doctor requires 'rich' library: pip install rich")
        return 1


def _load_plugins(extra_dirs, config):
    """
    Load plugins from discovered directories.
    
    Uses PluginDiscovery to find plugins from:
    1. CLI --plugin-dirs
    2. BOBREVIEW_PLUGIN_DIRS environment variable
    3. ~/.bobreview/plugins/
    4. ./plugins/
    5. Bundled plugins (shipped with package)
    """
    dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=extra_dirs)
    
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
    # Initialize loader with discovered directories (respecting --plugin-dirs)
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
                console.print("\n[dim]To add plugins:[/dim] bobreview plugins create my-plugin")
            else:
                print("No plugins found.")
                print(f"\nPlugin directories searched:")
                for d in dirs:
                    print(f"  - {d}")
                print("\nTo add plugins, place them in ~/.bobreview/plugins/")
            return 0
        
        if RICH_AVAILABLE:
            table = Table(title="Installed Plugins", box=box.ROUNDED, border_style="cyan")
            table.add_column("Plugin", style="bold")
            table.add_column("Version", style="dim")
            table.add_column("Status", justify="center")
            if args.verbose:
                table.add_column("Author")
                table.add_column("Components")
            
            for p in plugins:
                status = "[green]✓ loaded[/green]" if p.loaded else "[dim]○ available[/dim]"
                if args.verbose:
                    provides_str = ", ".join(f"{k}:{len(v)}" for k, v in p.provides.items()) if p.provides else ""
                    table.add_row(p.name, p.version, status, p.author or "", provides_str)
                else:
                    table.add_row(p.name, p.version, status)
            
            console.print()
            console.print(table)
            console.print()
        else:
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
        
        manifest = PluginManifest.from_file(manifest_path)
        print(f"  Name: {manifest.name} v{manifest.version}")
        print(f"  Author: {manifest.author}")
        return 0
    
    elif args.plugin_command == 'uninstall':
        user_plugins = (Path.home() / ".bobreview" / "plugins").resolve()
        
        # Find the plugin
        found = None
        for p in loader.get_discovered_plugins():
            if p.name == args.name and p.path:
                found = Path(p.path).expanduser().resolve()
                break
        
        if not found:
            print(f"Error: Plugin not found: {args.name}")
            return 1
        
        # Only allow uninstalling from user directory
        # Use resolved paths to prevent path traversal via .. components
        if not found.is_relative_to(user_plugins):
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
            if RICH_AVAILABLE:
                console.print(f"[red]✗[/red] Plugin not found: {args.name}")
            else:
                print(f"Plugin not found: {args.name}")
            return 1
        
        if RICH_AVAILABLE:
            # Build info content
            info_lines = []
            info_lines.append(f"[bold]Version:[/bold] {found.version}")
            info_lines.append(f"[bold]Author:[/bold] {found.author or 'Unknown'}")
            info_lines.append(f"[bold]Description:[/bold] {found.description or 'No description'}")
            info_lines.append(f"[bold]Path:[/bold] {found.path}")
            status = "[green]✓ loaded[/green]" if found.loaded else "[dim]○ not loaded[/dim]"
            info_lines.append(f"[bold]Status:[/bold] {status}")
            
            if found.dependencies:
                info_lines.append(f"[bold]Dependencies:[/bold] {', '.join(found.dependencies)}")
            
            if found.provides:
                provides_lines = []
                for ext_type, items in found.provides.items():
                    provides_lines.append(f"  {ext_type}: {', '.join(items)}")
                info_lines.append(f"[bold]Provides:[/bold]\n" + "\n".join(provides_lines))
            
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
            if found.dependencies:
                print(f"  Dependencies: {', '.join(found.dependencies)}")
            if found.provides:
                print("  Provides:")
                for ext_type, items in found.provides.items():
                    print(f"    {ext_type}: {', '.join(items)}")
        return 0
    
    elif args.plugin_command == 'create':
        from .core.plugin_system.scaffolder.core import create_plugin
        
        # Determine output directory
        if args.output_dir:
            output_dir = Path(args.output_dir).expanduser().resolve()
        else:
            output_dir = Path.home() / ".bobreview" / "plugins"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if plugin already exists
        plugin_dir = output_dir / args.name.replace('-', '_')
        if plugin_dir.exists():
            print(f"Error: Plugin directory already exists: {plugin_dir}")
            return 1
        
        # Create the plugin
        try:
            color_theme = getattr(args, 'theme', 'dark')
            created_path = create_plugin(args.name, output_dir, args.template, color_theme)
            print(f"✓ Created plugin: {args.name}")
            print(f"  Location: {created_path}")
            print(f"  Template: {args.template}")
            print(f"  Theme: {color_theme}")
            print()
            print("Next steps:")
            print(f"  1. Edit {created_path}/manifest.json to update author and description")
            print(f"  2. Modify parsers/csv_parser.py for your data format")
            print(f"  3. Change theme in report_systems/{args.name.replace('-', '_')}.json (theme.preset)")
            print(f"  4. Test with: bobreview --plugin {args.name} --dir {created_path}/sample_data")
            return 0
        except Exception as e:
            print(f"Error creating plugin: {e}")
            return 1
    
    else:
        print("Usage: bob plugins <list|install|uninstall|info|create>")
        return 1


def main():
    """
    Parse CLI arguments and generate reports using plugins.
    
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
        description='BobReview - Extensible Report Generation Framework',
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

  # Create a new plugin from template
  bobreview plugins create my-plugin
  bobreview plugins create my-plugin --template minimal

  # List available LLM providers
  bobreview --list-providers
        """
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--dir', type=str, default='.',
        help='Directory containing data files to analyze (default: current directory)'
    )
    parser.add_argument(
        '--output', type=str, default='report.html',
        help='Output file path for generated report (default: report.html)'
    )
    parser.add_argument(
        '--title', type=str, default=None,
        help='Custom report title'
    )
    
    parser.add_argument(
        '--no-recommendations', action='store_true',
        help='Skip LLM recommendations section'
    )
    
    # LLM Provider arguments (unified)
    parser.add_argument(
        '--llm-provider', type=str, default='openai',
        choices=['openai', 'anthropic', 'ollama'],
        help='LLM provider (default: openai)'
    )
    parser.add_argument(
        '--llm-api-key', type=str, default=None,
        help='API key (or use OPENAI_API_KEY / ANTHROPIC_API_KEY env vars)'
    )
    parser.add_argument(
        '--llm-api-base', type=str, default=None,
        help='Custom API endpoint (for Ollama: http://localhost:11434)'
    )
    parser.add_argument(
        '--llm-model', type=str, default=None,
        help='Model name (defaults: gpt-4o, claude-3-5-sonnet, llama2)'
    )
    parser.add_argument(
        '--llm-temperature', type=float, default=0.7,
        help='Creativity (0.0-2.0, default: 0.7)'
    )
    parser.add_argument(
        '--llm-max-tokens', type=int, default=2000,
        help='Max response tokens (default: 2000)'
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
        help='Show available LLM providers'
    )
    
    # Caching options
    parser.add_argument(
        '--cache-dir', type=str, default='.bobreview_cache',
        help='Cache directory (default: .bobreview_cache)'
    )
    parser.add_argument(
        '--use-cache', action='store_true', default=True,
        help='Enable response caching (default)'
    )
    parser.add_argument(
        '--no-cache', action='store_false', dest='use_cache',
        help='Disable caching, always call LLM'
    )
    parser.add_argument(
        '--clear-cache', action='store_true',
        help='Clear cache before running'
    )
    
    # Execution options
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Skip LLM calls (placeholder content)'
    )
    parser.add_argument(
        '--sample', type=int, default=None, dest='sample_size',
        help='Process only N random samples'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show debug information'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Errors only'
    )
    parser.add_argument(
        '--no-embed-images', action='store_false', dest='embed_images', default=True,
        help='Link to images instead of embedding'
    )
    parser.add_argument(
        '--linked-css', action='store_true', default=False,
        help='Link to CSS instead of embedding'
    )
    parser.add_argument(
        '--theme', type=str, default=None, dest='theme_id',
        # Note: No choices restriction - plugins can register custom themes
        # Built-in: dark, light, high_contrast, ocean, purple, terminal, sunset
        # Plugin themes are validated at runtime after plugins are loaded
        help='Color theme (dark, ocean, purple, terminal, sunset, light, high_contrast)'
    )
    parser.add_argument(
        '--disable-page', action='append', dest='disabled_pages', default=[],
        metavar='PAGE_ID',
        help='Exclude page by ID (repeatable)'
    )
    # Plugin and report system selection
    parser.add_argument(
        '--plugin', type=str, required=False,
        metavar='PLUGIN_NAME',
        help='Plugin to use (see --list-plugins)'
    )
    parser.add_argument(
        '--report-system', type=str, default=None,
        metavar='SYSTEM',
        help='Report system ID (required if plugin has multiple)'
    )
    parser.add_argument(
        '--list-report-systems', action='store_true',
        help='Show available report systems'
    )
    parser.add_argument(
        '--list-plugins', action='store_true',
        help='Show available plugins'
    )
    parser.add_argument(
        '--list-themes', action='store_true',
        help='Show available color themes'
    )
    
    # Plugin arguments
    parser.add_argument(
        '--plugin-dir', action='append', dest='plugin_dirs', default=[],
        metavar='DIR',
        help='Extra plugin search directory (repeatable)'
    )
    # NOTE: --no-plugins was removed - plugins are now mandatory for report generation
    
    # Plugin subcommands
    subparsers = parser.add_subparsers(dest='command', help='Plugin management commands')
    
    # bob plugins list
    plugins_parser = subparsers.add_parser('plugins', help='Plugin management')
    plugins_subparsers = plugins_parser.add_subparsers(dest='plugin_command')
    
    plugins_list = plugins_subparsers.add_parser('list', help='Show installed plugins')
    plugins_list.add_argument('--verbose', '-v', action='store_true', help='Include details')
    
    plugins_install = plugins_subparsers.add_parser('install', help='Install a plugin from path')
    plugins_install.add_argument('path', help='Plugin directory path')
    
    plugins_uninstall = plugins_subparsers.add_parser('uninstall', help='Remove a plugin')
    plugins_uninstall.add_argument('name', help='Plugin name')
    
    plugins_info = plugins_subparsers.add_parser('info', help='Show plugin info')
    plugins_info.add_argument('name', help='Plugin name')
    
    plugins_create = plugins_subparsers.add_parser('create', help='Scaffold a new plugin')
    plugins_create.add_argument('name', help='Plugin name (e.g. my-plugin)')
    plugins_create.add_argument('--output-dir', '-o', type=str, default=None,
                                help='Where to create (default: ~/.bobreview/plugins/)')
    plugins_create.add_argument('--template', '-t', type=str, default='full',
                                choices=['minimal', 'full'],
                                help='minimal = basic, full = all features (default)')
    plugins_create.add_argument('--theme', type=str, default='dark',
                                choices=['dark', 'light', 'high_contrast', 'ocean', 'purple', 'terminal', 'sunset'],
                                help='Base color theme for templates (default: dark)')
    
    
    # build subcommand removed - use `bobreview --plugin <name> --dir <path>` instead
    # All report generation now goes through --plugin which uses ReportBuilder
    
    # validate command - validate a report config
    validate_parser = subparsers.add_parser('validate', help='Validate report config file')
    validate_parser.add_argument('config', help='Path to report config YAML')
    validate_parser.add_argument('--plugin-dir', action='append', dest='plugin_dirs', default=[],
                                help='Extra plugin directory')
    
    # doctor command
    doctor_parser = subparsers.add_parser('doctor', help='Check system setup')
    
    # Parse args
    args = parser.parse_args()
    
    # Handle --list-providers
    if args.list_providers:
        if RICH_AVAILABLE:
            table = Table(title="LLM Providers", box=box.ROUNDED, border_style="cyan")
            table.add_column("Provider", style="bold")
            table.add_column("Default Model")
            table.add_column("API Key", justify="center")
            
            for provider_name in list_providers():
                info = get_provider_info(provider_name)
                key_status = f"[yellow]{info['env_key_name']}[/yellow]" if info['requires_api_key'] else "[green]Not required[/green]"
                table.add_row(provider_name, info['default_model'], key_status)
            
            console.print()
            console.print(table)
            console.print()
        else:
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
            if RICH_AVAILABLE:
                console.print("[dim]No report systems found.[/dim]")
            else:
                print("No report systems found.")
            return 0
        
        if RICH_AVAILABLE:
            table = Table(title="Report Systems", box=box.ROUNDED, border_style="cyan")
            table.add_column("ID", style="bold")
            table.add_column("Version", style="dim")
            table.add_column("Source", justify="center")
            table.add_column("Description")
            
            for system in systems:
                source_label = "[green]built-in[/green]" if system['source'] == 'builtin' else "[yellow]plugin[/yellow]"
                table.add_row(system['id'], system['version'], source_label, system['description'] or "")
            
            console.print()
            console.print(table)
            console.print()
        else:
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
        dirs = PluginDiscovery.get_plugin_dirs(extra_dirs=getattr(args, 'plugin_dirs', []))
        loader = init_loader(dirs)
        loader.discover()
        plugins = loader.get_discovered_plugins()
        
        if not plugins:
            if RICH_AVAILABLE:
                console.print("[dim]No plugins found.[/dim]")
                console.print(f"\n[dim]Plugin directories searched:[/dim]")
                for d in dirs:
                    console.print(f"  [cyan]•[/cyan] {d}")
                console.print("\n[dim]To add plugins:[/dim] bobreview plugins create my-plugin")
            else:
                print("No plugins found.")
                print(f"\nPlugin directories searched:")
                for d in dirs:
                    print(f"  - {d}")
                print("\nTo add plugins, place them in ~/.bobreview/plugins/")
            return 0
        
        if RICH_AVAILABLE:
            table = Table(title="Available Plugins", box=box.ROUNDED, border_style="cyan")
            table.add_column("Plugin", style="bold")
            table.add_column("Version", style="dim")
            table.add_column("Status", justify="center")
            table.add_column("Author")
            table.add_column("Components")
            
            for p in plugins:
                status = "[green]✓ loaded[/green]" if p.loaded else "[dim]○ available[/dim]"
                provides_str = ", ".join(f"{k}:{len(v)}" for k, v in p.provides.items()) if p.provides else ""
                table.add_row(p.name, p.version, status, p.author or "", provides_str)
            
            console.print()
            console.print(table)
            console.print()
        else:
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
    
    # Handle --list-themes
    if args.list_themes:
        from .core.themes import BUILTIN_THEMES
        
        if RICH_AVAILABLE:
            table = Table(title="Available Themes", box=box.ROUNDED, border_style="cyan")
            table.add_column("Theme ID", style="bold")
            table.add_column("Name")
            table.add_column("Style")
            
            for theme in BUILTIN_THEMES:
                # Simple style indicator
                style_type = "dark" if "dark" in theme.id or theme.id in ["ocean", "purple", "terminal", "sunset"] else "light"
                if theme.id == "high_contrast":
                    style_type = "high contrast"
                table.add_row(theme.id, theme.name, style_type)
            
            console.print()
            console.print(table)
            console.print("\n[dim]Use --theme <id> to apply a theme[/dim]")
            console.print()
        else:
            print("Available themes:\n")
            for theme in BUILTIN_THEMES:
                print(f"  {theme.id} - {theme.name}")
            print("\nUse --theme <id> to apply a theme")
        return 0
    
    # Handle plugin commands
    if args.command == 'plugins':
        return handle_plugin_command(args)
    
    # Handle doctor command
    if args.command == 'doctor':
        return handle_doctor_command(extra_dirs=getattr(args, 'plugin_dirs', []))
    
    
    # build command removed - all report generation goes through --plugin
    
    # Handle validate command
    if args.command == 'validate':
        from .core.report_config import load_user_config, validate_user_config
        
        if RICH_AVAILABLE:
            console.print(f"[bold]Validating:[/bold] {args.config}")
        else:
            print(f"Validating: {args.config}")
        
        try:
            config = load_user_config(args.config)
            errors = validate_user_config(config)
            
            if errors:
                if RICH_AVAILABLE:
                    console.print("[red]✗ Validation failed:[/red]")
                    for err in errors:
                        console.print(f"  [red]•[/red] {err}")
                else:
                    print("✗ Validation failed:")
                    for err in errors:
                        print(f"  - {err}")
                return 1
            else:
                if RICH_AVAILABLE:
                    console.print("[green]✓ Config is valid[/green]")
                    console.print(f"  [dim]Name:[/dim] {config.name}")
                    console.print(f"  [dim]Plugin:[/dim] {config.plugin}")
                    console.print(f"  [dim]Pages:[/dim] {len(config.pages)}")
                else:
                    print("✓ Config is valid")
                    print(f"  Name: {config.name}")
                    print(f"  Plugin: {config.plugin}")
                    print(f"  Pages: {len(config.pages)}")
                return 0
        except FileNotFoundError as e:
            if RICH_AVAILABLE:
                console.print(f"[red]✗ File not found:[/red] {e}")
            else:
                print(f"✗ File not found: {e}")
            return 1
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]✗ Error:[/red] {e}")
            else:
                print(f"✗ Error: {e}")
            return 1

    
    # Validate that --plugin is provided if not using list commands
    if not args.plugin and not (args.list_plugins or args.list_report_systems or args.list_providers or args.list_themes):
        parser.error("--plugin is required (unless using a --list-* command)")
    
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
    
    # Build configuration using unified Config class
    # Extract directory and filename from --output (which is a file path)
    if hasattr(args, 'output') and args.output:
        output_path = Path(args.output)
        # If parent is current directory, use '.'; otherwise use the parent directory
        output_dir = str(output_path.parent) if output_path.parent != Path('.') else '.'
        output_filename = output_path.name
    else:
        output_dir = './output'
        output_filename = 'report.html'
    
    config = Config(
        title=args.title or "",
        llm_provider=args.llm_provider,
        llm_api_key=llm_api_key,
        llm_api_base=args.llm_api_base,
        llm_model=args.llm_model,
        llm_temperature=args.llm_temperature,
        llm_max_tokens=args.llm_max_tokens,
        llm_chunk_size=args.llm_chunk_size,
        theme=args.theme_id or 'dark',
        output_dir=output_dir,
        output_filename=output_filename,
        embed_images=args.embed_images,
        linked_css=args.linked_css,
        verbose=args.verbose,
        quiet=args.quiet,
        dry_run=args.dry_run,
        sample_size=args.sample_size,
        use_cache=args.use_cache and not args.dry_run,
        cache_dir=Path(args.cache_dir),
    )
    
    # Validate configuration
    validation_errors = config.validate()
    if validation_errors:
        log_error("Configuration validation failed:")
        for error in validation_errors:
            log_error(f"  - {error}")
        return 1
    
    # Initialize cache
    init_cache(config)
    
    # Clear cache if requested
    if args.clear_cache:
        cache = get_cache()
        if cache:
            cache.clear()
    
    if config.dry_run:
        log_warning("Running in DRY RUN mode - LLM calls will be skipped", config)
    
    log_verbose(f"LLM Provider: {config.llm_provider} (model: {config.llm_model})", config)
    
    # IMPORTANT: Plugins must be loaded BEFORE template engine is first accessed
    # to ensure plugin templates are available
    _load_plugins(args.plugin_dirs, config)
    
    # Refresh template engine to pick up plugin templates
    reset_template_engine()
    
    # Use the JSON-based report system framework
    try:
        # Plugin is required - determine which report system to use
        if args.report_system:
            # Explicit system specified - ensure the plugin is loaded first
            report_system_id = args.report_system
            plugin_manager = get_loader()
            if not plugin_manager.get_discovered_plugins():
                plugin_manager.discover()
            matched_manifest = None
            plugin_name_normalized = args.plugin.lower().replace('-', '_').replace(' ', '')
            for manifest in plugin_manager.get_discovered_plugins():
                manifest_name_normalized = manifest.name.lower().replace('-', '_').replace(' ', '')
                if manifest.name == args.plugin or manifest_name_normalized == plugin_name_normalized:
                    matched_manifest = manifest
                    break
            if matched_manifest and not plugin_manager.is_loaded(matched_manifest.name):
                try:
                    plugin_manager.load(matched_manifest.name)
                    log_info(f"Loaded plugin: {matched_manifest.name}", config)
                except PluginLoadError as e:
                    log_warning(f"Failed to load plugin '{matched_manifest.name}': {e}", config)
                args.plugin = matched_manifest.name
        else:
            # No explicit system - auto-select if only one, require selection if multiple
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
            
            # Load the plugin if found
            if matched_manifest:
                if not plugin_manager.is_loaded(matched_manifest.name):
                    try:
                        plugin_manager.load(matched_manifest.name)
                        log_info(f"Loaded plugin: {matched_manifest.name}", config)
                    except PluginLoadError as e:
                        log_warning(f"Failed to load plugin '{matched_manifest.name}': {e}", config)
                # Update args.plugin to the actual plugin name for consistency
                args.plugin = matched_manifest.name
            
            if plugin_path:
                # YAML config is required for report generation
                yaml_config = plugin_path / 'report_config.yaml'
                if yaml_config.exists():
                    log_info(f"Using config: {yaml_config}", config)
                    
                    # Use ReportBuilder for YAML-based generation
                    from .core.report_builder import get_report_builder
                    builder = get_report_builder()
                    
                    # Build with CLI overrides
                    result = builder.build(
                        config_path=str(yaml_config),
                        output_dir=str(Path(args.output).parent) if args.output else None,
                        dry_run=config.dry_run,
                        config=config,  # Pass CLI config for LLM, cache, etc.
                        input_dir=args.dir,  # Pass data directory
                        output_file=args.output  # Pass output filename
                    )
                    
                    if result['success']:
                        elapsed = time.time() - start_time
                        log_success(f"Report generated in {elapsed:.1f}s: {result.get('output_path', args.output)}", config)
                        return 0
                    else:
                        for err in result.get('errors', []):
                            log_error(err)
                        return 1
                else:
                    # YAML config required but not found
                    log_error(
                        f"Plugin '{args.plugin}' is missing report_config.yaml\n\n"
                        f"This file defines your report pages and components.\n"
                        f"Expected location: {yaml_config}\n\n"
                        f"To create one, run:\n"
                        f"  bobreview plugins create {args.plugin} --output-dir {plugin_path.parent}"
                    )
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
        
    except FileNotFoundError as e:
        log_error(str(e))
        return 1
    except ValueError as e:
        log_error(f"Report generation failed: {e}")
        return 1
    except Exception as e:
        log_error(f"Failed to generate report: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

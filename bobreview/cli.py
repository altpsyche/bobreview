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
from .data_parser import parse_filename

# Import report systems framework
from .report_systems import load_report_system, list_available_systems
from .report_systems.executor import ReportSystemExecutor

# Import provider listing
from .llm.providers import list_providers, get_provider_info

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
  # Basic usage with defaults (OpenAI)
  bobreview --dir ./screenshots

  # Use Anthropic Claude
  bobreview --dir ./screenshots --llm-provider anthropic --llm-model claude-3-sonnet-20240229

  # Use local Ollama
  bobreview --dir ./screenshots --llm-provider ollama --llm-model llama2

  # Custom thresholds and title
  bobreview --dir ./screenshots --title "My Level Analysis" \\
    --draw-hard-cap 700 --tri-hard-cap 150000 --location "City District"

  # Dry run to test without calling LLM
  bobreview --dir ./screenshots --dry-run

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
        help='Report title (default: "Performance Analysis Report")'
    )
    parser.add_argument(
        '--location', type=str, default=None,
        help='Location/level name (default: "Unknown Location")'
    )
    
    # Threshold arguments
    parser.add_argument(
        '--draw-soft-cap', type=int, default=550,
        help='Soft cap for draw calls (default: 550)'
    )
    parser.add_argument(
        '--draw-hard-cap', type=int, default=600,
        help='Hard cap for draw calls (default: 600)'
    )
    parser.add_argument(
        '--tri-soft-cap', type=int, default=100000,
        help='Soft cap for triangles (default: 100000)'
    )
    parser.add_argument(
        '--tri-hard-cap', type=int, default=120000,
        help='Hard cap for triangles (default: 120000)'
    )
    parser.add_argument(
        '--high-load-draws', type=int, default=None,
        help='High-load threshold for draw calls (default: same as draw-hard-cap)'
    )
    parser.add_argument(
        '--high-load-tris', type=int, default=None,
        help='High-load threshold for triangles (default: same as tri-hard-cap)'
    )
    parser.add_argument(
        '--low-load-draws', type=int, default=400,
        help='Low-load threshold for draw calls (default: 400)'
    )
    parser.add_argument(
        '--low-load-tris', type=int, default=50000,
        help='Low-load threshold for triangles (default: 50000)'
    )
    parser.add_argument(
        '--outlier-sigma', type=float, default=2.0,
        help='Sigma multiplier for outlier detection (default: 2.0)'
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
    parser.add_argument(
        '--report-system', type=str, default='png_data_points',
        metavar='SYSTEM',
        help='Report system to use (built-in name or path to JSON file)'
    )
    parser.add_argument(
        '--list-report-systems', action='store_true',
        help='List all available report systems and exit'
    )
    
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
    config = ReportConfig(
        title=args.title or "Performance Analysis Report",
        location=args.location or "Unknown Location",
        draw_soft_cap=args.draw_soft_cap,
        draw_hard_cap=args.draw_hard_cap,
        tri_soft_cap=args.tri_soft_cap,
        tri_hard_cap=args.tri_hard_cap,
        high_load_draw_threshold=args.high_load_draws or args.draw_hard_cap,
        high_load_tri_threshold=args.high_load_tris or args.tri_hard_cap,
        low_load_draw_threshold=args.low_load_draws,
        low_load_tri_threshold=args.low_load_tris,
        outlier_sigma=args.outlier_sigma,
        enable_recommendations=not args.no_recommendations,
        llm_provider=args.llm_provider,
        llm_api_key=llm_api_key,
        llm_api_base=args.llm_api_base,
        llm_model=args.llm_model,
        llm_temperature=args.llm_temperature,
        llm_max_tokens=args.llm_max_tokens,
        llm_chunk_size=args.llm_chunk_size,
        llm_combine_warning_threshold=args.llm_combine_warning_threshold,
        cache_dir=Path(args.cache_dir),
        use_cache=args.use_cache and not args.dry_run,
        clear_cache=args.clear_cache,
        dry_run=args.dry_run,
        sample_size=args.sample_size,
        verbose=args.verbose,
        quiet=args.quiet,
        embed_images=args.embed_images,
        linked_css=args.linked_css,
        theme_id=args.theme_id,
        disabled_pages=args.disabled_pages
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
    if config.clear_cache:
        cache = get_cache()
        if cache:
            cache.clear()
    
    if config.dry_run:
        log_warning("Running in DRY RUN mode - LLM calls will be skipped", config)
    
    log_verbose(f"LLM Provider: {config.llm_provider} (model: {config.llm_model})", config)
    
    # Use the JSON-based report system framework
    try:
        log_info(f"Loading report system: {args.report_system}", config)
        
        # Build CLI overrides for the JSON system
        cli_overrides = {
            'thresholds': {
                'draw_soft_cap': config.draw_soft_cap,
                'draw_hard_cap': config.draw_hard_cap,
                'tri_soft_cap': config.tri_soft_cap,
                'tri_hard_cap': config.tri_hard_cap,
                'high_load_draw_threshold': config.high_load_draw_threshold,
                'high_load_tri_threshold': config.high_load_tri_threshold,
                'low_load_draw_threshold': config.low_load_draw_threshold,
                'low_load_tri_threshold': config.low_load_tri_threshold,
                'outlier_sigma': config.outlier_sigma,
                'mad_threshold': config.mad_threshold,
            },
            'llm_config': {
                'provider': config.llm_provider,
                'model': config.llm_model,
                'temperature': config.llm_temperature,
                'max_tokens': config.llm_max_tokens,
                'chunk_size': config.llm_chunk_size,
                'enable_cache': config.use_cache,
            },
            'output': {
                'embed_images': config.embed_images,
                'linked_css': config.linked_css,
            },
            'theme': {
                'default': config.theme_id,
            },
            'disabled_pages': config.disabled_pages
        }
        
        # Load report system with CLI overrides
        system_def = load_report_system(args.report_system, cli_overrides=cli_overrides)
        
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
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

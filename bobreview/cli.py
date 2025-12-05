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
from .pages import generate_report

# Import report systems framework
from .report_systems import load_report_system, list_available_systems
from .report_systems.executor import ReportSystemExecutor

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
    
    This is the script entry point: it builds a ReportConfig from command-line options, validates configuration, initializes (and optionally clears) the LLM response cache, scans and parses PNG files whose filenames encode performance metrics, computes statistics, and generates an HTML report. Depending on options it may sample the input set, run in dry-run mode (skip LLM calls and use placeholder content), and use cached LLM responses. Errors during validation, parsing, analysis, LLM interaction, HTML generation, or file I/O cause a non-zero exit code; verbose and quiet flags control console output.
    
    Returns:
        exit_code (int): 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        prog='bobreview',
        description='BobReview - Performance Analysis and Review Tool for Game Development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults
  bobreview --dir ./screenshots

  # Custom thresholds and title
  bobreview --dir ./screenshots --title "My Level Analysis" \\
    --draw-hard-cap 700 --tri-hard-cap 150000 --location "City District"

  # Subsequent runs reuse cache automatically (enabled by default)
  bobreview --dir ./screenshots

  # Disable caching for this run
  bobreview --dir ./screenshots --no-cache

  # Dry run to test without calling LLM
  bobreview --dir ./screenshots --dry-run

  # Process only a random sample
  bobreview --dir ./screenshots --sample 50

  # Or set OPENAI_API_KEY environment variable
  export OPENAI_API_KEY=sk-...
  bobreview --dir ./screenshots

  # Clear cache and regenerate
  bobreview --dir ./screenshots --clear-cache

  # Use external image files (reduces HTML file size)
  bobreview --dir ./screenshots --no-embed-images
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
        help='Output directory/file path (creates index.html and additional pages, default: performance_report.html)'
    )
    parser.add_argument(
        '--images-dir', type=str, default=None,
        help='Relative path to images directory from output (auto-detected if not specified)'
    )
    parser.add_argument(
        '--title', type=str, default=None,
        help='Report title (default: "Performance Analysis Report")'
    )
    parser.add_argument(
        '--location', type=str, default=None,
        help='Location/level name (default: "Unknown Location")'
    )
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
    parser.add_argument(
        '--openai-key', type=str, default=None,
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )
    parser.add_argument(
        '--image-chunk-size', type=int, default=10,
        help='Number of data samples to send per LLM call (default: 10)'
    )
    parser.add_argument(
        '--openai-model', type=str, default='gpt-4o',
        help='OpenAI model to use (default: gpt-4o)'
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
        '--llm-combine-warning-threshold', type=int, default=100000,
        help='Character count threshold for warning when combining chunks (default: 100000, roughly 25K tokens). Advanced option.'
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
        help='Use external CSS file instead of embedding (creates styles.css in output directory)'
    )
    parser.add_argument(
        '--theme', type=str, default='dark', dest='theme_id',
        choices=['dark', 'light', 'high_contrast'],
        help='Report theme (default: dark). Options: dark, light, high_contrast'
    )
    parser.add_argument(
        '--disable-page', action='append', dest='disabled_pages', default=[],
        metavar='PAGE_ID',
        help='Disable a page by ID (can be used multiple times). Valid IDs: home, metrics, zones, visuals, optimization, stats'
    )
    parser.add_argument(
        '--report-system', type=str, default='png_data_points',
        metavar='SYSTEM',
        help='Report system to use (built-in name or path to JSON file). Default: png_data_points'
    )
    parser.add_argument(
        '--list-report-systems', action='store_true',
        help='List all available report systems and exit'
    )
    
    # Parse args but also track which were explicitly provided
    args = parser.parse_args()
    
    # Get the raw command line arguments to detect user-provided values
    # This helps us distinguish between defaults and user-specified values
    import sys
    user_provided_args = set()
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith('--'):
            # Remove leading dashes and convert to argument name
            arg_name = arg.lstrip('-').replace('-', '_')
            user_provided_args.add(arg_name)
    
    # Handle --list-report-systems
    if args.list_report_systems:
        systems = list_available_systems()
        if not systems:
            print("No report systems found.")
            return 0
        
        print("Available report systems:")
        print()
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
    
    # Check for OpenAI API key (unless dry run)
    openai_key = args.openai_key or os.getenv('OPENAI_API_KEY')
    if not openai_key and not args.dry_run:
        parser.error("OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --openai-key")
    
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
        openai_api_key=openai_key,
        openai_model=args.openai_model,
        llm_temperature=args.llm_temperature,
        llm_max_tokens=args.llm_max_tokens,
        llm_combine_warning_threshold=args.llm_combine_warning_threshold,
        image_chunk_size=args.image_chunk_size,
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
    
    # Use the new JSON-based report system framework
    try:
        log_info(f"Loading report system: {args.report_system}", config)
        
        # Build CLI overrides for the JSON system
        # These allow CLI arguments to override values from the JSON definition
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
                'model': config.openai_model,
                'temperature': config.llm_temperature,
                'max_tokens': config.llm_max_tokens,
                'chunk_size': config.image_chunk_size,
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


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
from .config import ReportConfig, validate_config
from .utils import log_info, log_success, log_warning, log_error, log_verbose, format_number
from .cache import init_cache, get_cache
from .data_parser import parse_filename
from .analysis import analyze_data
from .report_generator import generate_html_report

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
        help='Output HTML file (default: performance_report.html)'
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
    
    args = parser.parse_args()
    
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
        image_chunk_size=args.image_chunk_size,
        cache_dir=Path(args.cache_dir),
        use_cache=args.use_cache and not args.dry_run,
        clear_cache=args.clear_cache,
        dry_run=args.dry_run,
        sample_size=args.sample_size,
        verbose=args.verbose,
        quiet=args.quiet,
        embed_images=args.embed_images
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
    
    # Find PNG files
    input_dir = Path(args.dir).resolve()
    
    if not input_dir.exists():
        log_error(f"Directory not found: {input_dir}")
        return 1
    
    if not input_dir.is_dir():
        log_error(f"Path is not a directory: {input_dir}")
        return 1
    
    log_info(f"Scanning directory: {input_dir}", config)
    png_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.png')]
    
    if not png_files:
        log_error(f"No PNG files found in {input_dir}")
        log_info("Expected filename format: TestCase_tricount_drawcalls_timestamp.png", config)
        log_info("Example: Level1_85000_520_1234567890.png", config)
        return 1
    
    log_success(f"Found {len(png_files)} PNG file(s)", config)
    
    # Parse data
    data_points = []
    parse_errors = 0
    
    iterator = tqdm(png_files, desc="Parsing files", disable=config.quiet) if TQDM_AVAILABLE else png_files
    
    for png_file in iterator:
        try:
            data_points.append(parse_filename(png_file))
        except (ValueError, IndexError) as e:
            log_warning(f"Skipping {png_file} - {e}", config)
            parse_errors += 1
            continue
    
    if not data_points:
        log_error("No valid data points found after parsing")
        log_info(f"Skipped {parse_errors} file(s) due to parsing errors", config)
        return 1
    
    if parse_errors > 0:
        log_warning(f"Successfully parsed {len(data_points)}/{len(png_files)} files ({parse_errors} errors)", config)
    
    # Apply sampling if requested
    original_count = len(data_points)
    if config.sample_size and config.sample_size < len(data_points):
        log_info(f"Sampling {config.sample_size} random data points from {len(data_points)}", config)
        data_points = random.sample(data_points, config.sample_size)
    
    # Sort by timestamp
    data_points.sort(key=lambda x: x['ts'])
    
    # Calculate statistics
    log_info("Analyzing performance data...", config)
    stats = analyze_data(data_points, config)
    
    log_verbose(f"Statistics calculated: {stats['count']} samples", config)
    log_verbose(f"  Draw calls - Min: {stats['draws']['min']}, Max: {stats['draws']['max']}, Mean: {format_number(stats['draws']['mean'], 1)}", config)
    log_verbose(f"  Triangles - Min: {format_number(stats['tris']['min'])}, Max: {format_number(stats['tris']['max'])}, Mean: {format_number(stats['tris']['mean'], 1)}", config)
    
    # Determine image directory path
    output_path = Path(args.output).resolve()
    if args.images_dir:
        images_dir_rel = args.images_dir
    else:
        try:
            images_dir_rel = input_dir.relative_to(output_path.parent).as_posix()
        except ValueError:
            images_dir_rel = os.path.relpath(input_dir, output_path.parent).replace(os.sep, '/')
    
    # Generate HTML
    log_info(f"Generating report: {output_path}", config)
    
    if config.dry_run:
        log_info("Dry run mode: Generating report with placeholder LLM content", config)
    elif config.use_cache:
        log_info("Using cache when available for LLM responses", config)
    
    try:
        html = generate_html_report(data_points, stats, images_dir_rel, output_path, config)
    except Exception as e:
        log_error(f"Failed to generate HTML report: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Write output
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
    except Exception as e:
        log_error(f"Failed to write output file: {e}")
        return 1
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    log_success(f"Report written to: {output_path}", config)
    log_info("Summary:", config)
    log_info(f"  - {stats['count']} samples analyzed", config)
    log_info(f"  - {len(stats['high_load'])} high-load frames identified", config)
    log_info(f"  - Critical hotspot: index {stats['critical'][0]} ({stats['critical'][1]['draws']} draws, {format_number(stats['critical'][1]['tris'])} tris)", config)
    
    if config.embed_images:
        log_info(f"  - Images embedded as base64 (standalone HTML)", config)
    
    if config.sample_size and config.sample_size < original_count:
        log_info(f"  - Sampled {config.sample_size} of {original_count} total samples", config)
    
    if config.dry_run:
        log_warning("  - Dry run mode - no actual LLM calls made", config)
    
    log_info(f"Completed in {elapsed_time:.1f}s", config)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())


#!/usr/bin/env python3
"""
Multi-page HTML report generation for BobReview.

This package generates a comprehensive performance analysis report split across multiple pages:
- index.html: Homepage with executive summary and navigation
- metrics.html: Detailed metrics analysis with charts
- zones.html: Performance zones and hotspots
- visuals.html: Distribution charts and visual analysis
- optimization.html: Optimization checklist and recommendations
- stats.html: Comprehensive statistical summary with full data table
"""

from pathlib import Path
from typing import Dict, List, Any

from ..utils import log_info, log_verbose, image_to_base64, log_warning
from ..llm_provider import (
    generate_executive_summary,
    generate_metric_deep_dive,
    generate_zones_hotspots,
    generate_optimization_checklist,
    generate_system_recommendations,
    generate_visual_analysis,
    generate_statistical_interpretation
)

from .homepage import generate_homepage
from .metrics import generate_metrics_page
from .zones import generate_zones_page
from .visuals import generate_visuals_page
from .optimization import generate_optimization_page
from .stats import generate_stats_page

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


def generate_html_report(
    data_points: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    images_dir_rel: str, 
    output_path: Path, 
    config
) -> str:
    """
    Generate a multi-page HTML performance report.
    
    This function creates multiple HTML files in the same directory as the output file:
    - index.html: Homepage with overview and navigation
    - metrics.html: Detailed metrics page
    - zones.html: Zones and hotspots page
    - visuals.html: Visual analysis page
    - optimization.html: Optimization checklist page
    - stats.html: Statistical summary page
    
    Parameters:
        data_points: List of parsed capture records
        stats: Aggregated analysis results
        images_dir_rel: Path to images directory relative to output HTML
        output_path: Destination file path (will be renamed to index.html)
        config: Report configuration
    
    Returns:
        str: Path to the generated index.html file
    """
    # Convert relative image path to absolute for LLM functions
    images_dir_abs = (output_path.parent / images_dir_rel).resolve() if images_dir_rel else output_path.parent
    
    # Pre-encode all images to base64 if embed_images is enabled
    image_data_uris = {}
    if config.embed_images:
        log_info("Embedding images as base64 data URIs...", config)
        unique_images = set(point['img'] for point in data_points)
        for img_name in unique_images:
            img_path = images_dir_abs / img_name
            data_uri = image_to_base64(img_path)
            if data_uri:
                image_data_uris[img_name] = data_uri
            else:
                log_warning(f"Could not encode image: {img_name}", config)
        log_verbose(f"Encoded {len(image_data_uris)} images to base64", config)
    
    # Generate LLM content
    log_info("Generating LLM content for all pages...", config)
    
    sections = [
        ("Executive Summary", lambda: generate_executive_summary(data_points, stats, config, str(images_dir_abs))),
        ("Metric Deep Dive", lambda: generate_metric_deep_dive(data_points, stats, config, str(images_dir_abs))),
        ("Zones & Hotspots", lambda: generate_zones_hotspots(data_points, stats, config, str(images_dir_abs))),
        ("Visual Analysis", lambda: generate_visual_analysis(data_points, stats, config, str(images_dir_abs))),
        ("Statistical Interpretation", lambda: generate_statistical_interpretation(data_points, stats, config, str(images_dir_abs))),
        ("Optimization Checklist", lambda: generate_optimization_checklist(data_points, stats, config, str(images_dir_abs))),
    ]
    
    if config.enable_recommendations:
        sections.append(
            ("System Recommendations", lambda: generate_system_recommendations(data_points, stats, config, str(images_dir_abs)))
        )
    
    if TQDM_AVAILABLE and not config.quiet:
        iterator = tqdm(sections, desc="Generating LLM content")
    else:
        iterator = sections
    
    results = {}
    for section_name, generate_func in iterator:
        log_verbose(f"Generating: {section_name}", config)
        results[section_name] = generate_func()
    
    exec_summary = results["Executive Summary"]
    metric_content = results["Metric Deep Dive"]
    zones_content = results["Zones & Hotspots"]
    visual_analysis_content = results["Visual Analysis"]
    statistical_interpretation = results["Statistical Interpretation"]
    optimization_content = results["Optimization Checklist"]
    system_recs = results.get("System Recommendations", {})
    
    # Determine output directory (use parent of output_path for multi-file output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate all pages
    log_info("Generating HTML pages...", config)
    
    pages = [
        ("index.html", lambda: generate_homepage(stats, config, exec_summary)),
        ("metrics.html", lambda: generate_metrics_page(data_points, stats, config, metric_content)),
        ("zones.html", lambda: generate_zones_page(stats, images_dir_rel, image_data_uris, config, zones_content)),
        ("visuals.html", lambda: generate_visuals_page(data_points, stats, config, visual_analysis_content)),
        ("optimization.html", lambda: generate_optimization_page(data_points, stats, images_dir_rel, image_data_uris, config, optimization_content, system_recs)),
        ("stats.html", lambda: generate_stats_page(data_points, stats, images_dir_rel, image_data_uris, config, statistical_interpretation)),
    ]
    
    generated_files = []
    for filename, generate_func in pages:
        page_path = output_dir / filename
        log_verbose(f"Writing {filename}...", config)
        html_content = generate_func()
        page_path.write_text(html_content, encoding='utf-8')
        generated_files.append(str(page_path))
        log_verbose(f"Created: {page_path}", config)
    
    log_info(f"Generated {len(generated_files)} HTML files in {output_dir}", config)
    
    # Return the path to index.html as the main entry point
    return str(output_dir / "index.html")


# For backward compatibility, export the main function
__all__ = ['generate_html_report']


"""
Multi-page HTML report generation for BobReview.

This package generates a comprehensive performance analysis report using a
modular page registry system. Pages self-register and can be enabled/disabled
via configuration.
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

# Import registry
from .registry import get_enabled_pages, get_all_pages, set_disabled_pages

# Import all page modules to trigger their registration
from . import homepage
from . import metrics
from . import zones
from . import visuals
from . import optimization
from . import stats

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


# Mapping from llm_section names to generator functions
LLM_GENERATORS = {
    'Executive Summary': generate_executive_summary,
    'Metric Deep Dive': generate_metric_deep_dive,
    'Zones & Hotspots': generate_zones_hotspots,
    'Visual Analysis': generate_visual_analysis,
    'Statistical Interpretation': generate_statistical_interpretation,
    'Optimization Checklist': generate_optimization_checklist,
    'System Recommendations': generate_system_recommendations,
}


def generate_html_report(
    data_points: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    images_dir_rel: str, 
    output_path: Path, 
    config
) -> str:
    """
    Generate a multi-page HTML performance report using the page registry.
    
    Pages are generated based on the registry, with disabled pages excluded.
    Navigation is automatically generated from enabled pages.
    
    Parameters:
        data_points: List of parsed capture records
        stats: Aggregated analysis results
        images_dir_rel: Path to images directory relative to output HTML
        output_path: Destination file path (will be renamed to index.html)
        config: Report configuration (includes disabled_pages list)
    
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
    
    # Set disabled pages in registry so get_nav_items knows about them
    set_disabled_pages(config.disabled_pages)
    
    # Get enabled pages from registry
    enabled_pages = get_enabled_pages()
    log_verbose(f"Enabled pages: {[p.id for p in enabled_pages]}", config)
    
    # Collect unique LLM sections needed by enabled pages
    needed_sections = set(p.llm_section for p in enabled_pages)
    
    # Add system recommendations if enabled
    if config.enable_recommendations:
        needed_sections.add('System Recommendations')
    
    # Generate LLM content for needed sections
    log_info("Generating LLM content for enabled pages...", config)
    
    sections = [
        (section_name, lambda s=section_name: LLM_GENERATORS[s](data_points, stats, config, str(images_dir_abs)))
        for section_name in needed_sections
        if section_name in LLM_GENERATORS
    ]
    
    if TQDM_AVAILABLE and not config.quiet:
        iterator = tqdm(sections, desc="Generating LLM content")
    else:
        iterator = sections
    
    llm_results = {}
    for section_name, generate_func in iterator:
        log_verbose(f"Generating: {section_name}", config)
        llm_results[section_name] = generate_func()
    
    # Determine output directory
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate all enabled pages
    log_info("Generating HTML pages...", config)
    
    generated_files = []
    for page in enabled_pages:
        page_path = output_dir / page.filename
        log_verbose(f"Writing {page.filename}...", config)
        
        # Build kwargs for page generator based on what it needs
        kwargs = {
            'stats': stats,
            'config': config,
        }
        
        # Add LLM content (each generator expects specific content)
        llm_content = llm_results.get(page.llm_section, {})
        
        # Match kwargs based on page ID (generators have different signatures)
        if page.id == 'home':
            kwargs['exec_summary'] = llm_content
        elif page.id == 'metrics':
            kwargs['data_points'] = data_points
            kwargs['metric_content'] = llm_content
        elif page.id == 'zones':
            kwargs['images_dir_rel'] = images_dir_rel
            kwargs['image_data_uris'] = image_data_uris
            kwargs['zones_content'] = llm_content
        elif page.id == 'visuals':
            kwargs['data_points'] = data_points
            kwargs['visual_analysis_content'] = llm_content  # Fixed: was 'visual_content'
        elif page.id == 'optimization':
            kwargs['data_points'] = data_points
            kwargs['images_dir_rel'] = images_dir_rel
            kwargs['image_data_uris'] = image_data_uris
            kwargs['optimization_content'] = llm_content
            kwargs['system_recs'] = llm_results.get('System Recommendations', {})
        elif page.id == 'stats':
            kwargs['data_points'] = data_points
            kwargs['images_dir_rel'] = images_dir_rel
            kwargs['image_data_uris'] = image_data_uris
            kwargs['statistical_interpretation'] = llm_content  # Fixed: was 'stats_content'
        
        html_content = page.page_generator(**kwargs)
        page_path.write_text(html_content, encoding='utf-8')
        generated_files.append(str(page_path))
        log_verbose(f"Created: {page_path}", config)
    
    # Copy CSS file if using linked CSS mode
    if config.linked_css:
        from .base import copy_css_to_output
        css_path = copy_css_to_output(output_dir)
        generated_files.append(str(css_path))
        log_info(f"Created external CSS: {css_path}", config)
    
    log_info(f"Generated {len(generated_files)} files in {output_dir}", config)
    
    # Return the path to index.html as the main entry point
    return str(output_dir / "index.html")


# For backward compatibility, export the main function
__all__ = ['generate_html_report']

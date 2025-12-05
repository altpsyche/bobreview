"""
Pages package for BobReview HTML report generation.

Each module generates a specific page of the report.
"""

from pathlib import Path
from typing import Dict, List, Any

from ..core.utils import log_info, log_verbose, log_warning, image_to_base64
from ..registry.pages import get_enabled_pages, set_disabled_pages

# Import page modules to trigger registration
from . import homepage
from . import metrics
from . import zones
from . import visuals
from . import optimization
from . import stats

# Check for tqdm
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    class tqdm:
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable
        def __iter__(self):
            return iter(self.iterable)


def generate_report(
    data_points: List[Dict[str, Any]], 
    stats_data: Dict[str, Any], 
    images_dir_rel: str, 
    output_path: Path, 
    config,
    llm_results: Dict[str, Any]
) -> str:
    """
    Generate multi-page HTML report.
    
    Parameters:
        data_points: Parsed capture records
        stats_data: Aggregated analysis
        images_dir_rel: Relative path to images
        output_path: Destination file path
        config: Report configuration
        llm_results: Pre-generated LLM content
    
    Returns:
        Path to generated index.html
    """
    images_dir_abs = (output_path.parent / images_dir_rel).resolve() if images_dir_rel else output_path.parent
    
    # Pre-encode images
    image_data_uris = {}
    if config.embed_images:
        log_info("Embedding images as base64...", config)
        for point in data_points:
            img_name = point['img']
            if img_name not in image_data_uris:
                img_path = images_dir_abs / img_name
                uri = image_to_base64(img_path)
                if uri:
                    image_data_uris[img_name] = uri
        log_verbose(f"Encoded {len(image_data_uris)} images", config)
    
    set_disabled_pages(config.disabled_pages)
    enabled_pages = get_enabled_pages()
    log_verbose(f"Enabled pages: {[p.id for p in enabled_pages]}", config)
    
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_info("Generating HTML pages...", config)
    
    generated_files = []
    for page in enabled_pages:
        page_path = output_dir / page.filename
        log_verbose(f"Writing {page.filename}...", config)
        
        kwargs = {'stats': stats_data, 'config': config}
        llm_content = llm_results.get(page.llm_section, {})
        
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
            kwargs['visual_analysis_content'] = llm_content
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
            kwargs['statistical_interpretation'] = llm_content
        
        html = page.page_generator(**kwargs)
        page_path.write_text(html, encoding='utf-8')
        generated_files.append(str(page_path))
    
    # Copy CSS if using linked mode
    if config.linked_css:
        from .base import copy_css_to_output
        try:
            css_path = copy_css_to_output(output_dir)
            generated_files.append(str(css_path))
        except Exception as e:
            log_warning(f"CSS copy failed: {e}", config)
    
    log_info(f"Generated {len(generated_files)} files in {output_dir}", config)
    return str(output_dir / "index.html")


__all__ = ['generate_report']

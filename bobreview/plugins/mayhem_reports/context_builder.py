"""
Context Builder for mayhem-reports Plugin.

Adds performance-specific template context:
- images: List with src, draws, tris metadata
- critical: Critical hotspot point data
- high_load_count, low_load_count, percentages
- metrics, metric_labels from system extensions

Implements ContextBuilderInterface from core.api.
"""

from typing import Dict, List, Any, TYPE_CHECKING
from pathlib import Path

from bobreview.core.api import ContextBuilderInterface

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig


class MayhemReportsContextBuilder(ContextBuilderInterface):
    """
    Builds template context for performance analysis reports.
    
    Adds:
    - images: List of images with draws/tris metadata
    - critical: Critical hotspot point data
    - metric_labels: Labels for primary metrics
    - high_load_count, low_load_count, percentages
    """
    
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build template context from data and statistics.
        
        Parameters:
            data_points: List of parsed data points
            stats: Statistical analysis results
            config: ReportConfig with settings
            base_context: Base context already prepared by framework
        
        Returns:
            Enriched context dictionary merged with base_context.
        """
        context = {}
        
        # Extract values from base_context
        input_dir = base_context.get('input_dir')
        image_data_uris = base_context.get('image_data_uris')
        system_def = base_context.get('system_def')
        
        # Build images list with performance metadata
        images = []
        if input_dir:
            possible_dirs = [input_dir, input_dir / 'images']
            
            for point in data_points:
                img_name = point.get('img') or point.get('image')
                
                if img_name:
                    img_path = None
                    for test_dir in possible_dirs:
                        test_path = test_dir / img_name
                        if test_path.exists():
                            img_path = test_path
                            break
                    
                    if img_path:
                        if config.output.embed_images and image_data_uris and img_name in image_data_uris:
                            src = image_data_uris[img_name]
                        else:
                            src = img_name
                        
                        images.append({
                            'src': src,
                            'name': img_name,
                            'testcase': point.get('testcase', ''),
                            'draws': point.get('draws', 0),
                            'tris': point.get('tris', 0)
                        })
                    else:
                        images.append(None)
                else:
                    images.append(None)
        else:
            images = [None] * len(data_points)
        
        context['images'] = images
        context['has_images'] = any(img is not None for img in images)
        
        # Build critical point data
        critical = {}
        try:
            metrics_ext = system_def.extensions.get('metrics', {}) if system_def else {}
            primary_metrics = metrics_ext.get('primary', []) if metrics_ext else []
            if primary_metrics and 'critical' in stats:
                critical_point = stats['critical'][1] if stats['critical'] else {}
                critical = {
                    'index': stats['critical'][0] if stats['critical'] else 0,
                    **{m: critical_point.get(m, 0) for m in primary_metrics}
                }
        except (AttributeError, KeyError):
            primary_metrics = []
        
        context['critical'] = critical
        
        # Add metric labels from system definition extensions
        context['metrics'] = primary_metrics
        metrics_ext = system_def.extensions.get('metrics', {}) if system_def else {}
        context['metric_labels'] = metrics_ext.get('metric_labels', {}) if metrics_ext else {}
        
        # Get location from extensions or extract from data
        location = None
        if system_def:
            mayhem_ext = system_def.extensions.get('mayhem', {})
            if mayhem_ext and 'location' in mayhem_ext:
                location = mayhem_ext['location']
        
        if not location and data_points and 'testcase' in data_points[0]:
            testcases = [dp.get('testcase', '') for dp in data_points if dp.get('testcase')]
            if testcases:
                location = testcases[0]
        
        if location:
            context['location'] = location
        
        # Add high_load_count, low_load_count, percentages
        high_load_count = len(stats.get('high_load', []))
        low_load_count = len(stats.get('low_load', []))
        total_count = stats.get('count', 1)
        context['high_load_count'] = high_load_count
        context['low_load_count'] = low_load_count
        context['high_load_pct'] = (high_load_count / total_count) * 100 if total_count > 0 else 0
        context['low_load_pct'] = (low_load_count / total_count) * 100 if total_count > 0 else 0
        
        # Add ranked_data for backwards compatibility with scaffolded template
        ranked = sorted(data_points, key=lambda x: x.get('draws', 0), reverse=True)
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        context['ranked_data'] = ranked
        
        # Merge with base_context and return
        return {
            **base_context,
            **context
        }

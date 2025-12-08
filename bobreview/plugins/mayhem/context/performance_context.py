"""
Performance context builder for MayhemAutomation.

Adds performance-specific template context: images with draws/tris,
critical point tracking, and metric labels.
"""
from typing import Dict, List, Any
from pathlib import Path


class PerformanceContextBuilder:
    """
    Builds template context for performance analysis reports.
    
    Adds:
    - images: List of images with draws/tris metadata
    - critical: Critical hotspot point data
    - metric_labels: Labels for primary metrics
    """
    
    def build(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        system_def: Any,
        input_dir: Path = None
    ) -> Dict[str, Any]:
        """
        Build performance-specific template context.
        
        Args:
            data_points: List of data points
            stats: Statistical analysis results
            config: Report configuration
            system_def: Report system definition
            input_dir: Input directory for images
            
        Returns:
            Dict of additional context to merge into base context
        """
        context = {}
        
        # Build images list with performance metadata
        images = []
        if input_dir:
            images_dir = input_dir / 'images'
            if images_dir.exists():
                for point in data_points:
                    img_name = point.get('image')
                    if not img_name:
                        continue
                    img_path = images_dir / img_name
                    if not img_path.exists():
                        continue
                    
                    # Build relative src path
                    src = f"images/{img_name}"
                    images.append({
                        'src': src,
                        'testcase': point.get('testcase', ''),
                        'draws': point.get('draws', 0),
                        'tris': point.get('tris', 0)
                    })
        
        context['images'] = images
        context['has_images'] = len(images) > 0
        
        # Build critical point data
        critical = {}
        try:
            metrics_config = system_def.metrics
            primary_metrics = metrics_config.primary if metrics_config else []
            if primary_metrics and 'critical' in stats:
                critical_point = stats['critical'][1] if stats['critical'] else {}
                critical = {
                    'index': stats['critical'][0] if stats['critical'] else 0,
                    **{m: critical_point.get(m, 0) for m in primary_metrics}
                }
        except (AttributeError, KeyError):
            primary_metrics = []
        
        context['critical'] = critical
        
        # Add metric labels from system definition
        context['metrics'] = primary_metrics if 'primary_metrics' in dir() else []
        context['metric_labels'] = getattr(system_def.metrics, 'metric_labels', {}) if system_def.metrics else {}
        
        return context

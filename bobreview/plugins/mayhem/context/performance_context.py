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
        input_dir: Path = None,
        image_data_uris: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Build performance-specific template context.
        
        Args:
            data_points: List of data points
            stats: Statistical analysis results
            config: Report configuration
            system_def: Report system definition
            input_dir: Input directory for images
            image_data_uris: Dict mapping image names to base64 data URIs (if embedding)
            
        Returns:
            Dict of additional context to merge into base context
        """
        context = {}
        
        # Build images list with performance metadata
        # IMPORTANT: Images list must match data_points by index for templates to work
        images = []
        if input_dir:
            # Try input_dir directly first (PNG files are usually in the directory itself)
            # Also try images subdirectory as fallback
            possible_dirs = [input_dir, input_dir / 'images']
            
            for point in data_points:
                # Support both 'img' and 'image' field names
                img_name = point.get('img') or point.get('image')
                
                if img_name:
                    # Find the image file
                    img_path = None
                    for test_dir in possible_dirs:
                        test_path = test_dir / img_name
                        if test_path.exists():
                            img_path = test_path
                            break
                    
                    if img_path:
                        # Determine src - use base64 if embedding, otherwise relative path
                        if config.output.embed_images and image_data_uris and img_name in image_data_uris:
                            src = image_data_uris[img_name]
                        else:
                            # Use just the filename - templates will construct full path using images_dir_rel
                            src = img_name
                        
                        images.append({
                            'src': src,
                            'name': img_name,
                            'testcase': point.get('testcase', ''),
                            'draws': point.get('draws', 0),
                            'tris': point.get('tris', 0)
                        })
                    else:
                        # Image not found - add None to maintain index alignment
                        images.append(None)
                else:
                    # No image name - add None to maintain index alignment
                    images.append(None)
        else:
            # No input_dir - create list of None to maintain index alignment
            images = [None] * len(data_points)
        
        context['images'] = images
        context['has_images'] = any(img is not None for img in images)
        
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

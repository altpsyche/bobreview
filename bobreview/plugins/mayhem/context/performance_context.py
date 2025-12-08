"""
Performance context builder for MayhemAutomation.

Adds performance-specific template context: images with draws/tris,
critical point tracking, and metric labels.

Implements ContextBuilderInterface from core.api.
"""
from typing import Dict, List, Any, TYPE_CHECKING
from pathlib import Path

from bobreview.core.api import ContextBuilderInterface

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig


class PerformanceContextBuilder(ContextBuilderInterface):
    """
    Builds template context for performance analysis reports.
    
    Adds:
    - images: List of images with draws/tris metadata
    - critical: Critical hotspot point data
    - metric_labels: Labels for primary metrics
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
        
        Implements ContextBuilderInterface.build_context().
        
        Parameters:
            data_points: List of parsed data points
            stats: Statistical analysis results
            config: ReportConfig with settings
            base_context: Base context already prepared by framework
        
        Returns:
            Enriched context dictionary. Should merge with base_context.
        """
        context = {}
        
        # Extract values from base_context that we need
        input_dir = base_context.get('input_dir')
        image_data_uris = base_context.get('image_data_uris')
        system_def = base_context.get('system_def')
        
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
        if system_def and hasattr(system_def, 'metrics'):
            context['metric_labels'] = getattr(system_def.metrics, 'metric_labels', {})
        else:
            context['metric_labels'] = {}
        
        # Get location from system_def (JSON config) or extract from data (MayhemAutomation-specific)
        # Priority: 1) JSON config, 2) Extract from testcase field
        location = None
        if system_def and hasattr(system_def, 'location') and system_def.location:
            location = system_def.location
        
        # Fall back to extracting from testcase field if not in JSON
        if not location and data_points and 'testcase' in data_points[0]:
            testcases = [dp.get('testcase', '') for dp in data_points if dp.get('testcase')]
            if testcases:
                location = testcases[0]
        
        if location:
            context['location'] = location
        
        # Merge with base_context and return
        return {
            **base_context,
            **context
        }
    
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
        Legacy method for backward compatibility with framework.
        
        This method is kept for compatibility but should use build_context() instead.
        """
        base_context = {
            'input_dir': input_dir,
            'image_data_uris': image_data_uris,
            'system_def': system_def
        }
        return self.build_context(data_points, stats, config, base_context)

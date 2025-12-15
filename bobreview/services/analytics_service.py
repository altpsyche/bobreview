"""
Analytics service for statistical analysis.

This service handles all statistical calculations:
- Mean, median, percentiles
- Standard deviation, variance
- Outlier detection
- Performance zone classification
"""

from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
import logging

from .base import BaseService, AnalyticsServiceError

if TYPE_CHECKING:
    from ..core.dataframe import DataFrame

logger = logging.getLogger(__name__)


class AnalyticsService(BaseService):
    """
    Service for statistical analysis of data.
    
    Extracted from ReportSystemExecutor.analyze_data() to enable:
    - Independent testing
    - Plugin replacement with custom analytics
    - Reuse across different report types
    
    Example:
        service = AnalyticsService()
        stats = service.analyze(
            data=data,  # DataFrame or List[Dict]
            metrics=['draws', 'tris'],
            metrics_config=system_def.metrics
        )
    """
    
    def analyze(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        metrics: List[str],
        metrics_config: Any,
        report_config: Any = None,
        thresholds: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate statistics for data points.
        
        Parameters:
            data: DataFrame or List[Dict] with data points to analyze
            metrics: List of metric field names
            metrics_config: Dict-like config with timestamp_field, identifier_field, threshold_mapping
            report_config: Config instance (preferred, contains all thresholds)
            thresholds: Dict of thresholds (fallback if report_config not provided)
            
        Returns:
            Dictionary with statistics for each metric
            
        Raises:
            AnalyticsServiceError: If analysis fails
        """
        # Convert DataFrame to list for internal use
        if hasattr(data, 'to_dicts'):
            data_points = list(data)  # DataFrame iteration yields dicts
        elif isinstance(data, list):
            data_points = data
        else:
            raise AnalyticsServiceError(f"Unsupported data type: {type(data)}")
        if not data_points:
            raise AnalyticsServiceError("No data points to analyze")
        
        # Handle dict-like or object metrics_config
        if hasattr(metrics_config, 'get'):
            # Dict-like
            timestamp_field = metrics_config.get('timestamp_field')
            identifier_field = metrics_config.get('identifier_field')
            threshold_mapping = metrics_config.get('threshold_mapping', {})
        else:
            # Object with attributes
            timestamp_field = getattr(metrics_config, 'timestamp_field', None)
            identifier_field = getattr(metrics_config, 'identifier_field', None)
            threshold_mapping = getattr(metrics_config, 'threshold_mapping', {})
        
        # Build metric_config dict
        metric_config = {
            'timestamp_field': timestamp_field,
            'identifier_field': identifier_field,
            'threshold_mapping': threshold_mapping
        }
        
        # Validate required fields exist
        first_point = data_points[0]
        missing = [m for m in metrics if m not in first_point]
        if missing:
            raise AnalyticsServiceError(
                f"Data points missing required metrics: {', '.join(missing)}. "
                f"Available fields: {', '.join(first_point.keys())}"
            )
        
        try:
            # Get analyzer from the plugin registry
            from ..core.plugin_system.registry import get_registry
            
            registry = get_registry()
            analyzer_func = registry.analyzers.get()  # Get default analyzer
            
            if analyzer_func:
                from ..core.config import Config
                
                # Use provided config or build from thresholds
                if report_config is not None:
                    config = report_config
                elif thresholds:
                    config = Config(thresholds=thresholds)
                else:
                    raise AnalyticsServiceError(
                        "Either report_config or thresholds must be provided"
                    )
                
                stats = analyzer_func(
                    data_points,
                    config,
                    metrics=metrics,
                    metric_config=metrics_config
                )
                
                logger.debug(f"Analyzed {len(data_points)} points across {len(metrics)} metrics")
                return stats
            else:
                # No plugin analyzer registered - return basic data structure
                logger.debug("No plugin analyzer registered, returning basic data")
                return {
                    'data': data_points, 
                    'count': len(data_points),
                    'metrics': metrics
                }
            
        except ImportError:
            # Plugin system not available - return basic stats only
            logger.warning("Plugin system not available, returning basic data")
            return {'data': data_points, 'count': len(data_points)}
        except KeyError as e:
            raise AnalyticsServiceError(
                f"Analysis failed: missing required field {e}"
            ) from e
        except Exception as e:
            raise AnalyticsServiceError(f"Analysis failed: {e}") from e
    
    def calculate_percentiles(
        self,
        values: List[float],
        percentiles: List[int] = None
    ) -> Dict[str, float]:
        """
        Calculate percentiles for a list of values.
        
        Parameters:
            values: List of numeric values
            percentiles: List of percentiles to calculate (default: [25, 50, 75, 90, 95, 99])
            
        Returns:
            Dict mapping percentile names to values (e.g., {'p25': 100, 'p50': 150, ...})
        """
        import statistics
        
        if not values:
            return {}
        
        percentiles = percentiles or [25, 50, 75, 90, 95, 99]
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        result = {}
        for p in percentiles:
            idx = int((p / 100) * (n - 1))
            result[f'p{p}'] = sorted_values[idx]
        
        return result
    
    def detect_outliers(
        self,
        values: List[float],
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect outliers in a list of values.
        
        Parameters:
            values: List of numeric values
            method: Detection method ('iqr', 'zscore', 'mad')
            threshold: Threshold multiplier for outlier detection
            
        Returns:
            Dict with 'indices', 'values', 'count', 'bounds'
        """
        import statistics
        
        if len(values) < 4:
            return {'indices': [], 'values': [], 'count': 0, 'bounds': None}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if method == 'iqr':
            q1_idx = n // 4
            q3_idx = (3 * n) // 4
            q1 = sorted_values[q1_idx]
            q3 = sorted_values[q3_idx]
            iqr = q3 - q1
            
            lower = q1 - (threshold * iqr)
            upper = q3 + (threshold * iqr)
            
        elif method == 'zscore':
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            lower = mean - (threshold * stdev)
            upper = mean + (threshold * stdev)
            
        elif method == 'mad':
            median = statistics.median(values)
            mad = statistics.median([abs(v - median) for v in values])
            # MAD to stdev conversion: 1.4826
            lower = median - (threshold * 1.4826 * mad)
            upper = median + (threshold * 1.4826 * mad)
        else:
            raise AnalyticsServiceError(f"Unknown outlier method: {method}")
        
        outlier_indices = []
        outlier_values = []
        
        for i, v in enumerate(values):
            if v < lower or v > upper:
                outlier_indices.append(i)
                outlier_values.append(v)
        
        return {
            'indices': outlier_indices,
            'values': outlier_values,
            'count': len(outlier_indices),
            'bounds': {'lower': lower, 'upper': upper}
        }
    
    def classify_performance_zones(
        self,
        data_points: List[Dict[str, Any]],
        metric: str,
        high_threshold: float,
        low_threshold: float
    ) -> Dict[str, List[int]]:
        """
        Classify data points into performance zones.
        
        Parameters:
            data_points: List of data points
            metric: Metric field to classify on
            high_threshold: Threshold for high-load zone
            low_threshold: Threshold for low-load zone
            
        Returns:
            Dict with 'high', 'normal', 'low' lists of indices
        """
        zones = {'high': [], 'normal': [], 'low': []}
        
        for i, point in enumerate(data_points):
            value = point.get(metric, 0)
            
            if value >= high_threshold:
                zones['high'].append(i)
            elif value <= low_threshold:
                zones['low'].append(i)
            else:
                zones['normal'].append(i)
        
        return zones

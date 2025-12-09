"""
Analytics service for statistical analysis.

This service handles all statistical calculations:
- Mean, median, percentiles
- Standard deviation, variance
- Outlier detection
- Performance zone classification
"""

from typing import List, Dict, Any, Optional
import logging

from .base import BaseService, AnalyticsServiceError

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
            data_points=data,
            metrics=['draws', 'tris'],
            metrics_config=system_def.metrics
        )
    """
    
    def analyze(
        self,
        data_points: List[Dict[str, Any]],
        metrics: List[str],
        metrics_config: Any,
        report_config: Any = None,
        thresholds: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate statistics for data points.
        
        Parameters:
            data_points: List of data points to analyze
            metrics: List of metric field names (e.g., ['draws', 'tris'])
            metrics_config: MetricsConfig from report system
            report_config: ReportConfig instance (preferred, contains all thresholds)
            thresholds: Dict of thresholds (fallback if report_config not provided)
            
        Returns:
            Dictionary with statistics for each metric
            
        Raises:
            AnalyticsServiceError: If analysis fails
        """
        # Import here to avoid circular imports
        from ..core import analyze_data, ReportConfig
        
        if not data_points:
            raise AnalyticsServiceError("No data points to analyze")
        
        # Build metric_config dict for core analyze_data function
        metric_config = {
            'timestamp_field': metrics_config.timestamp_field,
            'identifier_field': metrics_config.identifier_field,
            'threshold_mapping': metrics_config.threshold_mapping
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
            # Use provided config or build from thresholds
            if report_config is not None:
                config = report_config
            elif thresholds:
                # Build config with thresholds
                from ..core.config_classes import ThresholdConfig
                config = ReportConfig(thresholds=ThresholdConfig(**thresholds))
            else:
                raise AnalyticsServiceError(
                    "Either report_config or thresholds must be provided"
                )
            
            stats = analyze_data(
                data_points,
                config,
                metrics=metrics,
                metric_config=metric_config
            )
            
            logger.debug(f"Analyzed {len(data_points)} points across {len(metrics)} metrics")
            return stats
            
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

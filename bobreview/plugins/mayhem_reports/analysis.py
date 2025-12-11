"""
Performance analysis functions for mayhem-reports plugin.

Provides performance-specific analysis including:
- Metric statistics (draws, tris)
- High/low load detection
- Critical hotspot identification
- Frame time analysis
- Trend detection
"""

import statistics
from typing import Dict, List, Any, Tuple, TYPE_CHECKING

# Import generic utilities from core
from bobreview.core.analysis import (
    _calculate_confidence_interval,
    _calculate_linear_regression,
    _detect_outliers_iqr,
    _detect_outliers_mad,
    _classify_trend,
)

if TYPE_CHECKING:
    from bobreview.core.config_classes import ReportConfig


def calculate_frame_times(timestamps: List[int]) -> Dict[str, Any]:
    """
    Calculate frame time statistics from timestamps.
    
    Parameters:
        timestamps: List of timestamps in temporal order
    
    Returns:
        dict: Frame time statistics including min, max, mean, median, and anomalies.
    """
    if len(timestamps) < 2:
        return {
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'anomalies': []
        }
    
    # Calculate deltas between consecutive frames
    deltas_with_info = []
    for i in range(len(timestamps) - 1):
        delta = timestamps[i+1] - timestamps[i]
        if delta >= 0:  # Only include valid deltas
            deltas_with_info.append((i, delta, timestamps[i]))
    
    if not deltas_with_info:
        return {
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'anomalies': []
        }
    
    deltas = [d[1] for d in deltas_with_info]
    mean_delta = statistics.mean(deltas)
    median_delta = statistics.median(deltas)
    
    # Detect anomalies: frame times > 3x median
    anomaly_threshold = median_delta * 3 if median_delta > 0 else mean_delta * 3
    anomalies = [(idx, delta, ts) for idx, delta, ts in deltas_with_info
                 if delta > anomaly_threshold and anomaly_threshold > 0]
    
    return {
        'min': min(deltas),
        'max': max(deltas),
        'mean': mean_delta,
        'median': median_delta,
        'anomalies': anomalies
    }


def calculate_metric_stats(
    values: List[float],
    config: "ReportConfig",
    all_data_points: List[Dict[str, Any]] = None,
    metric_name: str = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for a single metric.
    
    Parameters:
        values: List of numeric values for this metric
        config: ReportConfig object with thresholds
        all_data_points: Optional full data points for outlier detection
        metric_name: Name of the metric being analyzed
    
    Returns:
        Dictionary with all statistics for this metric
    """
    n = len(values)
    if n == 0:
        return {
            'min': 0, 'max': 0, 'mean': 0, 'median': 0,
            'q1': 0, 'q3': 0, 'p90': 0, 'p95': 0, 'p99': 0,
            'stdev': 0, 'variance': 0, 'cv': 0,
            'ci_lower': 0, 'ci_upper': 0,
            'outliers_high': [], 'outliers_low': []
        }
    
    mean_val = statistics.mean(values)
    stdev_val = statistics.stdev(values) if n > 1 else 0
    variance_val = statistics.variance(values) if n > 1 else 0
    cv_val = (stdev_val / mean_val * 100) if mean_val > 0 else 0
    
    # Percentiles
    if n > 1:
        percentiles = statistics.quantiles(values, n=100)
        p90, p95, p99 = percentiles[89], percentiles[94], percentiles[98]
        quartiles = statistics.quantiles(values, n=4)
        q1, q3 = quartiles[0], quartiles[2]
    else:
        p90 = p95 = p99 = q1 = q3 = values[0]
    
    # Confidence interval
    ci = _calculate_confidence_interval(values)
    
    # Outlier detection
    sigma = config.thresholds.get('outlier_sigma', 2.0)
    outliers_high = []
    outliers_low = []
    if all_data_points and metric_name:
        outliers_high = [(i, p) for i, p in enumerate(all_data_points) 
                         if metric_name in p and p[metric_name] > mean_val + sigma * stdev_val]
        outliers_low = [(i, p) for i, p in enumerate(all_data_points) 
                        if metric_name in p and p[metric_name] < mean_val - sigma * stdev_val]
    
    return {
        'min': min(values),
        'max': max(values),
        'mean': mean_val,
        'median': statistics.median(values),
        'q1': q1,
        'q3': q3,
        'p90': p90,
        'p95': p95,
        'p99': p99,
        'stdev': stdev_val,
        'variance': variance_val,
        'cv': cv_val,
        'ci_lower': ci[0],
        'ci_upper': ci[1],
        'outliers_high': outliers_high,
        'outliers_low': outliers_low
    }


def analyze_performance_data(
    data_points: List[Dict[str, Any]],
    config: "ReportConfig",
    metrics: List[str],
    metric_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate statistics and identify hotspots from performance data.
    
    Parameters:
        data_points: List of parsed data points
        config: ReportConfig object with thresholds
        metrics: List of metric field names to analyze (e.g., ['draws', 'tris'])
        metric_config: Dict with:
            - timestamp_field: Field name for timestamps
            - identifier_field: Field name for item identifier
            - threshold_mapping: Maps metrics to threshold config keys
    
    Returns:
        dict: Statistical analysis results including high_load, low_load, 
              critical, frame_times, trends, etc.
    """
    if not data_points:
        raise ValueError("analyze_performance_data requires at least one data point")
    
    if not metrics:
        raise ValueError("metrics parameter is required")
    
    if not metric_config:
        raise ValueError("metric_config parameter is required")
    
    n = len(data_points)
    timestamp_field = metric_config.get('timestamp_field')
    identifier_field = metric_config.get('identifier_field')
    threshold_mapping = metric_config.get('threshold_mapping', {})
    
    if not timestamp_field:
        raise ValueError("metric_config must specify 'timestamp_field'")
    if not identifier_field:
        raise ValueError("metric_config must specify 'identifier_field'")
    
    indices = list(range(n))
    result = {'count': n}
    
    # Calculate statistics for each metric
    for metric in metrics:
        values = [p.get(metric, 0) for p in data_points]
        result[metric] = calculate_metric_stats(values, config, data_points, metric)
        
        # Calculate trend for this metric
        slope, intercept = _calculate_linear_regression(
            [float(i) for i in indices], [float(v) for v in values]
        )
        stdev = result[metric]['stdev']
        mean = result[metric]['mean']
        direction = _classify_trend(slope, stdev, mean)
        
        # Add trend info
        if 'trends' not in result:
            result['trends'] = {}
        result['trends'][metric] = {
            'slope': slope,
            'intercept': intercept,
            'direction': direction
        }
        
        # Add confidence intervals
        if 'confidence_intervals' not in result:
            result['confidence_intervals'] = {}
        result['confidence_intervals'][metric] = (
            result[metric]['ci_lower'],
            result[metric]['ci_upper']
        )
        
        # IQR and MAD outlier detection
        if 'outliers_iqr' not in result:
            result['outliers_iqr'] = {}
        if 'outliers_mad' not in result:
            result['outliers_mad'] = {}
        result['outliers_iqr'][metric] = _detect_outliers_iqr(values, indices)
        mad_threshold = config.thresholds.get('mad_threshold', 3.5)
        result['outliers_mad'][metric] = _detect_outliers_mad(values, indices, mad_threshold)
    
    # Frame time analysis
    timestamps = [p.get(timestamp_field, 0) for p in data_points]
    result['frame_times'] = calculate_frame_times(timestamps)
    
    # High-load and low-load detection
    high_load = []
    low_load = []
    
    for i, p in enumerate(data_points):
        is_high = False
        is_low = True
        
        for metric in metrics:
            if metric in threshold_mapping:
                high_key = threshold_mapping[metric].get('high')
                low_key = threshold_mapping[metric].get('low')
                
                high_threshold = config.thresholds.get(high_key) if high_key else None
                low_threshold = config.thresholds.get(low_key) if low_key else None
                
                val = p.get(metric, 0)
                if high_threshold is not None and val >= high_threshold:
                    is_high = True
                if low_threshold is not None and val >= low_threshold:
                    is_low = False
        
        if is_high:
            high_load.append((i, p))
        if is_low and not is_high:
            low_load.append((i, p))
    
    result['high_load'] = high_load
    result['low_load'] = low_load
    
    # Critical hotspot detection
    if len(metrics) >= 1:
        primary_metric = metrics[0]
        secondary_metric = metrics[1] if len(metrics) > 1 else None
        
        def score_point(i):
            p = data_points[i]
            score = p.get(primary_metric, 0)
            if secondary_metric:
                score += p.get(secondary_metric, 0) / 1000
            return score
        
        worst_idx = max(range(n), key=score_point)
        result['critical'] = (worst_idx, data_points[worst_idx])
    else:
        result['critical'] = (0, data_points[0])
    
    # Build outliers list for templates
    outliers_combined = []
    for metric in metrics:
        for idx, p in result[metric].get('outliers_high', []):
            mean = result[metric]['mean']
            stdev = result[metric]['stdev']
            if stdev > 0:
                zscore = (p.get(metric, 0) - mean) / stdev
            else:
                zscore = 0
            outlier_entry = {
                'index': idx,
                identifier_field: p.get(identifier_field, ''),
                **{m: p.get(m, 0) for m in metrics},
                'zscore': zscore
            }
            if outlier_entry not in outliers_combined:
                outliers_combined.append(outlier_entry)
    
    result['outliers'] = outliers_combined
    
    return result

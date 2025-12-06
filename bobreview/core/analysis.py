#!/usr/bin/env python3
"""
Statistical analysis utilities for BobReview.
"""

import math
import statistics
from typing import Dict, List, Any, Tuple, TYPE_CHECKING
from scipy import stats

if TYPE_CHECKING:
    from .config import ReportConfig


def _calculate_confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for the mean using t-distribution.
    
    Parameters:
        values: List of numeric values
        confidence: Confidence level (default 0.95 for 95% CI)
    
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    if len(values) < 2:
        mean_val = statistics.mean(values)
        return (mean_val, mean_val)
    
    n = len(values)
    mean_val = statistics.mean(values)
    stdev_val = statistics.stdev(values)
    
    # Use scipy's accurate t-distribution critical value
    # For a confidence level (e.g., 0.95), we need the (1 + confidence)/2 quantile
    # e.g., for 95% CI, we need the 0.975 quantile (two-tailed test)
    alpha = 1 - confidence
    df = n - 1
    t_critical = stats.t.ppf(1 - alpha / 2, df)
    
    margin_of_error = t_critical * (stdev_val / math.sqrt(n))
    return (mean_val - margin_of_error, mean_val + margin_of_error)


def _calculate_linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    Calculate simple linear regression slope and intercept.
    
    Parameters:
        x: Independent variable values
        y: Dependent variable values
    
    Returns:
        tuple: (slope, intercept)
    """
    if len(x) < 2 or len(x) != len(y):
        return (0.0, statistics.mean(y) if y else 0.0)
    
    n = len(x)
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    
    # Calculate slope
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    if denominator == 0:
        return (0.0, mean_y)
    
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    
    return (slope, intercept)


def _detect_outliers_iqr(values: List[float], indices: List[int]) -> List[Tuple[int, float]]:
    """
    Detect outliers using Interquartile Range (IQR) method.
    Outliers are values < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
    
    Parameters:
        values: List of numeric values
        indices: Corresponding indices for the values
    
    Returns:
        list: List of (index, value) tuples for outliers
    """
    if len(values) != len(indices):
        raise ValueError("values and indices must have the same length")
    
    if len(values) < 4:
        return []
    
    q1 = statistics.quantiles(values, n=4)[0]
    q3 = statistics.quantiles(values, n=4)[2]
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = [(idx, val) for idx, val in zip(indices, values)
                if val < lower_bound or val > upper_bound]
    
    return outliers


def _detect_outliers_mad(values: List[float], indices: List[int], threshold: float = 3.5) -> List[Tuple[int, float]]:
    """
    Detect outliers using Median Absolute Deviation (MAD) method.
    More robust than standard deviation for non-normal distributions.
    
    Parameters:
        values: List of numeric values
        indices: Corresponding indices for the values
        threshold: MAD threshold multiplier (default 3.5)
    
    Returns:
        list: List of (index, value) tuples for outliers
    """
    if len(values) != len(indices):
        raise ValueError("values and indices must have the same length")
    
    if len(values) < 3:
        return []
    
    median_val = statistics.median(values)
    deviations = [abs(v - median_val) for v in values]
    mad = statistics.median(deviations)
    
    # Avoid division by zero
    if mad == 0:
        return []
    
    # Modified z-scores
    modified_z_scores = [0.6745 * (val - median_val) / mad for val in values]
    
    outliers = [(idx, val) for idx, val, z_score in zip(indices, values, modified_z_scores)
                if abs(z_score) > threshold]
    
    return outliers


def _calculate_frame_times(timestamps: List[int]) -> Dict[str, Any]:
    """
    Calculate frame time statistics from timestamps.
    
    Parameters:
        timestamps: List of timestamps in temporal order (should be monotonically increasing)
    
    Returns:
        dict: Frame time statistics including min, max, mean, median, and anomalies.
              Anomalies are tuples of (frame_index, delta_time, timestamp) for frames
              with unusually long frame times (>3x median).
    """
    if len(timestamps) < 2:
        return {
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'anomalies': []
        }
    
    # Calculate deltas between consecutive frames with original indices
    deltas_with_info = []
    for i in range(len(timestamps) - 1):
        delta = timestamps[i+1] - timestamps[i]
        if delta >= 0:  # Only include valid (non-negative) deltas
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
    
    # Detect anomalies: frame times > 3x median (potential hitches)
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


def _classify_trend(slope: float, stdev: float, mean: float) -> str:
    """
    Classify trend direction based on slope magnitude relative to data variability.
    
    Parameters:
        slope: Linear regression slope
        stdev: Standard deviation of the data
        mean: Mean of the data
    
    Returns:
        str: 'improving', 'stable', or 'degrading'
    """
    if stdev == 0 or mean == 0:
        return 'stable'
    
    # Normalize slope relative to data scale
    # For performance metrics, negative slope = improving (lower is better)
    normalized_slope = slope / (stdev / 10)
    
    if normalized_slope < -0.1:
        return 'improving'
    elif normalized_slope > 0.1:
        return 'degrading'
    else:
        return 'stable'


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
        all_data_points: Optional full data points for z-score calculation
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
    
    indices = list(range(n))
    
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
    sigma = config.outlier_sigma
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


def analyze_data(
    data_points: List[Dict[str, Any]],
    config: "ReportConfig",
    metrics: List[str] = None,
    metric_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calculate statistics and identify hotspots from data.
    
    This function is metric-agnostic - it analyzes whatever metrics are specified.
    
    Parameters:
        data_points: List of parsed data points
        config: ReportConfig object with thresholds and parameters
        metrics: List of metric field names to analyze (default: ['draws', 'tris'])
        metric_config: Optional MetricConfig-like dict with:
            - timestamp_field: Field name for timestamps (default: 'ts')
            - identifier_field: Field name for item identifier (default: 'testcase')
            - threshold_mapping: Maps metrics to threshold config keys
    
    Returns:
        dict: Dictionary containing statistical analysis results for each metric,
              plus high_load, low_load, critical, frame_times, trends, etc.
    """
    if not data_points:
        raise ValueError("analyze_data requires at least one data point")
    
    # Defaults for backward compatibility
    if metrics is None:
        metrics = ['draws', 'tris']
    
    if metric_config is None:
        metric_config = {
            'timestamp_field': 'ts',
            'identifier_field': 'testcase',
            'threshold_mapping': {
                'draws': {
                    'high': 'high_load_draw_threshold',
                    'low': 'low_load_draw_threshold',
                    'soft_cap': 'draw_soft_cap',
                    'hard_cap': 'draw_hard_cap'
                },
                'tris': {
                    'high': 'high_load_tri_threshold',
                    'low': 'low_load_tri_threshold',
                    'soft_cap': 'tri_soft_cap',
                    'hard_cap': 'tri_hard_cap'
                }
            }
        }
    
    n = len(data_points)
    timestamp_field = metric_config.get('timestamp_field', 'ts')
    identifier_field = metric_config.get('identifier_field', 'testcase')
    threshold_mapping = metric_config.get('threshold_mapping', {})
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
        result['outliers_mad'][metric] = _detect_outliers_mad(values, indices, config.mad_threshold)
    
    # Frame time analysis using timestamp field
    timestamps = [p.get(timestamp_field, 0) for p in data_points]
    result['frame_times'] = _calculate_frame_times(timestamps)
    
    # High-load and low-load detection
    # Uses threshold_mapping to get thresholds dynamically
    high_load = []
    low_load = []
    
    for i, p in enumerate(data_points):
        is_high = False
        is_low = True
        
        for metric in metrics:
            if metric in threshold_mapping:
                high_key = threshold_mapping[metric].get('high')
                low_key = threshold_mapping[metric].get('low')
                
                high_threshold = getattr(config, high_key, None) if high_key else None
                low_threshold = getattr(config, low_key, None) if low_key else None
                
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
    
    # Critical hotspot detection - use first metric weighted more heavily
    if len(metrics) >= 1:
        primary_metric = metrics[0]
        secondary_metric = metrics[1] if len(metrics) > 1 else None
        
        def score_point(i):
            p = data_points[i]
            score = p.get(primary_metric, 0)
            if secondary_metric:
                # Weight secondary metric less (normalized by factor)
                score += p.get(secondary_metric, 0) / 1000
            return score
        
        worst_idx = max(range(n), key=score_point)
        result['critical'] = (worst_idx, data_points[worst_idx])
    else:
        result['critical'] = (0, data_points[0])
    
    # Build outliers list for templates (combined from all metrics)
    outliers_combined = []
    for metric in metrics:
        for idx, p in result[metric].get('outliers_high', []):
            # Calculate z-score
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


def format_data_table(
    data_points: List[Dict[str, Any]], max_rows: int | None = None
) -> str:
    """
    Render a list of data points as a markdown table suitable for embedding in prompts.
    
    Each data point is expected to be a mapping containing the keys: `testcase`, `draws`, `tris`, and `ts`. When `max_rows` is provided, the output is truncated to at most that many rows and a note is appended when truncation occurs.
    
    Parameters:
        data_points (List[Dict[str, Any]]): Sequence of data point dictionaries with keys `testcase`, `draws`, `tris`, and `ts`.
        max_rows (int, optional): Maximum number of rows to include; when omitted, all rows are included.
    
    Returns:
        str: A markdown-formatted table with columns "Index", "Test Case", "Draw Calls", "Triangles", and "Timestamp", or the string "No data available." if `data_points` is empty.
    """
    from .utils import format_number
    
    total_samples = len(data_points)
    display_points = data_points
    if max_rows is not None:
        display_points = data_points[:max_rows]
    
    if not display_points:
        return "No data available."
    
    # Create table header
    table = "| Index | Test Case | Draw Calls | Triangles | Timestamp |\n"
    table += "|-------|-----------|------------|-----------|----------|\n"
    
    # Add rows
    for idx, point in enumerate(display_points):
        table += f"| {idx} | {point['testcase']} | {point['draws']} | {format_number(point['tris'])} | {point['ts']} |\n"
    
    if max_rows is not None and total_samples > max_rows:
        table += f"\n(Showing first {max_rows} of {total_samples} total samples)"
    
    return table


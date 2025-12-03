#!/usr/bin/env python3
"""
Statistical analysis utilities for BobReview.
"""

import math
import statistics
from typing import Dict, List, Any, Tuple


def _calculate_confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for the mean using t-distribution approximation.
    
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
    
    # Use t-distribution critical value approximation
    # For 95% CI and n>30, t ≈ 1.96; for smaller n, use approximation
    if n > 30:
        t_critical = 1.96
    else:
        # Rough approximation: t_critical increases as n decreases
        # t(df=29, 0.975) ≈ 2.045, t(df=9, 0.975) ≈ 2.262, t(df=4, 0.975) ≈ 2.776
        t_critical = 2.0 + (30 - n) * 0.03
    
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
    if len(values) < 4:
        return []
    
    q1 = statistics.quantiles(values, n=4)[0]
    q3 = statistics.quantiles(values, n=4)[2]
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = [(indices[i], values[i]) for i in range(len(values)) 
                if values[i] < lower_bound or values[i] > upper_bound]
    
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
    if len(values) < 3:
        return []
    
    median_val = statistics.median(values)
    deviations = [abs(v - median_val) for v in values]
    mad = statistics.median(deviations)
    
    # Avoid division by zero
    if mad == 0:
        return []
    
    # Modified z-scores
    modified_z_scores = [0.6745 * (values[i] - median_val) / mad for i in range(len(values))]
    
    outliers = [(indices[i], values[i]) for i in range(len(values)) 
                if abs(modified_z_scores[i]) > threshold]
    
    return outliers


def _calculate_frame_times(timestamps: List[int]) -> Dict[str, Any]:
    """
    Calculate frame time statistics from timestamps.
    
    Parameters:
        timestamps: List of timestamps (sorted)
    
    Returns:
        dict: Frame time statistics including min, max, mean, median, and anomalies
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
    deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
    
    # Remove negative deltas (in case timestamps aren't properly sorted)
    deltas = [d for d in deltas if d >= 0]
    
    if not deltas:
        return {
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'anomalies': []
        }
    
    mean_delta = statistics.mean(deltas)
    median_delta = statistics.median(deltas)
    
    # Detect anomalies: frame times > 3x median (potential hitches)
    anomaly_threshold = median_delta * 3 if median_delta > 0 else mean_delta * 3
    anomalies = [(i, deltas[i]) for i in range(len(deltas)) 
                 if deltas[i] > anomaly_threshold and anomaly_threshold > 0]
    
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


def analyze_data(data_points: List[Dict[str, Any]], config) -> Dict[str, Any]:
    """
    Calculate statistics and identify hotspots from performance data.
    
    Parameters:
        data_points: List of parsed data points with 'draws', 'tris', etc.
        config: ReportConfig object with thresholds and parameters
    
    Returns:
        dict: Dictionary containing statistical analysis results including:
            - draws: Statistics for draw calls (min, max, mean, median, quartiles, percentiles, 
                     variance, CV, stdev, outliers)
            - tris: Statistics for triangle counts
            - frame_times: Frame time statistics and anomalies
            - confidence_intervals: 95% CI for draws and triangles
            - trends: Trend analysis with slope and direction
            - outliers_iqr: Outliers detected by IQR method
            - outliers_mad: Outliers detected by MAD method
            - high_load: List of high-load frames
            - low_load: List of low-load frames
            - critical: Critical hotspot (worst frame)
            - count: Total number of samples
    """
    if not data_points:
        raise ValueError("analyze_data requires at least one data point")
    
    n = len(data_points)
    draws = [p['draws'] for p in data_points]
    tris = [p['tris'] for p in data_points]
    timestamps = [p['ts'] for p in data_points]
    indices = list(range(n))
    
    # Basic statistics
    draw_mean = statistics.mean(draws)
    draw_stdev = statistics.stdev(draws) if n > 1 else 0
    draw_variance = statistics.variance(draws) if n > 1 else 0
    draw_cv = (draw_stdev / draw_mean * 100) if draw_mean > 0 else 0
    
    tri_mean = statistics.mean(tris)
    tri_stdev = statistics.stdev(tris) if n > 1 else 0
    tri_variance = statistics.variance(tris) if n > 1 else 0
    tri_cv = (tri_stdev / tri_mean * 100) if tri_mean > 0 else 0
    
    # Percentile analysis
    if n > 1:
        draw_percentiles = statistics.quantiles(draws, n=100)
        # P90 is at index 89 (90th percentile), P95 at 94, P99 at 98
        draw_p90 = draw_percentiles[89] if len(draw_percentiles) >= 90 else max(draws)
        draw_p95 = draw_percentiles[94] if len(draw_percentiles) >= 95 else max(draws)
        draw_p99 = draw_percentiles[98] if len(draw_percentiles) >= 99 else max(draws)
        
        tri_percentiles = statistics.quantiles(tris, n=100)
        tri_p90 = tri_percentiles[89] if len(tri_percentiles) >= 90 else max(tris)
        tri_p95 = tri_percentiles[94] if len(tri_percentiles) >= 95 else max(tris)
        tri_p99 = tri_percentiles[98] if len(tri_percentiles) >= 99 else max(tris)
    else:
        draw_p90 = draw_p95 = draw_p99 = draws[0]
        tri_p90 = tri_p95 = tri_p99 = tris[0]
    
    # Confidence intervals
    draw_ci = _calculate_confidence_interval(draws)
    tri_ci = _calculate_confidence_interval(tris)
    
    # Frame time analysis
    frame_times = _calculate_frame_times(sorted(timestamps))
    
    # Trend detection (using index as x-axis for temporal order)
    draw_slope, draw_intercept = _calculate_linear_regression(
        [float(i) for i in indices], [float(d) for d in draws]
    )
    tri_slope, tri_intercept = _calculate_linear_regression(
        [float(i) for i in indices], [float(t) for t in tris]
    )
    
    draw_trend_direction = _classify_trend(draw_slope, draw_stdev, draw_mean)
    tri_trend_direction = _classify_trend(tri_slope, tri_stdev, tri_mean)
    
    # Outlier detection (existing sigma method)
    sigma = config.outlier_sigma
    draw_outliers_high = [(i, p) for i, p in enumerate(data_points) 
                          if p['draws'] > draw_mean + sigma * draw_stdev]
    draw_outliers_low = [(i, p) for i, p in enumerate(data_points) 
                        if p['draws'] < draw_mean - sigma * draw_stdev]
    tri_outliers_high = [(i, p) for i, p in enumerate(data_points) 
                        if p['tris'] > tri_mean + sigma * tri_stdev]
    
    # IQR outlier detection
    draw_outliers_iqr = _detect_outliers_iqr(draws, indices)
    tri_outliers_iqr = _detect_outliers_iqr(tris, indices)
    
    # MAD outlier detection
    draw_outliers_mad = _detect_outliers_mad(draws, indices)
    tri_outliers_mad = _detect_outliers_mad(tris, indices)
    
    # High-load frames: configurable thresholds
    high_load = [(i, p) for i, p in enumerate(data_points) 
                 if p['draws'] >= config.high_load_draw_threshold or 
                    p['tris'] >= config.high_load_tri_threshold]
    
    # Low-load frames: configurable thresholds
    low_load = [(i, p) for i, p in enumerate(data_points) 
                if p['draws'] < config.low_load_draw_threshold and 
                   p['tris'] < config.low_load_tri_threshold]
    
    # Critical hotspot (worst frame)
    worst_idx = max(range(n), 
                    key=lambda i: data_points[i]['draws'] + data_points[i]['tris'] / 1000)
    critical = (worst_idx, data_points[worst_idx])
    
    return {
        'draws': {
            'min': min(draws), 
            'max': max(draws), 
            'mean': draw_mean, 
            'median': statistics.median(draws),
            'q1': statistics.quantiles(draws, n=4)[0] if n > 1 else draws[0],
            'q3': statistics.quantiles(draws, n=4)[2] if n > 1 else draws[0],
            'p90': draw_p90,
            'p95': draw_p95,
            'p99': draw_p99,
            'stdev': draw_stdev,
            'variance': draw_variance,
            'cv': draw_cv,
            'outliers_high': draw_outliers_high,
            'outliers_low': draw_outliers_low
        },
        'tris': {
            'min': min(tris), 
            'max': max(tris), 
            'mean': tri_mean, 
            'median': statistics.median(tris),
            'q1': statistics.quantiles(tris, n=4)[0] if n > 1 else tris[0],
            'q3': statistics.quantiles(tris, n=4)[2] if n > 1 else tris[0],
            'p90': tri_p90,
            'p95': tri_p95,
            'p99': tri_p99,
            'stdev': tri_stdev,
            'variance': tri_variance,
            'cv': tri_cv,
            'outliers_high': tri_outliers_high
        },
        'frame_times': frame_times,
        'confidence_intervals': {
            'draws': draw_ci,
            'tris': tri_ci
        },
        'trends': {
            'draws': {
                'slope': draw_slope,
                'intercept': draw_intercept,
                'direction': draw_trend_direction
            },
            'tris': {
                'slope': tri_slope,
                'intercept': tri_intercept,
                'direction': tri_trend_direction
            }
        },
        'outliers_iqr': {
            'draws': draw_outliers_iqr,
            'tris': tri_outliers_iqr
        },
        'outliers_mad': {
            'draws': draw_outliers_mad,
            'tris': tri_outliers_mad
        },
        'high_load': high_load,
        'low_load': low_load,
        'critical': critical,
        'count': n
    }


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


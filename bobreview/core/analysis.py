#!/usr/bin/env python3
"""
Statistical analysis utilities for BobReview.
"""

import math
import statistics
from typing import Dict, List, Any, Tuple, TYPE_CHECKING, Optional
from scipy import stats

if TYPE_CHECKING:
    from .config import Config


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
    # For metrics where lower is better, negative slope = improving
    normalized_slope = slope / (stdev / 10)
    
    if normalized_slope < -0.1:
        return 'improving'
    elif normalized_slope > 0.1:
        return 'degrading'
    else:
        return 'stable'




def format_data_table(
    data_points: List[Dict[str, Any]], 
    max_rows: Optional[int] = None,
    fields: Optional[List[str]] = None,
    field_labels: Optional[Dict[str, str]] = None
) -> str:
    """
    Render a list of data points as a markdown table suitable for embedding in prompts.
    
    Parameters:
        data_points: Sequence of data point dictionaries
        max_rows: Maximum number of rows to include; when omitted, all rows are included
        fields: List of field names to include as columns (default: all fields from first data point)
        field_labels: Dict mapping field names to display labels (default: field names as-is)
    
    Returns:
        str: A markdown-formatted table or "No data available." if `data_points` is empty.
    """
    from .utils import format_number
    
    total_samples = len(data_points)
    display_points = data_points
    if max_rows is not None:
        display_points = data_points[:max_rows]
    
    if not display_points:
        return "No data available."
    
    # Determine fields to display
    if fields is None:
        # Use all fields from first data point (excluding internal fields)
        first_point = display_points[0]
        fields = [k for k in first_point.keys() if not k.startswith('_')]
    
    if not fields:
        return "No data available."
    
    # Get labels (default to field names)
    if field_labels is None:
        field_labels = {}
    labels = {field: field_labels.get(field, field.replace('_', ' ').title()) for field in fields}
    
    # Create table header
    header_row = "| Index | " + " | ".join(labels.values()) + " |\n"
    separator_row = "|" + "|".join(["-------"] * (len(fields) + 1)) + "|\n"
    table = header_row + separator_row
    
    # Add rows
    for idx, point in enumerate(display_points):
        row_values = [str(idx)]
        for field in fields:
            value = point.get(field, '')
            # Format numbers nicely
            if isinstance(value, (int, float)):
                if isinstance(value, float) and value >= 1000:
                    value = format_number(int(value), 0)
                elif isinstance(value, int) and value >= 1000:
                    value = format_number(value, 0)
                else:
                    value = str(value)
            row_values.append(str(value))
        table += "| " + " | ".join(row_values) + " |\n"
    
    if max_rows is not None and total_samples > max_rows:
        table += f"\n(Showing first {max_rows} of {total_samples} total samples)"
    
    return table


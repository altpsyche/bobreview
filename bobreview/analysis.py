#!/usr/bin/env python3
"""
Statistical analysis utilities for BobReview.
"""

import statistics
from typing import Dict, List, Any


def analyze_data(data_points: List[Dict[str, Any]], config) -> Dict[str, Any]:
    """
    Calculate statistics and identify hotspots from performance data.
    
    Parameters:
        data_points: List of parsed data points with 'draws', 'tris', etc.
        config: ReportConfig object with thresholds and parameters
    
    Returns:
        dict: Dictionary containing statistical analysis results including:
            - draws: Statistics for draw calls (min, max, mean, median, quartiles, stdev, outliers)
            - tris: Statistics for triangle counts
            - high_load: List of high-load frames
            - low_load: List of low-load frames
            - critical: Critical hotspot (worst frame)
            - count: Total number of samples
    """
    if not data_points:
        raise ValueError("analyze_data requires at least one data point")
    
    draws = [p['draws'] for p in data_points]
    tris = [p['tris'] for p in data_points]
    
    draw_mean = statistics.mean(draws)
    draw_stdev = statistics.stdev(draws) if len(draws) > 1 else 0
    tri_mean = statistics.mean(tris)
    tri_stdev = statistics.stdev(tris) if len(tris) > 1 else 0
    
    # Identify outliers (>Nσ from mean)
    sigma = config.outlier_sigma
    draw_outliers_high = [(i, p) for i, p in enumerate(data_points) 
                          if p['draws'] > draw_mean + sigma * draw_stdev]
    draw_outliers_low = [(i, p) for i, p in enumerate(data_points) 
                        if p['draws'] < draw_mean - sigma * draw_stdev]
    tri_outliers_high = [(i, p) for i, p in enumerate(data_points) 
                        if p['tris'] > tri_mean + sigma * tri_stdev]
    
    # High-load frames: configurable thresholds
    high_load = [(i, p) for i, p in enumerate(data_points) 
                 if p['draws'] >= config.high_load_draw_threshold or 
                    p['tris'] >= config.high_load_tri_threshold]
    
    # Low-load frames: configurable thresholds
    low_load = [(i, p) for i, p in enumerate(data_points) 
                if p['draws'] < config.low_load_draw_threshold and 
                   p['tris'] < config.low_load_tri_threshold]
    
    # Critical hotspot (worst frame)
    worst_idx = max(range(len(data_points)), 
                    key=lambda i: data_points[i]['draws'] + data_points[i]['tris'] / 1000)
    critical = (worst_idx, data_points[worst_idx])
    
    return {
        'draws': {
            'min': min(draws), 
            'max': max(draws), 
            'mean': draw_mean, 
            'median': statistics.median(draws),
            'q1': statistics.quantiles(draws, n=4)[0] if len(draws) > 1 else draws[0],
            'q3': statistics.quantiles(draws, n=4)[2] if len(draws) > 1 else draws[0],
            'stdev': draw_stdev,
            'outliers_high': draw_outliers_high,
            'outliers_low': draw_outliers_low
        },
        'tris': {
            'min': min(tris), 
            'max': max(tris), 
            'mean': tri_mean, 
            'median': statistics.median(tris),
            'q1': statistics.quantiles(tris, n=4)[0] if len(tris) > 1 else tris[0],
            'q3': statistics.quantiles(tris, n=4)[2] if len(tris) > 1 else tris[0],
            'stdev': tri_stdev,
            'outliers_high': tri_outliers_high
        },
        'high_load': high_load,
        'low_load': low_load,
        'critical': critical,
        'count': len(data_points)
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


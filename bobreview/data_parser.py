#!/usr/bin/env python3
"""
Data parsing utilities for BobReview.

Generic utilities for working with parsed data points.
These functions work with any data structure returned by parsers.
"""

from typing import List, Dict, Any, Callable


def filter_data_points(
    data_points: List[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool]
) -> List[Dict[str, Any]]:
    """
    Filter data points using a predicate function.
    
    Parameters:
        data_points: List of data point dictionaries
        predicate: Function that takes a data point and returns True/False
    
    Returns:
        Filtered list of data points
    
    Example:
        # Filter points where 'value' > 100
        filtered = filter_data_points(points, lambda p: p.get('value', 0) > 100)
    """
    return [point for point in data_points if predicate(point)]


def extract_fields(
    data_points: List[Dict[str, Any]],
    fields: List[str],
    default: Any = None
) -> List[Dict[str, Any]]:
    """
    Extract specific fields from data points.
    
    Parameters:
        data_points: List of data point dictionaries
        fields: List of field names to extract
        default: Default value for missing fields
    
    Returns:
        List of dictionaries with only the specified fields
    
    Example:
        # Extract only 'name' and 'value' fields
        extracted = extract_fields(points, ['name', 'value'])
    """
    return [
        {field: point.get(field, default) for field in fields}
        for point in data_points
    ]


def sort_data_points(
    data_points: List[Dict[str, Any]],
    key_field: str,
    reverse: bool = False
) -> List[Dict[str, Any]]:
    """
    Sort data points by a field value.
    
    Parameters:
        data_points: List of data point dictionaries
        key_field: Field name to sort by
        reverse: If True, sort in descending order
    
    Returns:
        Sorted list of data points
    
    Example:
        # Sort by timestamp
        sorted_points = sort_data_points(points, 'timestamp')
    """
    return sorted(
        data_points,
        key=lambda p: p.get(key_field, 0),
        reverse=reverse
    )


def get_field_values(
    data_points: List[Dict[str, Any]],
    field: str
) -> List[Any]:
    """
    Extract all values for a specific field from data points.
    
    Parameters:
        data_points: List of data point dictionaries
        field: Field name to extract
    
    Returns:
        List of field values
    
    Example:
        # Get all timestamps
        timestamps = get_field_values(points, 'timestamp')
    """
    return [point.get(field) for point in data_points if field in point]


def normalize_field_name(field_name: str) -> str:
    """
    Normalize a field name to a standard format.
    
    Converts to lowercase and replaces spaces/underscores with underscores.
    
    Parameters:
        field_name: Original field name
    
    Returns:
        Normalized field name
    
    Example:
        normalize_field_name('Test Case') -> 'test_case'
        normalize_field_name('drawCalls') -> 'drawcalls'
    """
    return field_name.lower().replace(' ', '_').replace('-', '_')

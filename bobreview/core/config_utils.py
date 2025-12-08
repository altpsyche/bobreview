"""
Configuration utility functions.

Provides reusable functions for merging configuration objects.
"""

from typing import Any, Dict


def merge_config(target: Any, source: Dict[str, Any], prefix: str = "") -> None:
    """
    Merge source configuration dictionary into target object.
    
    For dict-like objects (including ThresholdConfig), merges all keys.
    For other objects, only sets existing attributes.
    
    Parameters:
        target: Target object to merge into (dict-like or object with attributes)
        source: Dictionary of configuration values to merge
        prefix: Optional prefix for logging/debugging
    """
    # Check if target is dict-like
    if isinstance(target, dict):
        target.update(source)
    else:
        # For objects, only set existing attributes
        for key, value in source.items():
            if hasattr(target, key):
                setattr(target, key, value)


def merge_nested_config(target: Any, source: Dict[str, Any]) -> None:
    """
    Merge nested configuration structure into target object.
    
    Handles nested dictionaries by recursively merging into nested attributes.
    
    Parameters:
        target: Target object to merge into
        source: Nested dictionary of configuration values
    """
    for key, value in source.items():
        if hasattr(target, key):
            if isinstance(value, dict) and hasattr(getattr(target, key), '__dict__'):
                # Nested object - merge recursively
                nested_target = getattr(target, key)
                if hasattr(nested_target, '__dict__'):
                    merge_nested_config(nested_target, value)
                else:
                    setattr(target, key, value)
            else:
                # Simple value - set directly
                setattr(target, key, value)


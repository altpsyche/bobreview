"""
Plugin utility functions.

Provides reusable functions for safely calling plugin methods and managing plugin lifecycle.
"""

from typing import Any, Optional
import logging

from ..core import log_warning

logger = logging.getLogger(__name__)


def safe_plugin_call(
    plugin: Any,
    method_name: str,
    *args,
    config: Optional[Any] = None,
    **kwargs
) -> Optional[Any]:
    """
    Safely call a plugin method with error handling.
    
    If the method doesn't exist or raises an exception, logs a warning and returns None.
    This prevents plugin errors from crashing the entire system.
    
    Parameters:
        plugin: Plugin instance
        method_name: Name of the method to call
        *args: Positional arguments to pass to the method
        config: Optional ReportConfig for logging (uses log_warning if provided)
        **kwargs: Keyword arguments to pass to the method
    
    Returns:
        Method return value, or None if method doesn't exist or raises an exception
    """
    try:
        method = getattr(plugin, method_name, None)
        if method is None:
            return None
        
        return method(*args, **kwargs)
    except Exception as e:
        plugin_name = getattr(plugin, 'name', str(plugin))
        error_msg = f"Plugin '{plugin_name}' {method_name} failed: {e}"
        
        if config:
            log_warning(error_msg, config)
        else:
            logger.warning(error_msg)
        
        return None


def call_plugin_lifecycle_hooks(
    plugins: list,
    hook_name: str,
    context: dict,
    config: Optional[Any] = None
) -> None:
    """
    Call a lifecycle hook on all plugins.
    
    Parameters:
        plugins: List of plugin instances
        hook_name: Name of the hook method (e.g., 'on_report_start')
        context: Context dictionary to pass to the hook
        config: Optional ReportConfig for logging
    """
    for plugin in plugins:
        safe_plugin_call(plugin, hook_name, context, config=config)


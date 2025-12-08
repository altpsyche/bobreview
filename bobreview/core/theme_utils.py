"""
Theme utility functions for accessing themes from the plugin registry.

These functions provide a convenient interface to get themes and generate
CSS variables, using the plugin registry as the source of truth.
"""

from typing import Optional
from .themes import ReportTheme, get_theme_css_variables as _get_theme_css_variables


def get_theme(theme_id: Optional[str] = None) -> Optional[ReportTheme]:
    """
    Get a theme from the plugin registry.
    
    Parameters:
        theme_id: Theme ID (e.g., 'dark', 'light'). If None, returns first available theme.
    
    Returns:
        ReportTheme instance or None if not found
    """
    from ..plugins import get_registry
    
    registry = get_registry()
    theme = registry.themes.get(theme_id)
    
    # If no theme found and no ID specified, try 'dark' as default
    if theme is None and theme_id is None:
        theme = registry.themes.get('dark')
    
    return theme


def get_theme_css_variables(theme_id: Optional[str] = None) -> str:
    """
    Generate CSS :root block with theme variables.
    
    Parameters:
        theme_id: Theme ID (e.g., 'dark', 'light'). If None, uses default theme.
    
    Returns:
        CSS string with :root { ... } block
    """
    theme = get_theme(theme_id)
    if not theme:
        return ''
    
    return _get_theme_css_variables(theme)


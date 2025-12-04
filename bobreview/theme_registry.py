"""
Report theme registry for modular HTML report styling.

This module provides a registry pattern for report themes,
allowing easy customization of colors, fonts, and styling.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ReportTheme:
    """
    Defines a complete visual theme for HTML reports.
    
    These values map directly to CSS custom properties (variables) in styles.css.
    
    Attributes:
        id: Unique identifier for the theme (e.g., 'dark', 'light')
        name: Human-readable theme name
        
        # Background colors
        bg: Main background color
        bg_elevated: Elevated surface background
        bg_soft: Soft/subtle background
        
        # Accent colors
        accent: Primary accent color (links, highlights)
        accent_soft: Soft accent (backgrounds, hover states)
        accent_strong: Strong accent (special highlights)
        
        # Text colors
        text_main: Primary text color
        text_soft: Secondary/muted text color
        
        # Status colors
        danger: Error/critical status
        warn: Warning status
        ok: Success/good status
        
        # Border and effects
        border_subtle: Subtle borders
        shadow_soft: Soft shadow for elevation
        radius_lg: Large border radius
        radius_md: Medium border radius
        
        # Fonts
        font_mono: Monospace font family
        font_sans: Sans-serif font family
    """
    id: str
    name: str
    
    # Backgrounds
    bg: str = '#070b10'
    bg_elevated: str = '#0e141b'
    bg_soft: str = '#151c26'
    
    # Accents
    accent: str = '#4ea1ff'
    accent_soft: str = 'rgba(78, 161, 255, 0.15)'
    accent_strong: str = '#ffb347'
    
    # Text
    text_main: str = '#f5f7fb'
    text_soft: str = '#a8b3c5'
    
    # Status colors
    danger: str = '#ff5c5c'
    warn: str = '#e6b35c'
    ok: str = '#4fd18b'
    
    # Borders and effects
    border_subtle: str = '#1e2835'
    shadow_soft: str = '0 18px 45px rgba(0, 0, 0, 0.55)'
    radius_lg: str = '12px'
    radius_md: str = '8px'
    
    # Fonts
    font_mono: str = '"SF Mono", Menlo, Consolas, monospace'
    font_sans: str = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    
    # Chart styling
    chart_grid_opacity: float = 0.5


# Global theme registry
_THEME_REGISTRY: Dict[str, ReportTheme] = {}

# Active theme (can be changed at runtime)
_active_theme_id: str = 'dark'


def register_theme(theme: ReportTheme) -> None:
    """Register a report theme."""
    _THEME_REGISTRY[theme.id] = theme


def get_theme(theme_id: Optional[str] = None) -> ReportTheme:
    """
    Get a theme by ID.
    
    If no theme_id provided, returns the active theme.
    Falls back to dark theme if not found.
    """
    if theme_id is None:
        theme_id = _active_theme_id
    return _THEME_REGISTRY.get(theme_id, _THEME_REGISTRY.get('dark'))


def set_active_theme(theme_id: str) -> bool:
    """
    Set the active theme.
    
    Returns True if theme exists, False otherwise.
    """
    global _active_theme_id
    if theme_id in _THEME_REGISTRY:
        _active_theme_id = theme_id
        return True
    return False


def get_all_themes() -> Dict[str, ReportTheme]:
    """Get all registered themes."""
    return _THEME_REGISTRY.copy()


def get_theme_css_variables(theme_id: Optional[str] = None) -> str:
    """
    Generate CSS :root block with theme variables.
    
    This can be used to override the default styles.css variables.
    
    Returns:
        CSS string with :root { ... } block
    """
    theme = get_theme(theme_id)
    if not theme:
        return ''
    
    return f""":root {{
  --bg: {theme.bg};
  --bg-elevated: {theme.bg_elevated};
  --bg-soft: {theme.bg_soft};
  --accent: {theme.accent};
  --accent-soft: {theme.accent_soft};
  --accent-strong: {theme.accent_strong};
  --text-main: {theme.text_main};
  --text-soft: {theme.text_soft};
  --border-subtle: {theme.border_subtle};
  --danger: {theme.danger};
  --warn: {theme.warn};
  --ok: {theme.ok};
  --mono: {theme.font_mono};
  --sans: {theme.font_sans};
  --radius-lg: {theme.radius_lg};
  --radius-md: {theme.radius_md};
  --shadow-soft: {theme.shadow_soft};
}}"""


# Register default dark theme
register_theme(ReportTheme(
    id='dark',
    name='Dark (Default)',
    bg='#070b10',
    bg_elevated='#0e141b',
    bg_soft='#151c26',
    accent='#4ea1ff',
    accent_soft='rgba(78, 161, 255, 0.15)',
    accent_strong='#ffb347',
    text_main='#f5f7fb',
    text_soft='#a8b3c5',
    border_subtle='#1e2835',
    danger='#ff5c5c',
    warn='#e6b35c',
    ok='#4fd18b'
))

# Register light theme
register_theme(ReportTheme(
    id='light',
    name='Light',
    bg='#f8f9fa',
    bg_elevated='#ffffff',
    bg_soft='#e9ecef',
    accent='#0066cc',
    accent_soft='rgba(0, 102, 204, 0.1)',
    accent_strong='#ff8c00',
    text_main='#212529',
    text_soft='#6c757d',
    border_subtle='#dee2e6',
    danger='#dc3545',
    warn='#ffc107',
    ok='#28a745',
    shadow_soft='0 4px 12px rgba(0, 0, 0, 0.1)'
))

# Register high contrast theme
register_theme(ReportTheme(
    id='high_contrast',
    name='High Contrast',
    bg='#000000',
    bg_elevated='#1a1a1a',
    bg_soft='#2d2d2d',
    accent='#00ffff',
    accent_soft='rgba(0, 255, 255, 0.2)',
    accent_strong='#ffff00',
    text_main='#ffffff',
    text_soft='#cccccc',
    border_subtle='#404040',
    danger='#ff0000',
    warn='#ffff00',
    ok='#00ff00'
))

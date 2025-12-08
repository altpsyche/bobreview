"""
Theme definitions and utilities for BobReview.

This module provides theme dataclasses and built-in theme definitions.
Themes are registered via the plugin registry, but the definitions live here.
"""

from dataclasses import dataclass
from typing import Optional


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
    danger_soft: str = 'rgba(255, 92, 92, 0.15)'
    warn: str = '#e6b35c'
    warn_soft: str = 'rgba(230, 179, 92, 0.15)'
    ok: str = '#4fd18b'
    ok_soft: str = 'rgba(79, 209, 139, 0.15)'
    
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


# Built-in theme definitions
DARK_THEME = ReportTheme(
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
    danger_soft='rgba(255, 92, 92, 0.15)',
    warn='#e6b35c',
    warn_soft='rgba(230, 179, 92, 0.15)',
    ok='#4fd18b',
    ok_soft='rgba(79, 209, 139, 0.15)'
)

LIGHT_THEME = ReportTheme(
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
    danger_soft='rgba(220, 53, 69, 0.1)',
    warn='#ffc107',
    warn_soft='rgba(255, 193, 7, 0.1)',
    ok='#28a745',
    ok_soft='rgba(40, 167, 69, 0.1)',
    shadow_soft='0 4px 12px rgba(0, 0, 0, 0.1)'
)

HIGH_CONTRAST_THEME = ReportTheme(
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
    danger_soft='rgba(255, 0, 0, 0.2)',
    warn='#ffff00',
    warn_soft='rgba(255, 255, 0, 0.2)',
    ok='#00ff00',
    ok_soft='rgba(0, 255, 0, 0.2)'
)

# All built-in themes (for easy iteration by plugins)
BUILTIN_THEMES = [DARK_THEME, LIGHT_THEME, HIGH_CONTRAST_THEME]


def get_theme_css_variables(theme: ReportTheme) -> str:
    """
    Generate CSS :root block with theme variables.
    
    This can be used to override the default styles.css variables.
    
    Parameters:
        theme: ReportTheme instance
    
    Returns:
        CSS string with :root { ... } block
    """
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
  --danger-soft: {theme.danger_soft};
  --warn: {theme.warn};
  --warn-soft: {theme.warn_soft};
  --ok: {theme.ok};
  --ok-soft: {theme.ok_soft};
  --mono: {theme.font_mono};
  --sans: {theme.font_sans};
  --radius-lg: {theme.radius_lg};
  --radius-md: {theme.radius_md};
  --shadow-soft: {theme.shadow_soft};
}}"""


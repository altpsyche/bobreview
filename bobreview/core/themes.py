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

# =============================================================================
# ADDITIONAL BUILT-IN THEMES (Scaffolder Presets)
# =============================================================================


# Ocean Theme - Teal/Cyan, Inter font
OCEAN_THEME = ReportTheme(
    id='ocean',
    name='Ocean Dark',
    bg='#0a192f',
    bg_elevated='#112240',
    bg_soft='#1d3557',
    accent='#64ffda',
    accent_soft='rgba(100, 255, 218, 0.15)',
    accent_strong='#7efff0',
    text_main='#ccd6f6',
    text_soft='#8892b0',
    border_subtle='#233554',
    ok='#64ffda',
    ok_soft='rgba(100, 255, 218, 0.15)',
    warn='#ffd93d',
    warn_soft='rgba(255, 217, 61, 0.15)',
    danger='#ff6b6b',
    danger_soft='rgba(255, 107, 107, 0.15)',
    font_sans='"Inter", system-ui, -apple-system, sans-serif',
    font_mono='"Fira Code", "SF Mono", Consolas, monospace',
)

# Purple Night Theme - Dracula-inspired
PURPLE_THEME = ReportTheme(
    id='purple',
    name='Purple Night',
    bg='#1a1625',
    bg_elevated='#2d2640',
    bg_soft='#3d3455',
    accent='#bd93f9',
    accent_soft='rgba(189, 147, 249, 0.15)',
    accent_strong='#d4b8ff',
    text_main='#f8f8f2',
    text_soft='#6272a4',
    border_subtle='#44475a',
    ok='#50fa7b',
    ok_soft='rgba(80, 250, 123, 0.15)',
    warn='#ffb86c',
    warn_soft='rgba(255, 184, 108, 0.15)',
    danger='#ff5555',
    danger_soft='rgba(255, 85, 85, 0.15)',
)

# Terminal Theme - GitHub-style green, JetBrains Mono
TERMINAL_THEME = ReportTheme(
    id='terminal',
    name='Terminal Green',
    bg='#0d1117',
    bg_elevated='#161b22',
    bg_soft='#21262d',
    accent='#39d353',
    accent_soft='rgba(57, 211, 83, 0.15)',
    accent_strong='#56d364',
    text_main='#c9d1d9',
    text_soft='#8b949e',
    border_subtle='#30363d',
    ok='#39d353',
    ok_soft='rgba(57, 211, 83, 0.15)',
    warn='#d29922',
    warn_soft='rgba(210, 153, 34, 0.15)',
    danger='#f85149',
    danger_soft='rgba(248, 81, 73, 0.15)',
    font_sans='"JetBrains Mono", "Cascadia Code", Consolas, monospace',
    font_mono='"JetBrains Mono", "Cascadia Code", Consolas, monospace',
)

# Sunset Theme - Warm orange tones, Outfit font
SUNSET_THEME = ReportTheme(
    id='sunset',
    name='Sunset Warm',
    bg='#1f1b24',
    bg_elevated='#2d2733',
    bg_soft='#3d3544',
    accent='#ff7b54',
    accent_soft='rgba(255, 123, 84, 0.15)',
    accent_strong='#ff9b7a',
    text_main='#f5f5f5',
    text_soft='#b0a8b9',
    border_subtle='#4a4458',
    ok='#7ed957',
    ok_soft='rgba(126, 217, 87, 0.15)',
    warn='#ffb347',
    warn_soft='rgba(255, 179, 71, 0.15)',
    danger='#ff6b6b',
    danger_soft='rgba(255, 107, 107, 0.15)',
    font_sans='"Outfit", "Poppins", system-ui, sans-serif',
    font_mono='"Source Code Pro", "Fira Code", monospace',
)

# All built-in themes
BUILTIN_THEMES = [
    DARK_THEME, 
    LIGHT_THEME, 
    HIGH_CONTRAST_THEME,
    OCEAN_THEME,
    PURPLE_THEME,
    TERMINAL_THEME,
    SUNSET_THEME,
]

# Theme lookup by ID
THEMES_BY_ID = {theme.id: theme for theme in BUILTIN_THEMES}


def get_theme_by_id(theme_id: str) -> Optional[ReportTheme]:
    """Get a built-in theme by its ID. Returns None if not found."""
    return THEMES_BY_ID.get(theme_id)


def get_available_themes() -> list:
    """Return list of available theme IDs."""
    return list(THEMES_BY_ID.keys())


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


def theme_to_dict(theme: ReportTheme) -> dict:
    """
    Convert a ReportTheme to a dict for template context.
    
    Parameters:
        theme: ReportTheme instance
    
    Returns:
        Dict with theme values for use in templates
    """
    if not theme:
        return {}
    
    return {
        "id": theme.id,
        "name": theme.name,
        "bg": theme.bg,
        "bg_elevated": theme.bg_elevated,
        "bg_soft": theme.bg_soft,
        "accent": theme.accent,
        "accent_soft": theme.accent_soft,
        "accent_strong": theme.accent_strong,
        "text_main": theme.text_main,
        "text_soft": theme.text_soft,
        "ok": theme.ok,
        "ok_soft": theme.ok_soft,
        "warn": theme.warn,
        "warn_soft": theme.warn_soft,
        "danger": theme.danger,
        "danger_soft": theme.danger_soft,
        "border": theme.border_subtle,
    }


def generate_theme_css(theme: ReportTheme) -> str:
    """
    Generate CSS content with :root variables from a theme.
    
    Used for runtime theme.css generation when linked_css=True.
    
    Parameters:
        theme: ReportTheme instance
        
    Returns:
        CSS string with :root variables
    """
    return f"""/* Generated theme: {theme.name} */
:root {{
    --bg: {theme.bg};
    --bg-elevated: {theme.bg_elevated};
    --bg-soft: {theme.bg_soft};
    --bg-hover: {theme.accent_soft};
    --accent: {theme.accent};
    --accent-soft: {theme.accent_soft};
    --accent-strong: {theme.accent_strong};
    --text-main: {theme.text_main};
    --text-soft: {theme.text_soft};
    --ok: {theme.ok};
    --ok-soft: {theme.ok_soft};
    --warn: {theme.warn};
    --warn-soft: {theme.warn_soft};
    --danger: {theme.danger};
    --danger-soft: {theme.danger_soft};
    --border: {theme.border_subtle};
    --border-subtle: rgba(255, 255, 255, 0.05);
    --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.3);
    --shadow-strong: 0 8px 32px rgba(0, 0, 0, 0.4);
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --font-family: {theme.font_sans};
    --font-mono: {theme.font_mono};
}}
"""

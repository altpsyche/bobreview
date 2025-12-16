"""
Theme infrastructure for BobReview.

Plugin-First Architecture:
- This module provides ONLY the theme infrastructure
- Plugins define ALL themes using ReportTheme or create_theme()
- Plugins register themes via helper.add_theme()
- No built-in themes in core
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Union, Literal
from pathlib import Path
from markupsafe import Markup


@dataclass
class ReportTheme:
    """
    Defines a complete visual theme for HTML reports.
    
    These values map directly to CSS custom properties (variables).
    All themes are standalone - no inheritance.
    
    Attributes:
        id: Unique identifier for the theme (e.g., 'my_dark')
        name: Human-readable theme name
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
    shadow_strong: str = '0 8px 32px rgba(0, 0, 0, 0.4)'
    radius_sm: str = '4px'
    radius_md: str = '8px'
    radius_lg: str = '12px'
    radius_xl: str = '16px'
    
    # Fonts
    font_mono: str = '"SF Mono", Menlo, Consolas, monospace'
    font_family: str = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    font_url: str = ''
    
    # Chart styling
    chart_grid_opacity: float = 0.5
    
    def __post_init__(self):
        """Validate theme after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate theme has required fields and valid values."""
        errors = []
        
        if not self.id or not isinstance(self.id, str) or not self.id.strip():
            errors.append("Theme 'id' is required and must be a non-empty string")
        
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            errors.append("Theme 'name' is required and must be a non-empty string")
        
        if self.id and isinstance(self.id, str):
            if not self.id.replace('_', '').replace('-', '').isalnum():
                errors.append(f"Theme 'id' '{self.id}' contains invalid characters")
        
        if errors:
            error_msg = f"Theme '{self.id}' validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)


# =============================================================================
# THEME REGISTRY
# =============================================================================

# Plugin-first: No built-in themes in core
# Plugins register themes via helper.add_theme()
_registered_themes: Dict[str, ReportTheme] = {}


def register_theme(theme: ReportTheme) -> None:
    """Register a theme (called by plugin system)."""
    _registered_themes[theme.id] = theme


def get_theme_by_id(theme_id: str) -> Optional[ReportTheme]:
    """Get a theme by ID from the registry."""
    return _registered_themes.get(theme_id)


def get_available_themes() -> list:
    """Return list of available theme IDs."""
    return list(_registered_themes.keys())


# =============================================================================
# CSS GENERATION
# =============================================================================

def get_theme_css_variables(theme: ReportTheme) -> str:
    """Generate CSS :root block with theme variables."""
    if not theme:
        return ''
    
    return f""":root {{
  /* Backgrounds */
  --bg: {theme.bg};
  --bg-elevated: {theme.bg_elevated};
  --bg-soft: {theme.bg_soft};
  
  /* Accents */
  --accent: {theme.accent};
  --accent-soft: {theme.accent_soft};
  --accent-strong: {theme.accent_strong};
  
  /* Text */
  --text-main: {theme.text_main};
  --text-soft: {theme.text_soft};
  
  /* Status Colors */
  --ok: {theme.ok};
  --ok-soft: {theme.ok_soft};
  --warn: {theme.warn};
  --warn-soft: {theme.warn_soft};
  --danger: {theme.danger};
  --danger-soft: {theme.danger_soft};
  
  /* Borders & Effects */
  --border-subtle: {theme.border_subtle};
  --shadow-soft: {theme.shadow_soft};
  --shadow-strong: {theme.shadow_strong};
  
  /* Border Radius */
  --radius-sm: {theme.radius_sm};
  --radius-md: {theme.radius_md};
  --radius-lg: {theme.radius_lg};
  --radius-xl: {theme.radius_xl};
  
  /* Fonts */
  --font-family: {theme.font_family};
  --font-mono: {theme.font_mono};
}}"""


def theme_to_dict(theme: ReportTheme) -> Dict[str, Any]:
    """Convert a ReportTheme to a dict for template context."""
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
        "border_subtle": theme.border_subtle,
        "shadow_soft": theme.shadow_soft,
        "shadow_strong": theme.shadow_strong,
        "radius_sm": theme.radius_sm,
        "radius_md": theme.radius_md,
        "radius_lg": theme.radius_lg,
        "radius_xl": theme.radius_xl,
        "font_family": theme.font_family,
        "font_mono": theme.font_mono,
        "font_url": theme.font_url,
    }


# =============================================================================
# THEME CREATION HELPER
# =============================================================================

def create_theme(
    id: str,
    name: str,
    *,
    accent: Optional[str] = None,
    bg: Optional[str] = None,
    text_main: Optional[str] = None,
    **overrides
) -> ReportTheme:
    """
    Create a custom theme easily.
    
    This is the recommended way for plugins to create themes.
    
    Parameters:
        id: Unique theme ID
        name: Display name
        accent: Primary accent color
        bg: Main background color
        text_main: Main text color
        **overrides: Any other ReportTheme fields to override
    
    Example:
        MY_THEME = create_theme(
            id='my_theme',
            name='My Theme',
            accent='#ff4444',
            bg='#1a1a2e',
        )
        helper.add_theme(MY_THEME)
    """
    kwargs: Dict[str, Any] = {'id': id, 'name': name}
    
    if accent is not None:
        kwargs['accent'] = accent
    if bg is not None:
        kwargs['bg'] = bg
    if text_main is not None:
        kwargs['text_main'] = text_main
    
    kwargs.update(overrides)
    return ReportTheme(**kwargs)


def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """
    Convert hex color to rgba string.
    
    Parameters:
        hex_color: Hex color like '#ff6b35'
        alpha: Transparency value 0.0 to 1.0
    
    Returns:
        RGBA string like 'rgba(255, 107, 53, 0.15)'
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'
    except (ValueError, IndexError):
        return f'rgba(128, 128, 128, {alpha})'


# =============================================================================
# THEME SYSTEM (Unified API)
# =============================================================================

class ThemeSystem:
    """Unified theme system - singleton for theme operations."""
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'ThemeSystem':
        if cls._instance is None:
            cls._instance = ThemeSystem()
        return cls._instance
    
    def get_theme(self, theme_id: Optional[str] = None) -> Optional[ReportTheme]:
        """Get a theme by ID."""
        if not theme_id:
            # Return first registered theme or None
            themes = list(_registered_themes.values())
            return themes[0] if themes else None
        return get_theme_by_id(theme_id)
    
    def resolve_from_config(self, theme_config) -> Optional[ReportTheme]:
        """Resolve theme from config (string ID or None for default)."""
        if theme_config is None:
            return self.get_theme()  # First registered theme
        if isinstance(theme_config, str):
            return self.get_theme(theme_config)
        if isinstance(theme_config, dict):
            raise TypeError("Theme config must be a string, not dict.")
        return self.get_theme()
    
    def get_css(self, theme_id: str, mode: Literal['embedded', 'linked'] = 'embedded', include_base: bool = True) -> Union[Markup, str]:
        """Get CSS for a theme."""
        from .html_utils import get_shared_css
        import logging
        
        theme = self.get_theme(theme_id)
        if not theme:
            logging.getLogger(__name__).warning(f"Theme '{theme_id}' not found")
            return ''
        
        theme_css = get_theme_css_variables(theme)
        
        if mode == 'linked':
            return theme_css
        
        if include_base:
            base_css = get_shared_css()
            return Markup(f"<style>\n{base_css}\n{theme_css}\n</style>")
        
        return Markup(f"<style>\n{theme_css}\n</style>")
    
    def get_theme_dict(self, theme_id: str) -> Dict[str, Any]:
        """Get theme as dict for templates."""
        theme = self.get_theme(theme_id)
        return theme_to_dict(theme) if theme else {}
    
    def generate_theme_css_file(self, theme_id: str, output_path: Path) -> None:
        """Generate theme.css file for linked mode."""
        theme = self.get_theme(theme_id)
        if theme:
            css = get_theme_css_variables(theme)
            output_path.write_text(css, encoding='utf-8')


# Convenience functions
def get_theme_system() -> ThemeSystem:
    """Get the global ThemeSystem instance."""
    return ThemeSystem.get_instance()


def get_theme_css(theme_id: Optional[str] = None, mode: Literal['embedded', 'linked'] = 'embedded', include_base: bool = True) -> Union[Markup, str]:
    """Get CSS for a theme."""
    if not theme_id:
        themes = get_available_themes()
        if themes:
            theme_id = themes[0]
        else:
            return ''
    return get_theme_system().get_css(theme_id, mode, include_base)

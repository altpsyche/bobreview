"""
Theme definitions and utilities for BobReview.

This module provides theme dataclasses and built-in theme definitions.
Themes are registered via the plugin registry, but the definitions live here.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ReportTheme:
    """
    Defines a complete visual theme for HTML reports.
    
    These values map directly to CSS custom properties (variables) in styles.css.
    
    Supports theme inheritance via the `extends` parameter, allowing themes to
    inherit from other themes and override specific variables.
    
    Attributes:
        id: Unique identifier for the theme (e.g., 'dark', 'light')
        name: Human-readable theme name
        extends: Optional theme ID to inherit from (for modular themes)
        overrides: Optional dict of variable overrides (alternative to setting fields)
        
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
        font_family: Sans-serif font family
    """
    id: str
    name: str
    
    # Theme inheritance (modular)
    extends: Optional[str] = None
    overrides: Dict[str, Any] = field(default_factory=dict)
    
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
    # Google Fonts URL for loading web fonts (optional - only needed for web fonts)
    font_url: str = ''
    
    # Chart styling
    chart_grid_opacity: float = 0.5
    
    def __post_init__(self):
        """Apply overrides after initialization and validate theme."""
        if self.overrides:
            for key, value in self.overrides.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Validate required fields
        self._validate()
    
    def _validate(self):
        """Validate theme has required fields and valid values."""
        errors = []
        
        # Required fields
        if not self.id or not isinstance(self.id, str) or not self.id.strip():
            errors.append("Theme 'id' is required and must be a non-empty string")
        
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            errors.append("Theme 'name' is required and must be a non-empty string")
        
        # Validate id format (should be alphanumeric with underscores/hyphens)
        if self.id and isinstance(self.id, str):
            if not self.id.replace('_', '').replace('-', '').isalnum():
                errors.append(f"Theme 'id' '{self.id}' contains invalid characters. Use alphanumeric, underscore, or hyphen only.")
        
        # Validate extends reference (if set)
        if self.extends is not None:
            if not isinstance(self.extends, str) or not self.extends.strip():
                errors.append("Theme 'extends' must be a non-empty string if provided")
            elif self.extends == self.id:
                errors.append(f"Theme '{self.id}' cannot extend itself")
        
        # Validate overrides (if set)
        if self.overrides is not None:
            if not isinstance(self.overrides, dict):
                errors.append("Theme 'overrides' must be a dictionary if provided")
            else:
                # Check that override keys are valid theme fields
                valid_fields = {f.name for f in self.__dataclass_fields__.values()}
                invalid_overrides = [k for k in self.overrides.keys() if k not in valid_fields]
                if invalid_overrides:
                    errors.append(f"Theme 'overrides' contains invalid fields: {', '.join(invalid_overrides)}")
        
        if errors:
            error_msg = f"Theme '{self.id}' validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)


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
    ok_soft='rgba(79, 209, 139, 0.15)',
    font_family='"Plus Jakarta Sans", system-ui, -apple-system, sans-serif',
    font_mono='"JetBrains Mono", "SF Mono", Consolas, monospace',
    font_url='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
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
    shadow_soft='0 4px 12px rgba(0, 0, 0, 0.1)',
    font_family='"Inter", system-ui, -apple-system, sans-serif',
    font_mono='"Fira Code", "SF Mono", Consolas, monospace',
    font_url='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap',
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
    ok_soft='rgba(0, 255, 0, 0.2)',
    # High contrast uses system fonts for maximum compatibility
    font_family='system-ui, -apple-system, "Segoe UI", sans-serif',
    font_mono='Consolas, "Courier New", monospace',
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
    font_family='"Inter", system-ui, -apple-system, sans-serif',
    font_mono='"Fira Code", "SF Mono", Consolas, monospace',
    font_url='https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap',
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
    font_family='"Fira Code", system-ui, sans-serif',
    font_mono='"Fira Code", "SF Mono", Consolas, monospace',
    font_url='https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap',
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
    font_family='"JetBrains Mono", "Cascadia Code", Consolas, monospace',
    font_mono='"JetBrains Mono", "Cascadia Code", Consolas, monospace',
    font_url='https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap',
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
    font_family='"Outfit", "Poppins", system-ui, sans-serif',
    font_mono='"Source Code Pro", "Fira Code", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Source+Code+Pro:wght@400;500;600&display=swap',
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


def resolve_theme(theme: ReportTheme, theme_registry: Optional[Any] = None, visited: Optional[set] = None) -> ReportTheme:
    """
    Resolve theme inheritance and return a fully resolved theme.
    
    If theme extends another theme, inherits all values from parent and
    applies overrides. Handles multi-level inheritance.
    
    Parameters:
        theme: ReportTheme instance (may have extends/overrides)
        theme_registry: Optional registry to look up parent themes
                       (if None, uses built-in themes)
        visited: Set of theme IDs already visited (for circular inheritance detection)
    
    Returns:
        Resolved ReportTheme with all inheritance applied
    
    Raises:
        ValueError: If circular inheritance is detected
    """
    if not theme.extends:
        return theme
    
    # Initialize visited set if not provided (first call)
    if visited is None:
        visited = set()
    
    # Check for circular inheritance
    if theme.id in visited:
        cycle = ' -> '.join(sorted(visited)) + f' -> {theme.id}'
        raise ValueError(
            f"Circular theme inheritance detected: {cycle}. "
            f"Theme '{theme.id}' extends '{theme.extends}' which creates a cycle."
        )
    
    # Add current theme to visited set
    visited.add(theme.id)
    
    # Get parent theme
    if theme_registry:
        parent = theme_registry.get(theme.extends)
    else:
        parent = get_theme_by_id(theme.extends)
    
    if not parent:
        # Parent not found, return theme as-is (but warn)
        import warnings
        warnings.warn(
            f"Theme '{theme.id}' extends '{theme.extends}' but parent theme not found. "
            f"Returning theme without inheritance.",
            UserWarning,
            stacklevel=2
        )
        return theme
    
    # Resolve parent first (handle multi-level inheritance)
    # Pass visited set to detect cycles
    resolved_parent = resolve_theme(parent, theme_registry, visited.copy())
    
    # Create new theme with parent values, overridden by child's EXPLICIT overrides
    from dataclasses import asdict
    parent_dict = asdict(resolved_parent)
    
    # Start with parent values
    merged = {**parent_dict}
    
    # Apply only the child's explicit overrides (not all default values)
    # Child can specify overrides via the 'overrides' dict
    if theme.overrides:
        merged.update(theme.overrides)
    
    # Also preserve child's id and name
    merged['id'] = theme.id
    merged['name'] = theme.name
    
    # Remove extends/overrides from merged dict (they're not needed in resolved theme)
    merged.pop('extends', None)
    merged.pop('overrides', None)
    
    # Create resolved theme
    return ReportTheme(**merged)


def get_theme_css_variables(theme: ReportTheme) -> str:
    """
    Generate CSS :root block with theme variables.
    
    This generates a complete set of CSS custom properties that override
    the default styles.css variables.
    
    Parameters:
        theme: ReportTheme instance
    
    Returns:
        CSS string with :root { ... } block
    """
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
  
  /* Font Weights */
  --weight-light: 300;
  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
}}"""


def theme_to_dict(theme: ReportTheme) -> dict:
    """
    Convert a ReportTheme to a dict for template context.
    
    Templates can use these values for dynamic styling.
    
    Parameters:
        theme: ReportTheme instance
    
    Returns:
        Dict with theme values for use in templates
    """
    if not theme:
        return {}
    
    return {
        # Core theme info
        "id": theme.id,
        "name": theme.name,
        
        # Backgrounds
        "bg": theme.bg,
        "bg_elevated": theme.bg_elevated,
        "bg_soft": theme.bg_soft,
        
        # Accents
        "accent": theme.accent,
        "accent_soft": theme.accent_soft,
        "accent_strong": theme.accent_strong,
        
        # Text
        "text_main": theme.text_main,
        "text_soft": theme.text_soft,
        
        # Status colors
        "ok": theme.ok,
        "ok_soft": theme.ok_soft,
        "warn": theme.warn,
        "warn_soft": theme.warn_soft,
        "danger": theme.danger,
        "danger_soft": theme.danger_soft,
        
        # Borders & Effects
        "border_subtle": theme.border_subtle,
        "shadow_soft": theme.shadow_soft,
        "shadow_strong": theme.shadow_strong,
        "radius_sm": theme.radius_sm,
        "radius_md": theme.radius_md,
        "radius_lg": theme.radius_lg,
        "radius_xl": theme.radius_xl,
        
        # Fonts
        "font_family": theme.font_family,
        "font_mono": theme.font_mono,
        "font_url": theme.font_url,
    }




# =============================================================================
# THEME CREATION HELPERS
# =============================================================================


def create_theme(
    id: str,
    name: str,
    *,
    base: str = 'dark',
    accent: Optional[str] = None,
    bg: Optional[str] = None,
    text_main: Optional[str] = None,
    **overrides
) -> ReportTheme:
    """
    Create a custom theme easily by extending a base theme.
    
    This is the recommended way for plugins to create themes.
    Only specify the colors you want to change.
    
    Parameters:
        id: Unique theme ID (e.g., 'my_plugin_theme')
        name: Display name (e.g., 'My Plugin Theme')
        base: Base theme to extend ('dark', 'light', 'ocean', etc.)
        accent: Primary accent color (optional)
        bg: Main background color (optional)
        text_main: Main text color (optional)
        **overrides: Any other ReportTheme fields to override
    
    Returns:
        ReportTheme instance
    
    Example:
        # Create a red-accent dark theme
        MY_THEME = create_theme(
            id='my_red_theme',
            name='My Red Theme',
            base='dark',
            accent='#ff4444',
            accent_soft='rgba(255, 68, 68, 0.15)',
        )
        
        # In plugin on_load:
        helper.add_theme(MY_THEME)
    """
    # Get base theme
    base_theme = get_theme_by_id(base)
    if not base_theme:
        base_theme = DARK_THEME
    
    # Build overrides dict
    theme_overrides = dict(overrides)
    if accent is not None:
        theme_overrides['accent'] = accent
    if bg is not None:
        theme_overrides['bg'] = bg
    if text_main is not None:
        theme_overrides['text_main'] = text_main
    
    # Create theme extending base
    return ReportTheme(
        id=id,
        name=name,
        extends=base,
        overrides=theme_overrides,
    )


def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """
    Convert hex color to rgba string.
    
    Utility function for plugin authors to generate soft/transparent versions
    of accent colors for their custom themes.
    
    Parameters:
        hex_color: Hex color like '#ff6b35' or 'ff6b35'
        alpha: Transparency value from 0.0 to 1.0 (default: 0.15)
    
    Returns:
        RGBA string like 'rgba(255, 107, 53, 0.15)'
    
    Example:
        theme = create_theme(
            id='custom',
            name='Custom',
            accent='#ff6b35',
            accent_soft=hex_to_rgba('#ff6b35', 0.15),
        )
    """
    # Validate alpha
    if not (0.0 <= alpha <= 1.0):
        raise ValueError(f"alpha must be between 0.0 and 1.0, got {alpha}")
    
    hex_color = hex_color.lstrip('#')
    
    # Normalize 3-char to 6-char
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    
    # Validate length and content
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color '{hex_color}': expected 3 or 6 hex digits")
    if any(c not in "0123456789abcdefABCDEF" for c in hex_color):
        raise ValueError(f"Invalid hex color '{hex_color}': contains non-hex characters")
    
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

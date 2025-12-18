"""
Generator for theme.py file.

Creates premium, production-ready themes:
- MIDNIGHT: Deep blue with electric cyan accents
- AURORA: Purple/magenta with northern lights feel
- SUNSET: Warm amber/orange gradients
- FROST: Clean icy light theme
"""


def generate_theme_module(name: str, safe_name: str, class_name: str) -> str:
    """
    Generate theme.py with premium, production-ready themes.
    
    Includes 4 stunning themes:
    - MIDNIGHT: Deep blue with electric cyan accents
    - AURORA: Purple/magenta with northern lights feel
    - SUNSET: Warm amber/orange gradients
    - FROST: Clean icy light theme
    """
    return f'''"""
Premium Themes for {name} Plugin.

Four stunning themes with unique personalities:

1. MIDNIGHT - Deep blue with electric cyan accents (default)
2. AURORA - Purple/magenta with northern lights glow
3. SUNSET - Warm amber and orange gradients
4. FROST - Clean, icy light theme

Themes are fully self-contained - no core imports needed.
"""

from dataclasses import dataclass


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
        return f'rgba({{r}}, {{g}}, {{b}}, {{alpha}})'
    except (ValueError, IndexError):
        # Invalid color, using gray fallback
        # In non-production contexts, consider logging the error or raising it
        # for better debugging: raise ValueError(f"Invalid hex color: {{hex_color}}")
        return f'rgba(128, 128, 128, {{alpha}})'


@dataclass
class ReportTheme:
    """
    Theme definition for plugin reports.
    
    All themes are standalone - define every value explicitly.
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


def get_theme_css_variables(theme: ReportTheme) -> str:
    """Generate CSS :root block with theme variables."""
    return f""":root {{{{
  /* Backgrounds */
  --bg: {{theme.bg}};
  --bg-elevated: {{theme.bg_elevated}};
  --bg-soft: {{theme.bg_soft}};
  
  /* Accents */
  --accent: {{theme.accent}};
  --accent-soft: {{theme.accent_soft}};
  --accent-strong: {{theme.accent_strong}};
  
  /* Text */
  --text-main: {{theme.text_main}};
  --text-soft: {{theme.text_soft}};
  
  /* Status Colors */
  --ok: {{theme.ok}};
  --ok-soft: {{theme.ok_soft}};
  --warn: {{theme.warn}};
  --warn-soft: {{theme.warn_soft}};
  --danger: {{theme.danger}};
  --danger-soft: {{theme.danger_soft}};
  
  /* Borders & Effects */
  --border-subtle: {{theme.border_subtle}};
  --shadow-soft: {{theme.shadow_soft}};
  --shadow-strong: {{theme.shadow_strong}};
  
  /* Border Radius */
  --radius-sm: {{theme.radius_sm}};
  --radius-md: {{theme.radius_md}};
  --radius-lg: {{theme.radius_lg}};
  --radius-xl: {{theme.radius_xl}};
  
  /* Fonts */
  --font-family: {{theme.font_family}};
  --font-mono: {{theme.font_mono}};
}}}}"""


# =============================================================================
# 🌙 MIDNIGHT THEME - Deep blue with electric cyan
# =============================================================================
# Perfect for: Technical reports, developer dashboards, code analysis
# Font: JetBrains Mono + Inter - clean, technical, highly readable

{safe_name.upper()}_MIDNIGHT = ReportTheme(
    id='{safe_name}_midnight',
    name='{class_name} Midnight',
    
    # Deep blue-black backgrounds
    bg='#0a0f1a',
    bg_elevated='#111827',
    bg_soft='#1e293b',
    
    # Electric cyan accents
    accent='#22d3ee',
    accent_soft=hex_to_rgba('#22d3ee', 0.15),
    accent_strong='#67e8f9',
    
    # Cool gray text
    text_main='#f1f5f9',
    text_soft='#94a3b8',
    
    # Vibrant status colors
    ok='#4ade80',
    ok_soft=hex_to_rgba('#4ade80', 0.15),
    warn='#facc15',
    warn_soft=hex_to_rgba('#facc15', 0.15),
    danger='#f87171',
    danger_soft=hex_to_rgba('#f87171', 0.15),
    
    # Sharp edges for technical feel
    border_subtle='#334155',
    shadow_soft='0 8px 32px rgba(0, 0, 0, 0.5)',
    shadow_strong='0 20px 60px rgba(0, 0, 0, 0.7)',
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='16px',
    
    # JetBrains Mono + Inter - technical, clean
    font_family='"Inter", "SF Pro Display", system-ui, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", "SF Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# 🌌 AURORA THEME - Purple/magenta with northern lights glow
# =============================================================================
# Perfect for: Creative projects, marketing reports, analytics dashboards
# Font: Space Grotesk + IBM Plex Mono - modern, geometric, stylish

{safe_name.upper()}_AURORA = ReportTheme(
    id='{safe_name}_aurora',
    name='{class_name} Aurora',
    
    # Deep purple-black backgrounds
    bg='#0c0a1d',
    bg_elevated='#13102a',
    bg_soft='#1e1839',
    
    # Vibrant magenta/pink accents
    accent='#e879f9',
    accent_soft=hex_to_rgba('#e879f9', 0.18),
    accent_strong='#f0abfc',
    
    # Soft lavender text
    text_main='#f5f3ff',
    text_soft='#a5b4fc',
    
    # Colorful neon status colors
    ok='#34d399',
    ok_soft=hex_to_rgba('#34d399', 0.15),
    warn='#fcd34d',
    warn_soft=hex_to_rgba('#fcd34d', 0.15),
    danger='#fb7185',
    danger_soft=hex_to_rgba('#fb7185', 0.15),
    
    # Soft glow effects
    border_subtle='#312e54',
    shadow_soft='0 10px 40px rgba(139, 92, 246, 0.2)',
    shadow_strong='0 25px 80px rgba(139, 92, 246, 0.35)',
    radius_sm='6px',
    radius_md='12px',
    radius_lg='18px',
    radius_xl='24px',
    
    # Space Grotesk + IBM Plex Mono - modern, geometric
    font_family='"Space Grotesk", "Outfit", system-ui, sans-serif',
    font_mono='"IBM Plex Mono", "Source Code Pro", monospace',
    font_url='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap',
    
    chart_grid_opacity=0.3,
)


# =============================================================================
# 🌅 SUNSET THEME - Warm amber and orange gradients
# =============================================================================
# Perfect for: Business reports, executive dashboards, warm presentations
# Font: DM Sans + JetBrains Mono - friendly, professional, approachable

{safe_name.upper()}_SUNSET = ReportTheme(
    id='{safe_name}_sunset',
    name='{class_name} Sunset',
    
    # Warm dark backgrounds with red undertones
    bg='#120c0c',
    bg_elevated='#1a1212',
    bg_soft='#271a1a',
    
    # Warm amber/orange accents
    accent='#fb923c',
    accent_soft=hex_to_rgba('#fb923c', 0.18),
    accent_strong='#fdba74',
    
    # Warm cream text
    text_main='#fef3e2',
    text_soft='#d4a574',
    
    # Fire-inspired status colors
    ok='#86efac',
    ok_soft=hex_to_rgba('#86efac', 0.15),
    warn='#fde047',
    warn_soft=hex_to_rgba('#fde047', 0.15),
    danger='#fca5a5',
    danger_soft=hex_to_rgba('#fca5a5', 0.15),
    
    # Warm, cozy effects
    border_subtle='#3d2a2a',
    shadow_soft='0 12px 40px rgba(251, 146, 60, 0.15)',
    shadow_strong='0 24px 70px rgba(251, 146, 60, 0.25)',
    radius_sm='6px',
    radius_md='10px',
    radius_lg='16px',
    radius_xl='24px',
    
    # DM Sans + JetBrains Mono - friendly, readable
    font_family='"DM Sans", "Nunito", "Poppins", system-ui, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", monospace',
    font_url='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# ❄️ FROST THEME - Clean, icy light theme
# =============================================================================
# Perfect for: Print-friendly reports, light mode preference, formal docs
# Font: Plus Jakarta Sans + Fira Code - elegant, modern, professional

{safe_name.upper()}_FROST = ReportTheme(
    id='{safe_name}_frost',
    name='{class_name} Frost',
    
    # Clean icy backgrounds
    bg='#f0f9ff',
    bg_elevated='#ffffff',
    bg_soft='#e0f2fe',
    
    # Cool blue accent
    accent='#0284c7',
    accent_soft=hex_to_rgba('#0284c7', 0.12),
    accent_strong='#0ea5e9',
    
    # Dark slate text
    text_main='#0f172a',
    text_soft='#475569',
    
    # Clear, vivid status
    ok='#16a34a',
    ok_soft=hex_to_rgba('#16a34a', 0.1),
    warn='#d97706',
    warn_soft=hex_to_rgba('#d97706', 0.1),
    danger='#dc2626',
    danger_soft=hex_to_rgba('#dc2626', 0.1),
    
    # Subtle, clean effects
    border_subtle='#bae6fd',
    shadow_soft='0 4px 20px rgba(14, 165, 233, 0.08)',
    shadow_strong='0 12px 40px rgba(14, 165, 233, 0.15)',
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='20px',
    
    # Plus Jakarta Sans + Fira Code - elegant, modern
    font_family='"Plus Jakarta Sans", "Outfit", "Inter", system-ui, sans-serif',
    font_mono='"Fira Code", "JetBrains Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap',
    
    chart_grid_opacity=0.25,
)


# =============================================================================
# DEFAULT THEME ALIAS
# =============================================================================
# Point to midnight as the default theme for this plugin

{safe_name.upper()}_THEME = {safe_name.upper()}_MIDNIGHT


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Import themes in your executor or templates:
#        from .theme import {safe_name.upper()}_MIDNIGHT, get_theme_css_variables
#
# 2. Generate CSS variables:
#        theme_css = get_theme_css_variables({safe_name.upper()}_MIDNIGHT)
#
# 3. Available themes:
#        {safe_name}_midnight  - Deep blue + cyan (default)
#        {safe_name}_aurora    - Purple + magenta
#        {safe_name}_sunset    - Warm amber + orange
#        {safe_name}_frost     - Clean light blue
'''
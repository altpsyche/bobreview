"""
Generator for theme.py file.

Creates premium, production-ready themes:
- DUNGEON: D&D fantasy parchment with gold accents (default)
- MIDNIGHT: Deep blue with electric cyan accents
- AURORA: Purple/magenta with northern lights feel
- SUNSET: Warm amber/orange gradients
- FROST: Clean icy light theme
"""


def generate_theme_module(name: str, safe_name: str, class_name: str) -> str:
    """
    Generate theme.py with premium, production-ready themes.
    
    Includes 5 stunning themes:
    - DUNGEON: D&D fantasy parchment with gold accents (default)
    - MIDNIGHT: Deep blue with electric cyan accents
    - AURORA: Purple/magenta with northern lights feel
    - SUNSET: Warm amber/orange gradients
    - FROST: Clean icy light theme
    """
    return f'''"""
Premium Themes for {name} Plugin.

Five stunning themes with unique personalities:

1. DUNGEON - D&D fantasy parchment with gold accents (default)
2. MIDNIGHT - Deep blue with electric cyan accents
3. AURORA - Purple/magenta with northern lights glow
4. SUNSET - Warm amber and orange gradients
5. FROST - Clean, icy light theme

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
# MIDNIGHT THEME - Arcane Tower / Wizard's Study
# =============================================================================
# Perfect for: Magic-themed reports, arcane studies, mystical dashboards
# Font: Cinzel + Cormorant Garamond - elegant, mystical, scholarly

{safe_name.upper()}_MIDNIGHT = ReportTheme(
    id='{safe_name}_midnight',
    name='{class_name} Midnight',
    
    # Deep arcane blue-black backgrounds
    bg='#0a0f1a',
    bg_elevated='#111827',
    bg_soft='#1e293b',
    
    # Electric cyan accents - arcane energy
    accent='#22d3ee',
    accent_soft=hex_to_rgba('#22d3ee', 0.15),
    accent_strong='#67e8f9',
    
    # Cool silvery text
    text_main='#f1f5f9',
    text_soft='#94a3b8',
    
    # Magical status colors
    ok='#4ade80',
    ok_soft=hex_to_rgba('#4ade80', 0.15),
    warn='#facc15',
    warn_soft=hex_to_rgba('#facc15', 0.15),
    danger='#f87171',
    danger_soft=hex_to_rgba('#f87171', 0.15),
    
    # Sharp mystical edges
    border_subtle='#334155',
    shadow_soft='0 8px 32px rgba(0, 0, 0, 0.5)',
    shadow_strong='0 20px 60px rgba(0, 0, 0, 0.7)',
    radius_sm='2px',
    radius_md='4px',
    radius_lg='6px',
    radius_xl='8px',
    
    # Cinzel + Cormorant - elegant fantasy serif
    font_family='"Cinzel", "Cormorant Garamond", "Palatino Linotype", serif',
    font_mono='"Courier New", "Lucida Console", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Cormorant+Garamond:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)

# =============================================================================
# DUNGEON THEME - D&D Fantasy Parchment Style
# =============================================================================
# Perfect for: D&D character sheets, fantasy games, medieval/tavern aesthetic
# Font: MedievalSharp + Cinzel - authentic medieval fantasy feel

{safe_name.upper()}_DUNGEON = ReportTheme(
    id='{safe_name}_dungeon',
    name='{class_name} Dungeon',
    
    # Parchment/leather backgrounds - warm aged paper feel
    bg='#1a1410',           # Dark burnt umber
    bg_elevated='#2a221a',  # Aged leather brown  
    bg_soft='#3d3326',      # Warm parchment shadow
    
    # Gold and crimson accents - royal fantasy colors
    accent='#d4a439',       # Antique gold
    accent_soft=hex_to_rgba('#d4a439', 0.2),
    accent_strong='#f5d67a',  # Bright gold highlight
    
    # Parchment text - aged paper colors
    text_main='#f4e8c1',    # Cream parchment
    text_soft='#c4a35a',    # Faded ink
    
    # D&D-inspired status colors
    ok='#5cb85c',           # Potion green
    ok_soft=hex_to_rgba('#5cb85c', 0.2),
    warn='#f0ad4e',         # Warning amber
    warn_soft=hex_to_rgba('#f0ad4e', 0.2),
    danger='#c9302c',       # Blood red
    danger_soft=hex_to_rgba('#c9302c', 0.2),
    
    # Ornate frame borders
    border_subtle='#5c4d3d',  # Weathered wood
    shadow_soft='0 8px 32px rgba(0, 0, 0, 0.6)',
    shadow_strong='0 20px 60px rgba(0, 0, 0, 0.8)',
    radius_sm='2px',        # Sharp medieval corners
    radius_md='4px',
    radius_lg='6px',
    radius_xl='8px',
    
    # MedievalSharp for titles, Cinzel for body - authentic fantasy
    font_family='"Cinzel", "MedievalSharp", "Palatino Linotype", serif',
    font_mono='"Courier New", "Lucida Console", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=MedievalSharp&display=swap',
    
    chart_grid_opacity=0.25,
)

# =============================================================================
# AURORA THEME - Fey Court / Enchanted Forest
# =============================================================================
# Perfect for: Fey-themed reports, enchanted realms, mystical creatures
# Font: Cinzel + Spectral - ethereal, magical, otherworldly

{safe_name.upper()}_AURORA = ReportTheme(
    id='{safe_name}_aurora',
    name='{class_name} Aurora',
    
    # Deep enchanted purple backgrounds
    bg='#0c0a1d',
    bg_elevated='#13102a',
    bg_soft='#1e1839',
    
    # Vibrant fey magenta/pink accents
    accent='#e879f9',
    accent_soft=hex_to_rgba('#e879f9', 0.18),
    accent_strong='#f0abfc',
    
    # Soft ethereal lavender text
    text_main='#f5f3ff',
    text_soft='#a5b4fc',
    
    # Enchanted status colors
    ok='#34d399',
    ok_soft=hex_to_rgba('#34d399', 0.15),
    warn='#fcd34d',
    warn_soft=hex_to_rgba('#fcd34d', 0.15),
    danger='#fb7185',
    danger_soft=hex_to_rgba('#fb7185', 0.15),
    
    # Soft mystical glow effects
    border_subtle='#312e54',
    shadow_soft='0 10px 40px rgba(139, 92, 246, 0.2)',
    shadow_strong='0 25px 80px rgba(139, 92, 246, 0.35)',
    radius_sm='2px',
    radius_md='4px',
    radius_lg='6px',
    radius_xl='8px',
    
    # Cinzel + Spectral - ethereal fantasy serif
    font_family='"Cinzel", "Spectral", "Palatino Linotype", serif',
    font_mono='"Courier New", "Lucida Console", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Spectral:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.3,
)


# =============================================================================
# SUNSET THEME - Dragon's Lair / Infernal Realm
# =============================================================================
# Perfect for: Dragon/fire themed reports, infernal realms, battle records
# Font: Cinzel + EB Garamond - powerful, ancient, commanding

{safe_name.upper()}_SUNSET = ReportTheme(
    id='{safe_name}_sunset',
    name='{class_name} Sunset',
    
    # Deep volcanic dark backgrounds
    bg='#120c0c',
    bg_elevated='#1a1212',
    bg_soft='#271a1a',
    
    # Warm dragon fire amber/orange accents
    accent='#fb923c',
    accent_soft=hex_to_rgba('#fb923c', 0.18),
    accent_strong='#fdba74',
    
    # Warm parchment-like text
    text_main='#fef3e2',
    text_soft='#d4a574',
    
    # Fire-inspired status colors
    ok='#86efac',
    ok_soft=hex_to_rgba('#86efac', 0.15),
    warn='#fde047',
    warn_soft=hex_to_rgba('#fde047', 0.15),
    danger='#fca5a5',
    danger_soft=hex_to_rgba('#fca5a5', 0.15),
    
    # Bold, dramatic effects
    border_subtle='#3d2a2a',
    shadow_soft='0 12px 40px rgba(251, 146, 60, 0.15)',
    shadow_strong='0 24px 70px rgba(251, 146, 60, 0.25)',
    radius_sm='2px',
    radius_md='4px',
    radius_lg='6px',
    radius_xl='8px',
    
    # Cinzel + EB Garamond - powerful fantasy serif
    font_family='"Cinzel", "EB Garamond", "Palatino Linotype", serif',
    font_mono='"Courier New", "Lucida Console", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=EB+Garamond:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# FROST THEME - Celestial Temple / Divine Realm
# =============================================================================
# Perfect for: Holy/divine themed reports, celestial realms, clerical records
# Font: Cinzel + Lora - sacred, elegant, illuminated manuscript style

{safe_name.upper()}_FROST = ReportTheme(
    id='{safe_name}_frost',
    name='{class_name} Frost',
    
    # Clean celestial light backgrounds
    bg='#f0f9ff',
    bg_elevated='#ffffff',
    bg_soft='#e0f2fe',
    
    # Divine blue accent
    accent='#0284c7',
    accent_soft=hex_to_rgba('#0284c7', 0.12),
    accent_strong='#0ea5e9',
    
    # Dark sacred text
    text_main='#0f172a',
    text_soft='#475569',
    
    # Holy status colors
    ok='#16a34a',
    ok_soft=hex_to_rgba('#16a34a', 0.1),
    warn='#d97706',
    warn_soft=hex_to_rgba('#d97706', 0.1),
    danger='#dc2626',
    danger_soft=hex_to_rgba('#dc2626', 0.1),
    
    # Subtle, refined effects
    border_subtle='#bae6fd',
    shadow_soft='0 4px 20px rgba(14, 165, 233, 0.08)',
    shadow_strong='0 12px 40px rgba(14, 165, 233, 0.15)',
    radius_sm='2px',
    radius_md='4px',
    radius_lg='6px',
    radius_xl='8px',
    
    # Cinzel + Lora - elegant fantasy serif for light theme
    font_family='"Cinzel", "Lora", "Palatino Linotype", serif',
    font_mono='"Courier New", "Lucida Console", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Lora:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.25,
)


# =============================================================================
# DEFAULT THEME ALIAS
# =============================================================================
# Point to dungeon as the default theme for this plugin

{safe_name.upper()}_THEME = {safe_name.upper()}_DUNGEON


# =============================================================================
# THEME NAMES LIST (for GUI discovery)
# =============================================================================
# Single source of truth for available theme names
# GUI imports this to populate theme dropdown

THEME_NAMES = ['dungeon', 'midnight', 'aurora', 'sunset', 'frost']


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Import themes in your executor or templates:
#        from .theme import {safe_name.upper()}_DUNGEON, get_theme_css_variables
#
# 2. Generate CSS variables:
#        theme_css = get_theme_css_variables({safe_name.upper()}_DUNGEON)
#
# 3. Available themes (THEME_NAMES):
#        dungeon   - D&D fantasy + gold (default)
#        midnight  - Deep blue + cyan
#        aurora    - Purple + magenta
#        sunset    - Warm amber + orange
#        frost     - Clean light blue
#
# 4. GUI theme discovery:
#        from .theme import THEME_NAMES
'''
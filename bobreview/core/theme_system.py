"""
Unified Theme System for BobReview.

Provides a single, predictable API for all theme operations:
- Theme resolution (with inheritance)
- CSS generation (unified, modular)
- Template integration (standardized helpers)

This module unifies theme operations across the codebase.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Literal, Union
import warnings
from markupsafe import Markup
from .themes import ReportTheme, resolve_theme, get_theme_by_id, get_theme_css_variables, get_available_themes
from .html_utils import get_shared_css
from .plugin_system import get_extension_point


class ThemeSystem:
    """
    Unified theme system for BobReview.
    
    Provides a single, predictable API for all theme operations.
    Handles theme resolution, CSS generation, and template integration.
    
    Usage:
        system = ThemeSystem.get_instance()
        theme = system.resolve_theme('dark')
        css = system.get_css('dark', mode='embedded')
    """
    
    _instance: Optional['ThemeSystem'] = None
    
    def __init__(self):
        """Initialize the theme system."""
        self._extension_point = None
    
    @classmethod
    def get_instance(cls) -> 'ThemeSystem':
        """Get or create the singleton ThemeSystem instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _get_extension_point(self):
        """Lazy load extension point."""
        if self._extension_point is None:
            self._extension_point = get_extension_point()
        return self._extension_point
    
    def get_theme(self, theme_id: Optional[str] = None) -> Optional[ReportTheme]:
        """
        Get a theme by ID from the registry.
        
        Parameters:
            theme_id: Theme ID (e.g., 'dark', 'light'). If None, returns 'dark' theme.
        
        Returns:
            ReportTheme instance or None if not found
        
        Raises:
            ValueError: If theme_id is invalid (empty string, whitespace, etc.)
        """
        # Validate theme_id
        if theme_id is not None:
            if not isinstance(theme_id, str):
                raise ValueError(f"Theme ID must be a string, got {type(theme_id).__name__}")
            theme_id = theme_id.strip()
            if not theme_id:
                raise ValueError("Theme ID cannot be empty or whitespace")
        
        # If no theme_id provided, return 'dark' theme directly
        if not theme_id:
            return get_theme_by_id('dark')
        
        extension_point = self._get_extension_point()
        
        # Check if this is a built-in theme ID
        built_in_theme_ids = set(get_available_themes())
        is_built_in_id = theme_id in built_in_theme_ids
        
        # Check plugin registry first (allows plugins to override built-in themes)
        plugin_theme = extension_point.get_theme(theme_id)
        
        if plugin_theme and is_built_in_id:
            # Plugin theme is overriding a built-in theme - warn about this
            warnings.warn(
                f"Plugin theme '{theme_id}' is overriding built-in theme '{theme_id}'. "
                f"This may cause unexpected behavior. Consider using a different theme ID.",
                UserWarning,
                stacklevel=2
            )
        
        theme = plugin_theme
        
        if not theme:
            # Try built-in themes
            theme = get_theme_by_id(theme_id)
        
        if not theme:
            # Fallback to dark theme (prefer built-in over plugin)
            built_in_dark = get_theme_by_id('dark')
            plugin_dark = extension_point.get_theme('dark')
            
            if built_in_dark:
                theme = built_in_dark
            elif plugin_dark:
                theme = plugin_dark
            else:
                # No theme found at all - this shouldn't happen, but handle gracefully
                warnings.warn(
                    f"Theme '{theme_id}' not found and fallback 'dark' theme also not available. "
                    f"Returning None.",
                    UserWarning,
                    stacklevel=2
                )
        
        return theme
    
    def resolve_theme(self, theme_id: str) -> Optional[ReportTheme]:
        """
        Resolve a theme with inheritance applied.
        
        If the theme extends another theme, resolves inheritance chain
        and returns a fully resolved theme. This is the recommended way
        to get themes as it handles inheritance automatically.
        
        Parameters:
            theme_id: Theme ID to resolve
        
        Returns:
            Resolved ReportTheme or None if not found
        
        Raises:
            ValueError: If theme_id is invalid or circular inheritance detected
        """
        # Validate theme_id
        if not isinstance(theme_id, str):
            raise ValueError(f"Theme ID must be a string, got {type(theme_id).__name__}")
        theme_id = theme_id.strip()
        if not theme_id:
            raise ValueError("Theme ID cannot be empty or whitespace")
        
        theme = self.get_theme(theme_id)
        if not theme:
            return None
        
        # Resolve inheritance using unified resolver
        extension_point = self._get_extension_point()
        theme_registry = extension_point.themes if hasattr(extension_point, 'themes') else None
        
        try:
            # Use resolve_theme from themes.py which handles multi-level inheritance
            return resolve_theme(theme, theme_registry)
        except ValueError as e:
            # Re-raise ValueError (circular inheritance) with context
            raise ValueError(f"Failed to resolve theme '{theme_id}': {e}") from e
    
    def resolve_from_config(self, theme_config) -> Optional[ReportTheme]:
        """
        Resolve a theme from a ThemeConfig object.
        
        This is a convenience method for integrating with the JSON schema.
        Accepts ThemeConfig, dict with 'preset' key, or string theme ID.
        
        Parameters:
            theme_config: ThemeConfig instance, dict, or string theme ID
        
        Returns:
            Resolved ReportTheme or None if not found
        
        Example:
            # From ReportSystemDefinition
            theme = theme_system.resolve_from_config(system_def.theme)
        """
        if theme_config is None:
            return self.resolve_theme('dark')
        
        # Extract preset from different input types
        if isinstance(theme_config, str):
            preset = theme_config
        elif hasattr(theme_config, 'preset'):
            preset = theme_config.preset
        elif isinstance(theme_config, dict):
            preset = theme_config.get('preset', 'dark')
        else:
            preset = 'dark'
        
        return self.resolve_theme(preset)
    
    def get_css(
        self,
        theme_id: str,
        mode: Literal['embedded', 'linked'] = 'embedded',
        include_base: bool = True
    ) -> Union[Markup, str]:
        """
        Get CSS for a theme in the specified mode.
        
        Parameters:
            theme_id: Theme ID
            mode: 'embedded' for inline CSS, 'linked' for external file reference
            include_base: Whether to include base styles from styles.css
        
        Returns:
            CSS string (for embedded) or file path (for linked)
        
        Raises:
            ValueError: If theme_id is invalid or theme resolution fails
        """
        # Validate theme_id
        if not isinstance(theme_id, str):
            raise ValueError(f"Theme ID must be a string, got {type(theme_id).__name__}")
        theme_id = theme_id.strip()
        if not theme_id:
            raise ValueError("Theme ID cannot be empty or whitespace")
        
        # Validate mode
        if mode not in ('embedded', 'linked'):
            raise ValueError(f"mode must be 'embedded' or 'linked', got '{mode}'")
        
        theme = self.resolve_theme(theme_id)
        if not theme:
            warnings.warn(
                f"Theme '{theme_id}' not found, returning empty CSS.",
                UserWarning,
                stacklevel=2
            )
            return ''
        
        if mode == 'embedded':
            # Generate embedded CSS
            css_parts = []
            
            # Theme variables
            css_parts.append(get_theme_css_variables(theme))
            
            # Base styles (if requested)
            if include_base:
                css_parts.append('\n/* Base styles */\n')
                css_parts.append(get_shared_css())
            
            # Wrap in Markup to prevent Jinja2 autoescape from escaping quotes in CSS
            return Markup('\n'.join(css_parts))
        
        else:  # linked
            # Return path to theme.css (generated by page_renderer)
            return 'static/theme.css'
    
    def get_theme_dict(self, theme_id: str) -> Dict[str, Any]:
        """
        Get theme as dictionary for template context.
        
        Parameters:
            theme_id: Theme ID
        
        Returns:
            Dict with theme values
        """
        from .themes import theme_to_dict
        
        theme = self.resolve_theme(theme_id)
        if not theme:
            return {}
        
        return theme_to_dict(theme)
    
    def generate_theme_css_file(self, theme_id: str, output_path: Path) -> None:
        """
        Generate a theme.css file for linked CSS mode.
        
        Parameters:
            theme_id: Theme ID
            output_path: Path to write theme.css
        """
        theme = self.resolve_theme(theme_id)
        if not theme:
            return
        
        # Generate CSS with theme variables
        css_vars = get_theme_css_variables(theme)
        
        # Add base styles
        base_css = get_shared_css()
        
        full_css = f"""/* Generated theme: {theme.name} */

{css_vars}

/* Base styles */
{base_css}
"""
        
        # Write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_css, encoding='utf-8')


# Convenience functions for easy access
def get_theme_system() -> ThemeSystem:
    """Get the global ThemeSystem instance."""
    return ThemeSystem.get_instance()


def get_resolved_theme(theme_id: str) -> Optional[ReportTheme]:
    """Get a resolved theme (with inheritance applied)."""
    return get_theme_system().resolve_theme(theme_id)


def get_theme_css(theme_id: Optional[str] = None, mode: Literal['embedded', 'linked'] = 'embedded', include_base: bool = True) -> Union[Markup, str]:
    """
    Get CSS for a theme.
    
    Parameters:
        theme_id: Theme ID (e.g., 'dark', 'light'). If None, uses 'dark' as fallback.
        mode: 'embedded' for inline CSS, 'linked' for file path
        include_base: Whether to include base styles from styles.css (default: True)
    
    Returns:
        CSS string (for embedded) or file path (for linked)
    
    Raises:
        ValueError: If theme_id is invalid or theme resolution fails
    """
    if not theme_id:
        # Direct fallback to 'dark' theme (don't try to get "default" theme)
        theme_id = 'dark'
    
    # Validate mode
    if mode not in ('embedded', 'linked'):
        raise ValueError(f"Mode must be 'embedded' or 'linked', got '{mode}'")
    
    return get_theme_system().get_css(theme_id, mode=mode, include_base=include_base)


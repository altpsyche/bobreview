"""
Unit tests for bobreview.core.themes module.

Tests cover:
- ReportTheme dataclass creation and validation
- Built-in theme definitions
- Theme inheritance resolution
- CSS generation
- Theme creation helpers
"""

import pytest
from bobreview.core.themes import (
    ReportTheme,
    DARK_THEME,
    LIGHT_THEME,
    OCEAN_THEME,
    PURPLE_THEME,
    TERMINAL_THEME,
    SUNSET_THEME,
    HIGH_CONTRAST_THEME,
    BUILTIN_THEMES,
    THEMES_BY_ID,
    get_theme_by_id,
    get_available_themes,
    resolve_theme,
    get_theme_css_variables,
    theme_to_dict,
    create_theme,
)


# =============================================================================
# REPORT THEME DATACLASS TESTS
# =============================================================================


class TestReportThemeCreation:
    """Tests for ReportTheme dataclass creation."""

    def test_create_minimal_theme(self):
        """Theme can be created with just id and name."""
        theme = ReportTheme(id='test', name='Test Theme')
        assert theme.id == 'test'
        assert theme.name == 'Test Theme'

    def test_default_values_exist(self):
        """Theme has default values for all required fields."""
        theme = ReportTheme(id='test', name='Test')
        # Verify defaults exist without checking specific values
        assert theme.bg is not None
        assert theme.accent is not None
        assert theme.text_main is not None

    def test_custom_colors_override_defaults(self):
        """Custom color values override defaults."""
        theme = ReportTheme(
            id='custom',
            name='Custom',
            accent='#ff0000',
            bg='#000000',
        )
        assert theme.accent == '#ff0000'
        assert theme.bg == '#000000'

    def test_all_radius_fields_exist(self):
        """Theme has all radius fields."""
        theme = ReportTheme(id='test', name='Test')
        assert hasattr(theme, 'radius_sm')
        assert hasattr(theme, 'radius_md')
        assert hasattr(theme, 'radius_lg')
        assert hasattr(theme, 'radius_xl')
        # Verify they have string values (CSS units)
        assert isinstance(theme.radius_sm, str)
        assert isinstance(theme.radius_xl, str)

    def test_shadow_strong_field_exists(self):
        """Theme has shadow_strong field."""
        theme = ReportTheme(id='test', name='Test')
        assert hasattr(theme, 'shadow_strong')
        assert 'rgba' in theme.shadow_strong


class TestReportThemeValidation:
    """Tests for ReportTheme validation."""

    def test_empty_id_raises_error(self):
        """Empty ID raises ValueError."""
        with pytest.raises(ValueError, match="id.*required"):
            ReportTheme(id='', name='Test')

    def test_whitespace_id_raises_error(self):
        """Whitespace-only ID raises ValueError."""
        with pytest.raises(ValueError, match="id.*required"):
            ReportTheme(id='   ', name='Test')

    def test_empty_name_raises_error(self):
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="name.*required"):
            ReportTheme(id='test', name='')

    def test_invalid_id_characters_raises_error(self):
        """ID with invalid characters raises ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            ReportTheme(id='test@theme!', name='Test')

    def test_valid_id_with_underscores(self):
        """ID with underscores is valid."""
        theme = ReportTheme(id='my_custom_theme', name='Test')
        assert theme.id == 'my_custom_theme'

    def test_valid_id_with_hyphens(self):
        """ID with hyphens is valid."""
        theme = ReportTheme(id='my-custom-theme', name='Test')
        assert theme.id == 'my-custom-theme'

    def test_self_extends_raises_error(self):
        """Theme cannot extend itself."""
        with pytest.raises(ValueError, match="cannot extend itself"):
            ReportTheme(id='test', name='Test', extends='test')


class TestReportThemeOverrides:
    """Tests for ReportTheme override mechanism."""

    def test_overrides_dict_applied(self):
        """Overrides dict values are applied to theme."""
        theme = ReportTheme(
            id='test',
            name='Test',
            overrides={'accent': '#ff0000', 'bg': '#000000'}
        )
        assert theme.accent == '#ff0000'
        assert theme.bg == '#000000'

    def test_invalid_override_key_raises_error(self):
        """Invalid override key raises ValueError."""
        with pytest.raises(ValueError, match="invalid fields"):
            ReportTheme(
                id='test',
                name='Test',
                overrides={'not_a_real_field': 'value'}
            )


# =============================================================================
# BUILT-IN THEMES TESTS
# =============================================================================


class TestBuiltInThemes:
    """Tests for built-in theme definitions."""

    def test_all_builtin_themes_exist(self):
        """All expected built-in themes are defined."""
        expected_ids = ['dark', 'light', 'high_contrast', 'ocean', 'purple', 'terminal', 'sunset']
        for theme_id in expected_ids:
            assert theme_id in THEMES_BY_ID, f"Missing theme: {theme_id}"

    def test_builtin_themes_list_not_empty(self):
        """Built-in themes list is not empty."""
        assert len(BUILTIN_THEMES) > 0

    def test_get_theme_by_id_returns_correct_theme(self):
        """get_theme_by_id returns correct theme."""
        theme = get_theme_by_id('ocean')
        assert theme is not None
        assert theme.id == 'ocean'
        assert theme.accent is not None  # Has accent color

    def test_get_theme_by_id_returns_none_for_unknown(self):
        """get_theme_by_id returns None for unknown ID."""
        theme = get_theme_by_id('nonexistent')
        assert theme is None

    def test_get_available_themes_returns_all_ids(self):
        """get_available_themes returns theme IDs."""
        themes = get_available_themes()
        assert 'dark' in themes
        assert len(themes) > 0  # At least one theme


class TestThemeCharacteristics:
    """Tests for theme characteristics - behavior not specific values."""

    def test_dark_theme_exists_with_id(self):
        """Dark theme exists and has correct id."""
        assert DARK_THEME.id == 'dark'
        assert DARK_THEME.name is not None

    def test_light_theme_exists_with_id(self):
        """Light theme exists and has correct id."""
        assert LIGHT_THEME.id == 'light'
        assert LIGHT_THEME.name is not None

    def test_ocean_theme_uses_inter_font(self):
        """Ocean theme uses Inter font."""
        assert 'Inter' in OCEAN_THEME.font_sans

    def test_terminal_theme_uses_jetbrains_mono(self):
        """Terminal theme uses JetBrains Mono for both fonts."""
        assert 'JetBrains Mono' in TERMINAL_THEME.font_sans
        assert 'JetBrains Mono' in TERMINAL_THEME.font_mono


# =============================================================================
# THEME INHERITANCE TESTS
# =============================================================================


class TestThemeInheritance:
    """Tests for theme inheritance resolution."""

    def test_resolve_theme_without_extends(self):
        """Theme without extends returns unchanged."""
        theme = ReportTheme(id='test', name='Test', accent='#ff0000')
        resolved = resolve_theme(theme)
        assert resolved.accent == '#ff0000'

    def test_resolve_theme_inherits_from_parent(self):
        """Theme with extends inherits parent values."""
        child = ReportTheme(
            id='child',
            name='Child',
            extends='dark',
            overrides={'accent': '#ff0000'}
        )
        resolved = resolve_theme(child)
        
        # Should have child's accent
        assert resolved.accent == '#ff0000'
        # Should inherit dark theme's background
        assert resolved.bg == DARK_THEME.bg

    def test_circular_inheritance_detected(self):
        """Circular inheritance raises ValueError."""
        # Create themes that reference each other
        theme_a = ReportTheme(id='a', name='A', extends='b')
        theme_b = ReportTheme(id='b', name='B', extends='a')
        
        # Mock registry that creates circular reference
        class MockRegistry:
            def get(self, theme_id):
                if theme_id == 'a':
                    return theme_a
                if theme_id == 'b':
                    return theme_b
                return None
        
        with pytest.raises(ValueError, match="[Cc]ircular"):
            resolve_theme(theme_a, MockRegistry())

    def test_missing_parent_returns_theme_with_warning(self):
        """Theme with missing parent returns original with warning."""
        child = ReportTheme(id='child', name='Child', extends='nonexistent')
        
        with pytest.warns(UserWarning, match="parent theme not found"):
            resolved = resolve_theme(child)
        
        assert resolved.id == 'child'


# =============================================================================
# CSS GENERATION TESTS
# =============================================================================


class TestCSSGeneration:
    """Tests for CSS generation functions."""

    def test_get_theme_css_variables_returns_string(self):
        """get_theme_css_variables returns CSS string."""
        theme = ReportTheme(id='test', name='Test')
        css = get_theme_css_variables(theme)
        assert isinstance(css, str)
        assert ':root {' in css

    def test_css_contains_all_background_vars(self):
        """Generated CSS contains all background variables."""
        css = get_theme_css_variables(DARK_THEME)
        assert '--bg:' in css
        assert '--bg-elevated:' in css
        assert '--bg-soft:' in css

    def test_css_contains_all_accent_vars(self):
        """Generated CSS contains all accent variables."""
        css = get_theme_css_variables(DARK_THEME)
        assert '--accent:' in css
        assert '--accent-soft:' in css
        assert '--accent-strong:' in css

    def test_css_contains_all_status_vars(self):
        """Generated CSS contains all status color variables."""
        css = get_theme_css_variables(DARK_THEME)
        assert '--ok:' in css
        assert '--ok-soft:' in css
        assert '--warn:' in css
        assert '--warn-soft:' in css
        assert '--danger:' in css
        assert '--danger-soft:' in css

    def test_css_contains_all_radius_vars(self):
        """Generated CSS contains all radius variables."""
        css = get_theme_css_variables(DARK_THEME)
        assert '--radius-sm:' in css
        assert '--radius-md:' in css
        assert '--radius-lg:' in css
        assert '--radius-xl:' in css

    def test_css_contains_shadow_strong(self):
        """Generated CSS contains shadow-strong variable."""
        css = get_theme_css_variables(DARK_THEME)
        assert '--shadow-strong:' in css

    def test_css_uses_theme_values(self):
        """Generated CSS uses actual theme values."""
        theme = ReportTheme(id='test', name='Test', accent='#deadbeef')
        css = get_theme_css_variables(theme)
        assert '#deadbeef' in css

    def test_none_theme_returns_empty_string(self):
        """None theme returns empty string."""
        css = get_theme_css_variables(None)
        assert css == ''


# =============================================================================
# THEME TO DICT TESTS
# =============================================================================


class TestThemeToDict:
    """Tests for theme_to_dict function."""

    def test_returns_dict(self):
        """theme_to_dict returns dictionary."""
        result = theme_to_dict(DARK_THEME)
        assert isinstance(result, dict)

    def test_contains_id_and_name(self):
        """Result contains id and name."""
        result = theme_to_dict(DARK_THEME)
        assert result['id'] == 'dark'
        assert result['name'] == 'Dark (Default)'

    def test_contains_all_color_fields(self):
        """Result contains all color fields."""
        result = theme_to_dict(DARK_THEME)
        assert 'bg' in result
        assert 'accent' in result
        assert 'text_main' in result
        assert 'ok' in result
        assert 'warn' in result
        assert 'danger' in result

    def test_contains_backward_compat_aliases(self):
        """Result contains backward compatibility aliases."""
        result = theme_to_dict(DARK_THEME)
        assert result['border'] == result['border_subtle']
        assert result['success'] == result['ok']
        assert result['warning'] == result['warn']

    def test_none_theme_returns_empty_dict(self):
        """None theme returns empty dict."""
        result = theme_to_dict(None)
        assert result == {}


# =============================================================================
# THEME CREATION HELPERS TESTS
# =============================================================================


class TestCreateTheme:
    """Tests for create_theme helper - behavior-focused."""

    def test_creates_theme_with_extends(self):
        """create_theme sets extends to specified base."""
        theme = create_theme('custom', 'Custom', base='ocean')
        assert theme.extends == 'ocean'

    def test_defaults_to_dark_base(self):
        """Default base is dark theme."""
        theme = create_theme('custom', 'Custom')
        assert theme.extends == 'dark'

    def test_inherits_base_theme_values(self):
        """Resolved theme inherits values from base theme."""
        base_theme = get_theme_by_id('ocean')
        theme = create_theme('custom', 'Custom', base='ocean')
        resolved = resolve_theme(theme)
        
        # Should inherit base theme's background
        assert resolved.bg == base_theme.bg
        # Should inherit base theme's text colors
        assert resolved.text_main == base_theme.text_main

    def test_explicit_overrides_win(self):
        """Explicit overrides take precedence over base theme."""
        theme = create_theme('custom', 'Custom', base='dark', accent='#ff0000')
        resolved = resolve_theme(theme)
        assert resolved.accent == '#ff0000'

    def test_multiple_overrides_applied(self):
        """Multiple overrides are all applied."""
        theme = create_theme(
            'custom', 'Custom',
            base='dark',
            accent='#ff0000',
            bg='#000000',
            ok='#00ff00'
        )
        resolved = resolve_theme(theme)
        assert resolved.accent == '#ff0000'
        assert resolved.bg == '#000000'
        assert resolved.ok == '#00ff00'

    def test_preserves_id_and_name(self):
        """Resolved theme preserves child's id and name."""
        theme = create_theme('my_theme', 'My Custom Theme', base='ocean')
        resolved = resolve_theme(theme)
        assert resolved.id == 'my_theme'
        assert resolved.name == 'My Custom Theme'


class TestHexToRgba:
    """Tests for hex_to_rgba utility function."""

    def test_converts_hex_to_rgba(self):
        """Converts hex color to rgba format."""
        from bobreview.core.themes import hex_to_rgba
        result = hex_to_rgba('#ff0000', 0.5)
        assert result == 'rgba(255, 0, 0, 0.5)'

    def test_handles_short_hex(self):
        """Handles 3-character hex shorthand."""
        from bobreview.core.themes import hex_to_rgba
        result = hex_to_rgba('#f00', 0.5)
        assert result == 'rgba(255, 0, 0, 0.5)'

    def test_handles_hex_without_hash(self):
        """Works without leading hash."""
        from bobreview.core.themes import hex_to_rgba
        result = hex_to_rgba('00ff00', 0.25)
        assert result == 'rgba(0, 255, 0, 0.25)'

    def test_default_alpha(self):
        """Default alpha is 0.15."""
        from bobreview.core.themes import hex_to_rgba
        result = hex_to_rgba('#0066cc')
        assert '0.15' in result

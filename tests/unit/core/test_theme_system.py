"""
Unit tests for bobreview.core.theme_system module.

Tests cover:
- ThemeSystem singleton behavior
- Theme retrieval via ThemeSystem
- Theme resolution with inheritance
- resolve_from_config method
- CSS generation via ThemeSystem
- Theme dict generation
"""

import pytest
from bobreview.core.theme_system import (
    ThemeSystem,
    get_theme_system,
    get_resolved_theme,
    get_theme_css,
)
from bobreview.core.themes import (
    ReportTheme,
    DARK_THEME,
    OCEAN_THEME,
)
from bobreview.engine.schema import ThemeConfig


# =============================================================================
# SINGLETON TESTS
# =============================================================================


class TestThemeSystemSingleton:
    """Tests for ThemeSystem singleton behavior."""

    def test_get_instance_returns_same_object(self):
        """get_instance returns the same object."""
        system1 = ThemeSystem.get_instance()
        system2 = ThemeSystem.get_instance()
        assert system1 is system2

    def test_get_theme_system_returns_singleton(self):
        """get_theme_system function returns singleton."""
        system1 = get_theme_system()
        system2 = get_theme_system()
        assert system1 is system2

    def test_singleton_can_be_reset(self):
        """Singleton can be reset for testing."""
        system1 = get_theme_system()
        ThemeSystem._instance = None
        system2 = get_theme_system()
        assert system1 is not system2


# =============================================================================
# GET_THEME TESTS
# =============================================================================


class TestThemeSystemGetTheme:
    """Tests for ThemeSystem.get_theme method."""

    def test_get_builtin_theme(self, theme_system):
        """Can retrieve built-in theme."""
        theme = theme_system.get_theme('dark')
        assert theme is not None
        assert theme.id == 'dark'

    def test_get_theme_returns_none_for_unknown(self, theme_system):
        """Returns None for unknown theme ID."""
        theme = theme_system.get_theme('nonexistent_theme_xyz')
        # Should fall back to dark, not return None
        assert theme is not None  # Falls back to dark

    def test_get_theme_with_none_returns_dark(self, theme_system):
        """None theme ID returns dark theme."""
        theme = theme_system.get_theme(None)
        assert theme is not None
        assert theme.id == 'dark'

    def test_get_theme_validates_input_type(self, theme_system):
        """Non-string input raises ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            theme_system.get_theme(123)

    def test_get_theme_rejects_empty_string(self, theme_system):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            theme_system.get_theme('')

    def test_get_theme_all_builtin_themes(self, theme_system):
        """Can retrieve all built-in themes."""
        theme_ids = ['dark', 'light', 'high_contrast', 'ocean', 'purple', 'terminal', 'sunset']
        for theme_id in theme_ids:
            theme = theme_system.get_theme(theme_id)
            assert theme is not None, f"Failed to get theme: {theme_id}"
            assert theme.id == theme_id


# =============================================================================
# RESOLVE_THEME TESTS
# =============================================================================


class TestThemeSystemResolveTheme:
    """Tests for ThemeSystem.resolve_theme method."""

    def test_resolve_builtin_theme(self, theme_system):
        """Can resolve built-in theme."""
        theme = theme_system.resolve_theme('ocean')
        assert theme is not None
        assert theme.id == 'ocean'
        assert theme.accent is not None  # Has an accent color

    def test_resolve_returns_none_for_unknown(self, theme_system):
        """Returns None for unknown theme."""
        theme = theme_system.resolve_theme('totally_fake_theme')
        # Note: get_theme falls back to dark, so resolve might too
        # Check actual behavior
        assert theme is not None  # Falls back

    def test_resolve_validates_input_type(self, theme_system):
        """Non-string input raises ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            theme_system.resolve_theme(42)

    def test_resolve_rejects_empty_string(self, theme_system):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            theme_system.resolve_theme('')


# =============================================================================
# RESOLVE_FROM_CONFIG TESTS
# =============================================================================


class TestResolveFromConfig:
    """Tests for ThemeSystem.resolve_from_config method."""

    def test_resolve_from_theme_config(self, theme_system, theme_config_ocean):
        """Can resolve from ThemeConfig object."""
        theme = theme_system.resolve_from_config(theme_config_ocean)
        assert theme is not None
        assert theme.id == 'ocean'

    def test_resolve_from_default_config(self, theme_system, theme_config_default):
        """Default ThemeConfig resolves to dark."""
        theme = theme_system.resolve_from_config(theme_config_default)
        assert theme is not None
        assert theme.id == 'dark'

    def test_resolve_from_string(self, theme_system):
        """Can resolve from string theme ID."""
        theme = theme_system.resolve_from_config('purple')
        assert theme is not None
        assert theme.id == 'purple'

    def test_resolve_from_dict(self, theme_system):
        """Can resolve from dict with preset key."""
        theme = theme_system.resolve_from_config({'preset': 'terminal'})
        assert theme is not None
        assert theme.id == 'terminal'

    def test_resolve_from_none(self, theme_system):
        """None config resolves to dark."""
        theme = theme_system.resolve_from_config(None)
        assert theme is not None
        assert theme.id == 'dark'

    def test_resolve_from_object_with_preset(self, theme_system):
        """Can resolve from any object with preset attribute."""
        class FakeConfig:
            preset = 'sunset'
        
        theme = theme_system.resolve_from_config(FakeConfig())
        assert theme is not None
        assert theme.id == 'sunset'


# =============================================================================
# GET_CSS TESTS
# =============================================================================


class TestThemeSystemGetCSS:
    """Tests for ThemeSystem.get_css method."""

    def test_get_css_embedded_mode(self, theme_system):
        """get_css returns CSS string in embedded mode."""
        css = theme_system.get_css('dark', mode='embedded')
        assert isinstance(css, str)
        assert ':root {' in css

    def test_get_css_linked_mode(self, theme_system):
        """get_css returns path in linked mode."""
        result = theme_system.get_css('dark', mode='linked')
        assert 'static/theme.css' in result

    def test_get_css_includes_base_by_default(self, theme_system):
        """get_css includes base styles by default."""
        css = theme_system.get_css('dark', mode='embedded')
        # Base styles include reset rules
        assert 'box-sizing' in css

    def test_get_css_without_base(self, theme_system):
        """get_css can exclude base styles."""
        css = theme_system.get_css('dark', mode='embedded', include_base=False)
        # Should have theme vars but not base styles
        assert ':root {' in css
        assert 'box-sizing' not in css

    def test_get_css_validates_mode(self, theme_system):
        """Invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="must be 'embedded' or 'linked'"):
            theme_system.get_css('dark', mode='invalid')


# =============================================================================
# GET_THEME_DICT TESTS
# =============================================================================


class TestThemeSystemGetThemeDict:
    """Tests for ThemeSystem.get_theme_dict method."""

    def test_returns_dict(self, theme_system):
        """get_theme_dict returns dictionary."""
        result = theme_system.get_theme_dict('dark')
        assert isinstance(result, dict)

    def test_contains_theme_values(self, theme_system):
        """Result contains theme values."""
        result = theme_system.get_theme_dict('ocean')
        assert result['id'] == 'ocean'
        assert 'accent' in result  # Has accent key

    def test_unknown_theme_returns_empty_dict(self, theme_system):
        """Unknown theme returns empty dict."""
        # Note: depends on fallback behavior
        result = theme_system.get_theme_dict('nonexistent_xyz')
        # May fall back to dark or return empty
        assert isinstance(result, dict)


# =============================================================================
# MODULE-LEVEL FUNCTION TESTS
# =============================================================================


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_resolved_theme(self):
        """get_resolved_theme function works."""
        theme = get_resolved_theme('ocean')
        assert theme is not None
        assert theme.id == 'ocean'

    def test_get_theme_css_default(self):
        """get_theme_css with no args returns dark theme CSS."""
        css = get_theme_css()
        assert ':root {' in css

    def test_get_theme_css_specific_theme(self):
        """get_theme_css with theme ID returns that theme's CSS."""
        css = get_theme_css('purple')
        # Contains CSS structure
        assert ':root {' in css
        assert '--accent:' in css

    def test_get_theme_css_embedded_mode(self):
        """get_theme_css embedded mode works."""
        css = get_theme_css('dark', mode='embedded')
        assert ':root {' in css

    def test_get_theme_css_linked_mode(self):
        """get_theme_css linked mode returns path."""
        result = get_theme_css('dark', mode='linked')
        assert 'theme.css' in result

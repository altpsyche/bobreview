"""
Shared pytest fixtures and configuration for BobReview tests.
"""

import pytest
from pathlib import Path

from bobreview.core.themes import (
    ReportTheme,
    DARK_THEME,
    LIGHT_THEME,
    OCEAN_THEME,
    PURPLE_THEME,
    create_theme,
)
from bobreview.core.theme_system import ThemeSystem, get_theme_system
from bobreview.engine.schema import ThemeConfig


# =============================================================================
# THEME FIXTURES
# =============================================================================


@pytest.fixture
def dark_theme():
    """Provide the built-in dark theme."""
    return DARK_THEME


@pytest.fixture
def light_theme():
    """Provide the built-in light theme."""
    return LIGHT_THEME


@pytest.fixture
def ocean_theme():
    """Provide the built-in ocean theme."""
    return OCEAN_THEME


@pytest.fixture
def custom_theme():
    """Provide a test custom theme."""
    return ReportTheme(
        id='test_custom',
        name='Test Custom Theme',
        accent='#ff0000',
        bg='#1a1a2e',
    )


@pytest.fixture
def theme_with_inheritance():
    """Provide a theme that extends dark theme."""
    return ReportTheme(
        id='child_theme',
        name='Child Theme',
        extends='dark',
        overrides={'accent': '#00ff00'},
    )


@pytest.fixture
def theme_system():
    """Provide a fresh ThemeSystem instance."""
    # Reset singleton for clean test state
    ThemeSystem._instance = None
    return get_theme_system()


@pytest.fixture
def theme_config_ocean():
    """Provide a ThemeConfig for ocean theme."""
    return ThemeConfig(preset='ocean')


@pytest.fixture
def theme_config_default():
    """Provide a default ThemeConfig."""
    return ThemeConfig()


# =============================================================================
# PATH FIXTURES
# =============================================================================


@pytest.fixture
def project_root():
    """Provide the project root path."""
    return Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir():
    """Provide the test fixtures directory."""
    return Path(__file__).parent / 'fixtures'


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================


@pytest.fixture(autouse=True)
def reset_theme_system():
    """Reset ThemeSystem singleton after each test."""
    yield
    ThemeSystem._instance = None

"""
Shared pytest fixtures and configuration for BobReview tests.

NOTE: Themes are now plugin-owned (v1.0.8 Plugin-First Architecture).
This conftest provides minimal stubs for legacy tests.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass


# =============================================================================
# THEME STUBS (themes are now plugin-owned, not in core)
# =============================================================================

@dataclass
class ReportTheme:
    """Minimal stub for ReportTheme - full implementation is in plugins."""
    id: str
    name: str
    accent: str = '#22d3ee'
    bg: str = '#0a0f1a'
    extends: str = ''
    overrides: dict = None
    
    def __post_init__(self):
        if self.overrides is None:
            self.overrides = {}


# Stub themes for legacy tests
DARK_THEME = ReportTheme(id='dark', name='Dark')
LIGHT_THEME = ReportTheme(id='light', name='Light', bg='#ffffff', accent='#0284c7')
OCEAN_THEME = ReportTheme(id='ocean', name='Ocean', accent='#0ea5e9')
PURPLE_THEME = ReportTheme(id='purple', name='Purple', accent='#a855f7')


def create_theme(**kwargs) -> ReportTheme:
    """Stub for create_theme - returns a ReportTheme with given kwargs."""
    return ReportTheme(**kwargs)


class ThemeSystem:
    """Stub ThemeSystem - themes are now plugin-owned."""
    _instance = None
    
    def get_theme(self, theme_id: str) -> ReportTheme:
        return DARK_THEME


def get_theme_system() -> ThemeSystem:
    """Stub for get_theme_system."""
    if ThemeSystem._instance is None:
        ThemeSystem._instance = ThemeSystem()
    return ThemeSystem._instance


@dataclass 
class ThemeConfig:
    """Stub for ThemeConfig."""
    preset: str = 'dark'


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

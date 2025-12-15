"""
Core utilities package for BobReview.

This package contains foundational modules for configuration,
caching, logging, and statistical analysis.
"""

from .config import Config, load_config
from .cache import LLMCache, get_cache, init_cache
from .utils import (
    log_info, log_success, log_warning, log_error, log_verbose,
    format_number, image_to_base64
)
from .themes import (
    ReportTheme, BUILTIN_THEMES, resolve_theme, get_theme_css_variables,
    ThemeSystem, get_theme_system, get_resolved_theme, get_theme_css
)
from .plugin_utils import safe_plugin_call, call_plugin_lifecycle_hooks
from .api import (
    DataParserInterface,
    LLMGeneratorInterface,
    ChartGeneratorInterface,
    ContextBuilderInterface,
    ComponentInterface,
)
from .html_utils import sanitize_llm_html, get_shared_css, get_trend_icon

__all__ = [
    # Config
    'Config',
    'load_config',
    
    # Cache
    'LLMCache',
    'get_cache',
    'init_cache',
    
    # Logging
    'log_info',
    'log_success',
    'log_warning',
    'log_error',
    'log_verbose',
    
    # Utilities
    'format_number',
    'image_to_base64',
    
    # Analysis - domain-specific functions moved to plugins
    # Use plugin-provided analysis instead
    
    # Themes (use ThemeSystem for new code)
    'ReportTheme',
    'get_theme_css_variables',  # From themes.py
    'BUILTIN_THEMES',
    'resolve_theme',
    # Unified Theme System
    'ThemeSystem',
    'get_theme_system',
    'get_resolved_theme',
    'get_theme_css',
    
    # Plugin utilities
    'safe_plugin_call',
    'call_plugin_lifecycle_hooks',
    
    # Core API Interfaces
    'DataParserInterface',
    'LLMGeneratorInterface',
    'ChartGeneratorInterface',
    'ContextBuilderInterface',
    'ComponentInterface',
    
    # HTML Utilities
    'sanitize_llm_html',
    'get_shared_css',
    'get_trend_icon',
]

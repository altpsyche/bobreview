"""
Core utilities package for BobReview.

This package contains foundational modules for configuration,
caching, logging, and the component system.

Plugin-First Architecture:
- Core provides infrastructure only
- All domain features (charts, LLM, parsing) come from plugins
"""

from .config import Config, load_config
from .cache import LLMCache, get_cache, init_cache
from .utils import (
    log_info, log_success, log_warning, log_error, log_verbose,
    format_number, image_to_base64
)
from .themes import (
    ReportTheme, get_theme_css_variables,
    ThemeSystem, get_theme_system, get_theme_css
)
from .plugin_utils import safe_plugin_call, call_plugin_lifecycle_hooks
from .html_utils import sanitize_llm_html, get_shared_css, get_trend_icon

# Core API interfaces removed - plugins define their own
# See docs/ARCHITECTURE_REFACTOR.md

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
    
    # Themes (infrastructure only - no built-in themes)
    'ReportTheme',
    'get_theme_css_variables',
    'ThemeSystem',
    'get_theme_system',
    'get_theme_css',
    
    # Plugin utilities
    'safe_plugin_call',
    'call_plugin_lifecycle_hooks',
    
    # HTML Utilities
    'sanitize_llm_html',
    'get_shared_css',
    'get_trend_icon',
]

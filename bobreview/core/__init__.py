"""
Core utilities package for BobReview.

This package contains foundational modules for configuration,
caching, logging, and statistical analysis.
"""

from .config import ReportConfig, validate_config
from .cache import LLMCache, get_cache, init_cache
from .utils import (
    log_info, log_success, log_warning, log_error, log_verbose,
    format_number, image_to_base64
)
from .analysis import analyze_data
from .theme_utils import get_theme, get_theme_css_variables
from .themes import ReportTheme, BUILTIN_THEMES
from .config_utils import merge_config, merge_nested_config
from .plugin_utils import safe_plugin_call, call_plugin_lifecycle_hooks

__all__ = [
    # Config
    'ReportConfig',
    'validate_config',
    
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
    
    # Analysis
    'analyze_data',
    
    # Themes
    'get_theme',
    'get_theme_css_variables',
    'ReportTheme',
    'BUILTIN_THEMES',
    
    # Config utilities
    'merge_config',
    'merge_nested_config',
    
    # Plugin utilities
    'safe_plugin_call',
    'call_plugin_lifecycle_hooks',
]

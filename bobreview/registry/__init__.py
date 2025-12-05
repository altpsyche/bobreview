"""
Registry package for BobReview.

Provides unified access to all registries:
- Themes: Visual styling for reports
- Charts: Chart.js configurations
- Pages: Report page definitions
"""

from .themes import (
    ReportTheme,
    register_theme,
    get_theme,
    set_active_theme,
    get_all_themes,
    get_theme_css_variables
)

from .charts import (
    ChartDataset,
    ChartConfig,
    register_dataset,
    register_chart,
    get_dataset,
    get_chart,
    get_chart_defaults_js,
    get_scale_options_js
)

from .pages import (
    PageDefinition,
    register_page,
    get_enabled_pages,
    get_all_pages,
    get_nav_items,
    set_disabled_pages,
    get_disabled_pages
)

__all__ = [
    # Themes
    'ReportTheme',
    'register_theme',
    'get_theme',
    'set_active_theme',
    'get_all_themes',
    'get_theme_css_variables',
    
    # Charts
    'ChartDataset',
    'ChartConfig',
    'register_dataset',
    'register_chart',
    'get_dataset',
    'get_chart',
    'get_chart_defaults_js',
    'get_scale_options_js',
    
    # Pages
    'PageDefinition',
    'register_page',
    'get_enabled_pages',
    'get_all_pages',
    'get_nav_items',
    'set_disabled_pages',
    'get_disabled_pages',
]

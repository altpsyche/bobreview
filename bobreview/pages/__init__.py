"""
Pages package for BobReview HTML report generation.

Note: Page generation is now handled by Jinja2 templates.
See bobreview/templates/ for page templates.
This module now only exports utilities from base.py.
"""

from .base import (
    get_shared_css,
    get_css_source_path,
    copy_css_to_output,
    sanitize_llm_html,
    get_trend_icon,
    get_html_template,
    render_stat_card,
    render_stats_item,
    get_page_header,
)

__all__ = [
    'get_shared_css',
    'get_css_source_path', 
    'copy_css_to_output',
    'sanitize_llm_html',
    'get_trend_icon',
    'get_html_template',
    'render_stat_card',
    'render_stats_item',
    'get_page_header',
]

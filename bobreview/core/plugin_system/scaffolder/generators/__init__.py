"""
Code generators for scaffolder.

This package contains modules for generating:
- Python source files (plugin.py, parsers, etc.)
- Configuration files (manifest.json, report_system.json, report_config.yaml)
"""

from .python_files import (
    generate_plugin_py,
    generate_csv_parser,
    generate_context_builder,
    generate_executor,
    generate_chart_generator,
    generate_analysis_module,
    generate_theme_module,
    generate_widgets_module,
    generate_component_module,
)
from .config_files import (
    generate_manifest,
    generate_report_system,
    generate_user_report_config,
)

__all__ = [
    'generate_plugin_py',
    'generate_csv_parser',
    'generate_context_builder',
    'generate_executor',
    'generate_chart_generator',
    'generate_analysis_module',
    'generate_theme_module',
    'generate_widgets_module',
    'generate_component_module',
    'generate_manifest',
    'generate_report_system',
    'generate_user_report_config',
]

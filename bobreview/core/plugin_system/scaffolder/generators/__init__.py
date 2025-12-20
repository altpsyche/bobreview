"""
Code generators for scaffolder.

This package contains modules for generating:
- Python source files (plugin.py, parsers, executor, charts, themes, etc.)
- Configuration files (manifest.json, report_system.json, report_config.yaml)

Modules are split by responsibility for maintainability:
- generator_plugin.py - plugin.py file
- generator_parser.py - csv_parser.py, context_builder.py
- generator_executor.py - executor.py (~735 lines)
- generator_charts.py - chart_generator.py
- generator_theme.py - theme.py with 4 themes
- generator_components.py - analysis.py, widgets.py, components.py
"""

from .generator_plugin import generate_plugin_py
from .generator_parser import generate_csv_parser, generate_context_builder
from .generator_executor import generate_executor
from .generator_charts import generate_chart_generator
from .generator_theme import generate_theme_module
from .generator_components import (
    generate_analysis_module,
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


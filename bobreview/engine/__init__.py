"""
Report systems framework for BobReview.

This module provides a JSON-based configuration system for defining custom
report generation pipelines. Each report system JSON defines:
- Data source parsing
- Metrics and analysis
- LLM generators
- Report pages
- Thresholds and configuration

Usage:
    from bobreview.engine import load_report_system, list_available_systems, ReportSystemExecutor
    
    # List available systems
    systems = list_available_systems()
    
    # Load and execute a system
    system_def = load_report_system('png_data_points')
    executor = ReportSystemExecutor(system_def, config)
    executor.execute(input_dir, output_path)
"""

from .schema import (
    ReportSystemDefinition,
    DataSourceConfig,
    LLMConfig,
    LLMGeneratorConfig,
    PageConfig,
    ThemeConfig,
    OutputConfig,
    validate_report_system,
    parse_report_system_definition
)

from .loader import (
    load_report_system,
    list_available_systems,
    discover_report_systems,
    find_report_system_path,
    clear_cache,
    ensure_user_directory,
    get_builtin_report_systems_dir,
    get_user_report_systems_dir
)

from .data_parser_base import (
    DataParser,
    FilenamePatternParser
)

from .parser_factory import ParserFactory

from .llm_generator_base import (
    LLMGeneratorTemplate,
    LLMGeneratorAdapter
)

from .page_generator_base import (
    PageGeneratorTemplate
)

from .executor import (
    ReportSystemExecutor
)

from .config_merger import ConfigMerger
from .service_validator import ServiceValidator
from .plugin_lifecycle import PluginLifecycleManager

__all__ = [
    # Schema classes
    'ReportSystemDefinition',
    'DataSourceConfig',
    'LLMConfig',
    'LLMGeneratorConfig',
    'PageConfig',
    'ThemeConfig',
    'OutputConfig',
    'validate_report_system',
    'parse_report_system_definition',
    
    # Loader functions
    'load_report_system',
    'list_available_systems',
    'discover_report_systems',
    'find_report_system_path',
    'clear_cache',
    'ensure_user_directory',
    'get_builtin_report_systems_dir',
    'get_user_report_systems_dir',
    
    # Base classes
    'DataParser',
    'FilenamePatternParser',
    'ParserFactory',
    'LLMGeneratorTemplate',
    'LLMGeneratorAdapter',
    'PageGeneratorTemplate',
    
    # Executor
    'ReportSystemExecutor',
    
    # Responsibility classes
    'ConfigMerger',
    'ServiceValidator',
    'PluginLifecycleManager',
]


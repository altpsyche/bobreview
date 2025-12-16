"""
Report systems framework for BobReview.

Plugin-First Architecture:
- Core provides minimal schema and loader
- Plugins provide all execution logic via ComponentRenderer
"""

from .schema import (
    ReportSystemDefinition,
    DataSourceConfig,
    LLMGeneratorConfig,
    PageConfig,
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

# Removed: executor, page_renderer, service_validator, plugin_lifecycle,
#          data_parser_base, parser_factory, llm_generator_base
# Plugins provide execution logic via ComponentRenderer

__all__ = [
    # Schema classes
    'ReportSystemDefinition',
    'DataSourceConfig',
    'LLMGeneratorConfig',
    'PageConfig',
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
]

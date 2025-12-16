"""
Report systems framework for BobReview.

Plugin-First Architecture:
- Core provides minimal schema and loader
- Plugins provide all execution logic via ComponentRenderer
- Domain structures (pages, charts, llm_generators) are generic dicts
"""

from .schema import (
    ReportSystemDefinition,
    DataSourceConfig,
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

# Removed typed dataclasses: LLMGeneratorConfig, PageConfig, ChartConfig, etc.
# These are now Dict[str, Any] - plugins handle their own structure

__all__ = [
    # Schema classes
    'ReportSystemDefinition',
    'DataSourceConfig',
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

"""
Focused registries for plugin components.

Plugin-First Architecture:
- Most registries removed (plugins handle their own features)
- Only infrastructure registries remain
- Themes now owned entirely by plugins
"""

from .base_registry import RegistryCollisionError
from .service_registry import ServiceRegistry
from .report_system_registry import ReportSystemRegistry
from .template_path_registry import TemplatePathRegistry
from .data_parser_registry import DataParserRegistry

# Removed registries (plugin features):
# - ThemeRegistry -> Plugins own theming entirely
# - WidgetRegistry -> Use ComponentRegistry from core.components
# - LLMGeneratorRegistry -> Plugin handles
# - ChartTypeRegistry -> Plugin handles
# - ChartGeneratorRegistry -> Plugin handles
# - ContextBuilderRegistry -> Plugin handles
# - AnalyzerRegistry -> Plugin handles
# - PageRegistry -> Plugin handles

__all__ = [
    'RegistryCollisionError',
    'ServiceRegistry',
    'ReportSystemRegistry',
    'TemplatePathRegistry',
    'DataParserRegistry',
]

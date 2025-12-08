"""
Focused registries for plugin components.

Each registry handles a single type of component, following the
Interface Segregation Principle.
"""

from .theme_registry import ThemeRegistry
from .widget_registry import WidgetRegistry
from .data_parser_registry import DataParserRegistry
from .llm_generator_registry import LLMGeneratorRegistry
from .chart_type_registry import ChartTypeRegistry
from .page_registry import PageRegistry
from .service_registry import ServiceRegistry
from .report_system_registry import ReportSystemRegistry
from .chart_generator_registry import ChartGeneratorRegistry
from .context_builder_registry import ContextBuilderRegistry
from .template_path_registry import TemplatePathRegistry

__all__ = [
    'ThemeRegistry',
    'WidgetRegistry',
    'DataParserRegistry',
    'LLMGeneratorRegistry',
    'ChartTypeRegistry',
    'PageRegistry',
    'ServiceRegistry',
    'ReportSystemRegistry',
    'ChartGeneratorRegistry',
    'ContextBuilderRegistry',
    'TemplatePathRegistry',
]


"""
BobReview Services Package.

This package provides modular services for the report generation pipeline.
Services can be independently tested, replaced by plugins, and reused.

Services:
    - DataService: Parse and validate input data
    - AnalyticsService: Calculate statistics
    - ChartService: Generate Chart.js configurations
    - LLMService: Generate AI content
    - ReportPipeline: Orchestrate all services

Quick Start:
    from bobreview.services import get_container, DataService, AnalyticsService

    # Register services
    container = get_container()
    container.register('data', DataService())
    container.register('analytics', AnalyticsService())

    # Use services
    data = container.get('data').parse(input_dir, data_source_config)
    stats = container.get('analytics').analyze(data, metrics, metrics_config)

Plugin Replacement:
    # Plugins can replace core services
    container.replace('analytics', MyCustomAnalyticsService())
"""

from .container import (
    ServiceContainer,
    get_container,
    reset_container,
)

from .base import (
    BaseService,
    ServiceError,
    DataServiceError,
    AnalyticsServiceError,
    ChartServiceError,
    LLMServiceError,
    RenderServiceError,
)

from .data_service import DataService
from .analytics_service import AnalyticsService
from .chart_service import ChartService
from .llm_service import LLMService
from .pipeline import ReportPipeline, create_default_pipeline

__all__ = [
    # Container
    'ServiceContainer',
    'get_container',
    'reset_container',
    
    # Base
    'BaseService',
    'ServiceError',
    'DataServiceError',
    'AnalyticsServiceError',
    'ChartServiceError',
    'LLMServiceError',
    'RenderServiceError',
    
    # Services
    'DataService',
    'AnalyticsService',
    'ChartService',
    'LLMService',
    
    # Pipeline
    'ReportPipeline',
    'create_default_pipeline',
]

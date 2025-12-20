"""
BobReview Services Package.

Plugin-First Architecture:
- Services are minimal infrastructure only
- Domain-specific services moved to plugins
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

# Removed: AnalyticsService, ChartService, LLMService, ReportPipeline
# Plugins provide domain-specific services

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
    
    # Services (minimal)
    'DataService',
]

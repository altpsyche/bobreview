"""
Base service class and common interfaces.

All BobReview services should extend BaseService for consistent
lifecycle management and configuration handling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseService(ABC):
    """
    Abstract base class for all BobReview services.
    
    Services are stateless processors that perform specific tasks
    in the report generation pipeline.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize service with optional configuration.
        
        Parameters:
            config: Service-specific configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Update service configuration.
        
        Parameters:
            config: New configuration values (merged with existing)
        """
        self.config.update(config)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)


class ServiceError(Exception):
    """Base exception for service errors."""
    pass


class DataServiceError(ServiceError):
    """Error during data parsing/validation."""
    pass


class AnalyticsServiceError(ServiceError):
    """Error during statistical analysis."""
    pass


class ChartServiceError(ServiceError):
    """Error during chart generation."""
    pass


class LLMServiceError(ServiceError):
    """Error during LLM content generation."""
    pass


class RenderServiceError(ServiceError):
    """Error during page rendering."""
    pass

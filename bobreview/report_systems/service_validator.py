"""
Service validator for report systems.

Responsible for validating that required services are available.
"""

from typing import Dict, Any, Optional
from ..services import ServiceContainer
from ..core import ReportConfig, log_warning, log_verbose
from ..services import LLMService


class ServiceValidator:
    """
    Validates that required services are available.
    
    Single Responsibility: Service validation only.
    """
    
    def __init__(self, container: ServiceContainer):
        """
        Initialize service validator.
        
        Parameters:
            container: ServiceContainer to validate
        """
        self.container = container
    
    def validate_required(
        self,
        required_services: Dict[str, str],
        config: ReportConfig
    ) -> bool:
        """
        Validate that all required services are available.
        
        Parameters:
            required_services: Dict mapping service name to description
            config: ReportConfig for logging
        
        Returns:
            True if all services are available, False otherwise
        
        Raises:
            RuntimeError: If plugins are loaded but services are missing
        """
        missing_services = []
        for service_name, description in required_services.items():
            if not self.container.has(service_name):
                missing_services.append(f"  - {service_name}: {description}")
        
        if missing_services:
            from ..plugins import get_loader
            loader = get_loader()
            loaded_plugins = [p.name for p in loader.get_loaded_plugins() if p.loaded]
            
            # If no plugins are loaded, this is expected
            if not loaded_plugins:
                log_warning(
                    "No plugins loaded. BobReview can run without plugins, but cannot generate reports "
                    "without the required services. Load a plugin (like MayhemAutomation or game-review) "
                    "to enable report generation.",
                    config
                )
                return False
            
            # If plugins are loaded but services are missing, that's an error
            error_msg = (
                f"Required services not found. Missing:\n" + "\n".join(missing_services) +
                f"\n\nLoaded plugins: {', '.join(loaded_plugins)}" +
                f"\n\nThe loaded plugins may not be providing the required services."
            )
            raise RuntimeError(error_msg)
        
        return True
    
    def ensure_llm_service(self, config: ReportConfig) -> None:
        """
        Ensure LLM service is registered, creating it if needed.
        
        LLM service needs runtime config, so we register it here if not already registered.
        
        Parameters:
            config: ReportConfig with LLM settings
        """
        if not self.container.has('llm'):
            llm_config = {
                'provider': config.llm.provider,
                'api_key': config.llm.api_key,
                'model': config.llm.model,
                'temperature': config.llm.temperature,
                'max_tokens': config.llm.max_tokens,
                'use_cache': config.llm.use_cache,
            }
            self.container.register('llm', LLMService(llm_config))
            log_verbose("Registered LLMService with runtime config", config)


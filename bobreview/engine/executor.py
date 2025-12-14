"""
Report system executor that orchestrates the entire report generation pipeline.

The executor takes a ReportSystemDefinition and executes it:
1. Parse data using configured data source
2. Calculate statistics based on metrics config  
3. Generate LLM content for configured generators
4. Generate HTML pages from Jinja2 templates (CMS-style)

NOTE: This executor now uses the services package for modular, pluggable processing.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from dataclasses import asdict
from datetime import datetime
import os
import jinja2

from .schema import ReportSystemDefinition, Labels

# Import from new package structure
from ..core import ReportConfig, log_info, log_verbose, log_warning, log_error, image_to_base64

# Import services and plugin system
from ..services import ServiceContainer, DataService, AnalyticsService, ChartService, LLMService, get_container
from ..core.plugin_system import PluginRegistry, PluginLoader, get_extension_point, get_plugin_manager
from ..core.template_engine import get_template_engine

# Import new responsibility classes
from .config_merger import ConfigMerger
from .service_validator import ServiceValidator
from .plugin_lifecycle import PluginLifecycleManager

if TYPE_CHECKING:
    from ..core.template_engine import TemplateEngine
    from ..core.dataframe import DataFrame


class ReportSystemExecutor:
    """
    Executes a report system from JSON definition.
    
    Uses the services package for modular processing:
    - DataService for parsing
    - AnalyticsService for statistics
    - ChartService for chart generation
    
    Plugins can replace services via the ServiceContainer.
    
    Single Responsibility: Orchestrates the report generation pipeline.
    """
    
    def __init__(
        self,
        system_def: ReportSystemDefinition,
        config: ReportConfig,
        container: Optional[ServiceContainer] = None,
        registry: Optional[PluginRegistry] = None,
        template_engine: Optional['TemplateEngine'] = None,
        plugin_loader: Optional[PluginLoader] = None
    ):
        """
        Initialize the executor with a report system definition.
        
        Parameters:
            system_def: Report system definition from JSON
            config: Report configuration (merged with JSON settings)
            container: ServiceContainer (injected dependency, uses global if None)
            registry: PluginRegistry (injected dependency, uses global if None)
            template_engine: TemplateEngine (injected dependency, uses global if None)
            plugin_loader: PluginLoader (injected dependency, uses global if None)
        """
        self.system_def = system_def
        self.config = config
        
        # Use dependency injection with fallback to globals for backward compatibility
        if container is None:
            container = get_container()
        if registry is None:
            extension_point = get_extension_point()
        else:
            extension_point = None  # Will be set from registry if provided
        if template_engine is None:
            template_engine = get_template_engine()
        if plugin_loader is None:
            plugin_manager = get_plugin_manager()
        else:
            plugin_manager = None  # Will use provided plugin_loader
        
        self.container = container
        self.registry = registry
        self._extension_point = extension_point
        self.template_engine = template_engine
        self.plugin_loader = plugin_loader
        self._plugin_manager = plugin_manager
        
        # Initialize responsibility classes
        self.config_merger = ConfigMerger()
        self.service_validator = ServiceValidator(container)
        # Use plugin_manager for lifecycle manager (fallback to plugin_loader if provided)
        if plugin_loader is not None:
            self.lifecycle_manager = PluginLifecycleManager(plugin_loader)
        else:
            # PluginLifecycleManager needs a PluginLoader, so get it from plugin_manager's internal loader
            from .plugin_lifecycle import PluginLifecycleManager
            self.lifecycle_manager = PluginLifecycleManager(self._plugin_manager.loader if hasattr(self._plugin_manager, 'loader') else None)
        
        # Merge configuration and validate services
        self.config_merger.merge(self.config, self.system_def)
        self.services_available = self._ensure_services()
    
    def _ensure_services(self) -> bool:
        """
        Ensure required services are available.
        
        Auto-registers default services if plugins are loaded but services aren't registered.
        Delegates to ServiceValidator for validation.
        
        Returns:
            bool: True if all services are available, False otherwise
        """
        required_services = {
            'data': 'DataService (required for data parsing)',
            'analytics': 'AnalyticsService (required for statistical analysis)',
            'charts': 'ChartService (required for chart generation)',
        }
        
        # Check if plugins are loaded
        if self._plugin_manager:
            loaded_plugins = [p.name for p in self._plugin_manager.get_loaded_plugins() if p.loaded]
        elif self.plugin_loader:
            loaded_plugins = [p.name for p in self.plugin_loader.get_loaded_plugins() if p.loaded]
        else:
            loaded_plugins = []
        
        # If plugins are loaded but services aren't registered, auto-register default services
        if loaded_plugins and not all(self.container.has(name) for name in required_services.keys()):
            log_verbose(f"Auto-registering default services for loaded plugins: {', '.join(loaded_plugins)}", self.config)
            from ..services import DataService, AnalyticsService, ChartService
            
            if not self.container.has('data'):
                self.container.register('data', DataService())
            if not self.container.has('analytics'):
                self.container.register('analytics', AnalyticsService())
            if not self.container.has('charts'):
                self.container.register('charts', ChartService())
        
        # Validate required services
        if not self.service_validator.validate_required(required_services, self.config):
            return False
        
        # Ensure LLM service is registered
        self.service_validator.ensure_llm_service(self.config)
        
        return True
    
    def execute(self, input_dir: Path, output_path: Path) -> bool:
        """
        Execute complete report generation pipeline.
        
        Parameters:
            input_dir: Directory containing input files
            output_path: Path for output HTML file
        
        Returns:
            True if report was generated successfully, False otherwise
        """
        # Check if services are available (plugins loaded)
        if not self.services_available:
            log_warning(
                "Cannot generate report: required services are not available. "
                "BobReview works without plugins, but cannot generate reports without them. "
                "Load a plugin to enable report generation.",
                self.config
            )
            return False
        
        log_info(f"Executing report system: {self.system_def.name}", self.config)
        log_verbose(f"System ID: {self.system_def.id} v{self.system_def.version}", self.config)
        
        # Build report context for lifecycle hooks
        report_context = {
            'system_id': self.system_def.id,
            'system_name': self.system_def.name,
            'input_dir': str(input_dir),
            'output_path': str(output_path),
            'config': self.config,
        }
        
        # Call plugin lifecycle hooks: on_report_start
        self.lifecycle_manager.call_report_start(report_context, self.config)
        
        try:
            # 1. Parse data (using DataService)
            data_points = self.parse_data(input_dir)
            if not data_points:
                log_warning("No data points found", self.config)
                report_result = {
                    'success': False,
                    'error': 'No data points found',
                    'output_path': str(output_path),
                    'data_points_count': 0,
                    'stats': {},
                }
                self.lifecycle_manager.call_report_complete(report_result, self.config)
                return False
            
            log_info(f"Parsed {len(data_points)} data points", self.config)
            
            # 2. Calculate statistics (using AnalyticsService)
            stats = self.analyze_data(data_points)
            log_info("Statistical analysis complete", self.config)
            
            # Set report title
            # Priority: 1) CLI (config.title), 2) JSON (system_def.title), 3) default "Report"
            if self.config.title is None:
                if hasattr(self.system_def, 'title') and self.system_def.title:
                    self.config.title = self.system_def.title
                    log_verbose(f"Using title from JSON config: {self.config.title}", self.config)
                else:
                    self.config.title = "Report"
                    log_verbose("Using default title: Report", self.config)
            
            # 3. Generate LLM content
            llm_results = self.generate_llm_content(data_points, stats)
            log_info("LLM content generation complete", self.config)
            
            # 4. Generate pages
            self.generate_pages(data_points, stats, llm_results, input_dir, output_path)
            log_info(f"Report generated: {output_path}", self.config)
            
            # Build report result for lifecycle hooks
            report_result = {
                'success': True,
                'output_path': str(output_path),
                'data_points_count': len(data_points),
                'stats': stats,
            }
            
            # Call plugin lifecycle hooks: on_report_complete
            self.lifecycle_manager.call_report_complete(report_result, self.config)
            
            return True
            
        except Exception as e:
            # Report failure to plugins
            report_result = {
                'success': False,
                'error': str(e),
            }
            self.lifecycle_manager.call_report_complete(report_result, self.config)
            raise
    
    def parse_data(self, input_dir: Path) -> List[Dict[str, Any]]:
        """
        Parse data using DataService from the container.
        
        Parameters:
            input_dir: Directory containing input files
        
        Returns:
            List of parsed data points
        """
        # Use DataService from container (allows plugin override)
        data_service: DataService = self.container.get('data')
        
        # Get timestamp field for sorting from extensions (plugin-provided metrics)
        sort_by = None
        metrics_ext = self.system_def.extensions.get('metrics')
        if metrics_ext:
            sort_by = metrics_ext.get('timestamp_field')
        
        return data_service.parse(
            input_dir=input_dir,
            data_source_config=self.system_def.data_source,
            sample_size=self.config.execution.sample_size,
            sort_by=sort_by
        )
    
    def _build_meta_text(self, stats: Dict[str, Any], data: Union[List[Dict[str, Any]], 'DataFrame']) -> str:
        """
        Build meta text for report header.
        """
        data_points = list(data) if hasattr(data, '__iter__') else data
        count = stats.get('count', len(data_points))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        return f"{count} items · Generated {timestamp}"
    
    def analyze_data(self, data: Union[List[Dict[str, Any]], 'DataFrame']) -> Dict[str, Any]:
        """
        Calculate statistics using AnalyticsService from the container.
        
        Uses the metrics configuration from JSON to dynamically analyze
        whatever fields are specified, not hardcoded draws/tris.
        
        Parameters:
            data_points: List of parsed data points
        
        Returns:
            Statistical analysis results
        """
        # Use AnalyticsService from container (allows plugin override)
        analytics_service: AnalyticsService = self.container.get('analytics')
        
        try:
            # Convert DataFrame to list for analysis
            data_points = list(data) if hasattr(data, '__iter__') else data
            
            # Get metrics config from extensions (plugin-provided)
            metrics_ext = self.system_def.extensions.get('metrics')
            metrics = None
            metrics_config = None
            
            if metrics_ext:
                metrics = metrics_ext.get('primary')
                metrics_config = metrics_ext
            
            # If no metrics config, return data as-is (for non-analytical report systems)
            if not metrics_config:
                # For report systems without metrics, return the data as stats
                if data_points:
                    return data_points[0] if len(data_points) == 1 else {'data': data_points}
                return {}
            
            # Pass the full report_config - service uses it directly
            return analytics_service.analyze(
                data=data_points,  # Service uses 'data' param
                metrics=metrics,
                metrics_config=metrics_config,
                report_config=self.config  # Pass config directly
            )
        except Exception as e:
            raise ValueError(
                f"Analysis failed: {e}. "
                f"Check that your data source configuration produces the required fields."
            ) from e
    
    def generate_llm_content(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        stats: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate content for all LLM generators using LLMService.
        
        Parameters:
            data: DataFrame or List[Dict] with data points
            stats: Statistical analysis results
        
        Returns:
            Dictionary mapping generator ID to generated content
        """
        # Use LLMService from container (allows plugin override)
        llm_service: LLMService = self.container.get('llm')
        
        # Build context for generators
        context = {
            'title': self.config.title
        }
        if getattr(self.system_def, "thresholds", None):
            context.update(self.system_def.thresholds)
        
        # Pass extensions to context so plugins can read plugin-specific values
        if hasattr(self.system_def, 'extensions') and self.system_def.extensions:
            context['extensions'] = self.system_def.extensions
        
        log_info(f"Generating LLM content for {len([g for g in self.system_def.llm_generators if g.enabled])} sections...", self.config)
        
        return llm_service.generate_all(
            generators=self.system_def.llm_generators,
            data=data,  # LLMService uses 'data' param, not 'data_points'
            stats=stats,
            context=context,
            dry_run=self.config.execution.dry_run,
            report_config=self.config
        )
    
    def generate_pages(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        stats: Dict[str, Any],
        llm_results: Dict[str, str],
        input_dir: Path,
        output_path: Path
    ):
        """
        Generate all configured pages using Jinja2 templates.
        
        Delegates to PageRenderer for the actual rendering logic.
        
        Parameters:
            data: DataFrame or List[Dict] with data points
            stats: Statistical analysis results
            llm_results: Generated LLM content
            input_dir: Input directory (for images)
            output_path: Output file path
        """
        from .page_renderer import PageRenderer
        
        renderer = PageRenderer(
            template_engine=self.template_engine,
            extension_point=self._extension_point,
            config=self.config,
            system_def=self.system_def
        )
        
        renderer.render_all_pages(
            data=data,  # PageRenderer uses 'data' param
            stats=stats,
            llm_results=llm_results,
            input_dir=input_dir,
            output_path=output_path
        )


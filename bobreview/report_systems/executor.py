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
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import asdict
from datetime import datetime
import os
import jinja2

from .schema import ReportSystemDefinition, LabelConfig

# Import from new package structure
from ..core import ReportConfig, log_info, log_verbose, log_warning, log_error, image_to_base64

# Import services and plugin system
from ..services import ServiceContainer, DataService, AnalyticsService, ChartService, LLMService
from ..plugins import PluginRegistry, PluginLoader

# Import new responsibility classes
from .config_merger import ConfigMerger
from .service_validator import ServiceValidator
from .plugin_lifecycle import PluginLifecycleManager

if TYPE_CHECKING:
    from ..core.template_engine import TemplateEngine


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
            from ..services import get_container
            container = get_container()
        if registry is None:
            from ..plugins import get_registry
            registry = get_registry()
        if template_engine is None:
            from ..core.template_engine import get_template_engine
            template_engine = get_template_engine()
        if plugin_loader is None:
            from ..plugins import get_loader
            plugin_loader = get_loader()
        
        self.container = container
        self.registry = registry
        self.template_engine = template_engine
        self.plugin_loader = plugin_loader
        
        # Initialize responsibility classes
        self.config_merger = ConfigMerger()
        self.service_validator = ServiceValidator(container)
        self.lifecycle_manager = PluginLifecycleManager(plugin_loader)
        
        # Merge configuration and validate services
        self.config_merger.merge(self.config, self.system_def)
        self.services_available = self._ensure_services()
    
    def _ensure_services(self) -> bool:
        """
        Ensure required services are available.
        
        Delegates to ServiceValidator for validation.
        
        Returns:
            bool: True if all services are available, False otherwise
        """
        required_services = {
            'data': 'DataService (required by a plugin like MayhemAutomation or game-review)',
            'analytics': 'AnalyticsService (required by a plugin like MayhemAutomation or game-review)',
            'charts': 'ChartService (required by a plugin like MayhemAutomation or game-review)',
        }
        
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
                "Load a plugin (like MayhemAutomation or game-review) to enable report generation.",
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
                return False
            
            log_info(f"Parsed {len(data_points)} data points", self.config)
            
            # 2. Calculate statistics (using AnalyticsService)
            stats = self.analyze_data(data_points)
            log_info("Statistical analysis complete", self.config)
            
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
        
        return data_service.parse(
            input_dir=input_dir,
            data_source_config=self.system_def.data_source,
            sample_size=self.config.execution.sample_size,
            sort_by=self.system_def.metrics.timestamp_field
        )
    
    def analyze_data(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            # Pass the full report_config - service uses it directly
            return analytics_service.analyze(
                data_points=data_points,
                metrics=self.system_def.metrics.primary,
                metrics_config=self.system_def.metrics,
                report_config=self.config  # Pass config directly, no dict building
            )
        except Exception as e:
            raise ValueError(
                f"Analysis failed: {e}. "
                f"Check that your data source configuration produces the required fields."
            ) from e
    
    def generate_llm_content(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate content for all LLM generators using LLMService.
        
        Parameters:
            data_points: List of data points
            stats: Statistical analysis results
        
        Returns:
            Dictionary mapping generator ID to generated content
        """
        # Use LLMService from container (allows plugin override)
        llm_service: LLMService = self.container.get('llm')
        
        # Build context for generators
        context = {
            'location': self.config.location,
            'title': self.config.title
        }
        context.update(self.system_def.thresholds)
        
        log_info(f"Generating LLM content for {len([g for g in self.system_def.llm_generators if g.enabled])} sections...", self.config)
        
        return llm_service.generate_all(
            generators=self.system_def.llm_generators,
            data_points=data_points,
            stats=stats,
            context=context,
            dry_run=self.config.execution.dry_run,
            report_config=self.config
        )
    
    def generate_pages(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        llm_results: Dict[str, str],
        input_dir: Path,
        output_path: Path
    ):
        """
        Generate all configured pages using Jinja2 templates.
        
        Uses CMS-style labels from JSON configuration - no hardcoded strings.
        
        Parameters:
            data_points: List of data points
            stats: Statistical analysis results
            llm_results: Generated LLM content
            input_dir: Input directory (for images)
            output_path: Output file path
        """
        # Pre-encode images if needed
        image_data_uris = {}
        if self.config.output.embed_images:
            log_info("Embedding images as base64...", self.config)
            unique_images = set(point.get('img', '') for point in data_points if 'img' in point)
            for img_name in unique_images:
                if img_name:
                    img_path = input_dir / img_name
                    data_uri = image_to_base64(img_path)
                    if data_uri:
                        image_data_uris[img_name] = data_uri
        
        # Determine output directory
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate relative images directory
        images_dir_rel = os.path.relpath(input_dir, output_dir)
        
        # Use injected template engine
        engine = self.template_engine
        
        # Get labels from system definition
        labels = self.system_def.labels
        
        # Get enabled pages
        enabled_pages = [p for p in self.system_def.pages if p.enabled]
        
        # Build navigation items
        nav_items = []
        for page in enabled_pages:
            nav_items.append({
                'label': page.nav_label,
                'url': page.filename,
                'active': False
            })
        
        # Generate each page
        log_info(f"Generating {len(enabled_pages)} HTML pages using Jinja2 templates...", self.config)
        
        for i, page_config in enumerate(enabled_pages, 1):
            page_path = output_dir / page_config.filename
            log_info(f"[{i}/{len(enabled_pages)}] Rendering {page_config.filename}...", self.config)
            
            # Update nav to mark current page as active
            page_nav = []
            for nav in nav_items:
                page_nav.append({
                    **nav,
                    'active': nav['url'] == page_config.filename
                })
            
            # Build LLM content dict for this page using llm_mappings from config
            llm_content = {}
            # Use llm_mappings if available, otherwise fall back to llm_content list
            if page_config.llm_mappings:
                for template_key, generator_id in page_config.llm_mappings.items():
                    llm_content[template_key] = llm_results.get(generator_id, '')
            elif page_config.llm_content:
                # Backward compat: use llm_content list as both key and generator ID
                for generator_id in page_config.llm_content:
                    llm_content[generator_id] = llm_results.get(generator_id, '')
            
            # Build base context for all templates (minimal universal context)
            context = {
                # Core data - available to all templates
                'config': self.config,
                'stats': stats,
                'data': stats,   # Universal alias - all templates can use data.*
                'data_points': data_points,
                'system_def': self.system_def,  # Add system_def for threshold lookups
                
                # LLM generated content
                'llm': llm_content,
                'llm_content': llm_content,  # Alias for consistency
                
                # Navigation
                'nav_items': page_nav,
                'pages': [asdict(p) for p in enabled_pages],
                
                # Report system content blocks
                'content': self.system_def.content_blocks,
                
                # Images
                'image_data_uris': image_data_uris,  # Base64 encoded images if embedding
                'images_dir_rel': images_dir_rel,  # Relative path to images if not embedding
                
                # Meta
                'meta_text': f"{stats.get('count', len(data_points))} items · {self.config.location} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            }
            
            # Add plugin-provided context (images, critical points, game aliases, etc.)
            context_builder_cls = self.registry.context_builders.get(self.system_def.id)
            if context_builder_cls:
                builder = context_builder_cls()
                plugin_context = builder.build(
                    data_points=data_points,
                    stats=stats,
                    config=self.config,
                    system_def=self.system_def,
                    input_dir=input_dir,
                    image_data_uris=image_data_uris
                )
                context.update(plugin_context)
            
            # Add charts if page has chart configurations - use plugin-provided generator
            if page_config.charts:
                chart_generator_cls = self.registry.chart_generators.get(self.system_def.id)
                if chart_generator_cls:
                    # Instantiate with config and thresholds
                    chart_generator = chart_generator_cls(self.config, self.system_def.thresholds)
                    labels_dict = labels.data if hasattr(labels, 'data') else {}
                    context['charts'] = chart_generator.generate(data_points, page_config.id, labels_dict)
            
            # Determine template to use - directly from page config
            template_name = None
            
            # Use template from page config (unified approach)
            if page_config.template.name:
                template_name = page_config.template.name
            
            # Render with Jinja2 template
            if template_name and engine.template_exists(template_name):
                log_verbose(f"  Using Jinja2 template: {template_name}", self.config)
                try:
                    html = engine.render(template_name, context, labels)
                except jinja2.TemplateError as e:
                    log_error(f"Template error for {page_config.id}: {e}")
                    if self.config.execution.verbose:
                        import traceback
                        traceback.print_exc()
                    html = f"<html><body><h1>Template Error: {page_config.id}</h1><pre>{e}</pre></body></html>"
                except Exception as e:
                    log_error(f"Unexpected error rendering {page_config.id}: {e}")
                    if self.config.execution.verbose:
                        import traceback
                        traceback.print_exc()
                    raise  # Re-raise unexpected errors
            else:
                log_warning(f"No template found for page: {page_config.id}", self.config)
                html = f"<html><body><h1>No template: {page_config.id}</h1></body></html>"
            
            # Write HTML file
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(html)
    
    def _generate_charts(self, data_points: List[Dict[str, Any]], page_type: str, labels: LabelConfig) -> Dict[str, str]:
        """
        DEPRECATED: Chart generation is now handled by plugin-provided chart generators.
        
        This method is kept for backward compatibility but should not be used.
        Instead, register a chart generator with the plugin registry using:
            registry.register_chart_generator(report_system_id, generator_class)
        """
        return {}

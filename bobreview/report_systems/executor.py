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
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from datetime import datetime
import os
import jinja2

from .schema import ReportSystemDefinition, LabelConfig

# Import from new package structure
from ..core import ReportConfig, log_info, log_verbose, log_warning, log_error, image_to_base64
from ..core.template_engine import get_template_engine

# Import services and plugin system
from ..services import get_container, DataService, AnalyticsService, ChartService, LLMService
from ..plugins import get_registry


class ReportSystemExecutor:
    """
    Executes a report system from JSON definition.
    
    Uses the services package for modular processing:
    - DataService for parsing
    - AnalyticsService for statistics
    - ChartService for chart generation
    
    Plugins can replace services via the ServiceContainer.
    """
    
    def __init__(self, system_def: ReportSystemDefinition, config: ReportConfig):
        """
        Initialize the executor with a report system definition.
        
        Parameters:
            system_def: Report system definition from JSON
            config: Report configuration (merged with JSON settings)
        """
        self.system_def = system_def
        self.config = config
        
        # Get service container
        self.container = get_container()
        self._ensure_services()
        
        self._merge_config()
    
    def _merge_config(self):
        """
        Merge JSON configuration into ReportConfig.
        
        Note: CLI overrides have already been merged into the JSON definition
        by the loader, so we just update the config with JSON values.
        The loader's merge_cli_overrides() ensures CLI arguments take precedence.
        """
        # Thresholds have already been merged in loader
        # The system_def.thresholds already contains CLI overrides
        for key, value in self.system_def.thresholds.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # LLM config has already been merged
        llm_cfg = self.system_def.llm_config
        self.config.openai_model = llm_cfg.model
        self.config.llm_temperature = llm_cfg.temperature
        self.config.llm_max_tokens = llm_cfg.max_tokens
        self.config.llm_chunk_size = llm_cfg.chunk_size
        self.config.use_cache = llm_cfg.enable_cache
        
        # Output config has already been merged
        output_cfg = self.system_def.output
        self.config.embed_images = output_cfg.embed_images
        self.config.linked_css = output_cfg.linked_css
        
        # Theme has already been merged
        theme_cfg = self.system_def.theme
        self.config.theme_id = theme_cfg.default
    
    def _ensure_services(self):
        """
        Ensure required services are available.
        
        Most services are registered by the core plugin.
        LLMService is registered here because it needs runtime config.
        """
        # Verify core services are available (registered by core plugin)
        required = ['data', 'analytics', 'charts']
        for service_name in required:
            if not self.container.has(service_name):
                raise RuntimeError(
                    f"Required service '{service_name}' not found. "
                    f"Ensure the core plugin is loaded."
                )
        
        # LLM service needs runtime config, so we register it here
        if not self.container.has('llm'):
            llm_config = {
                'provider': self.config.llm_provider,
                'api_key': self.config.llm_api_key,
                'model': getattr(self.config, 'openai_model', None) or self.config.llm_model,
                'temperature': self.config.llm_temperature,
                'max_tokens': self.config.llm_max_tokens,
                'use_cache': self.config.use_cache,
            }
            self.container.register('llm', LLMService(llm_config))
            log_verbose("Registered LLMService with runtime config", self.config)
    
    def execute(self, input_dir: Path, output_path: Path) -> bool:
        """
        Execute complete report generation pipeline.
        
        Parameters:
            input_dir: Directory containing input files
            output_path: Path for output HTML file
        
        Returns:
            True if report was generated successfully, False otherwise
        """
        log_info(f"Executing report system: {self.system_def.name}", self.config)
        log_verbose(f"System ID: {self.system_def.id} v{self.system_def.version}", self.config)
        
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
        return True
    
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
            sample_size=self.config.sample_size,
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
            dry_run=self.config.dry_run,
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
        if self.config.embed_images:
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
        
        # Get template engine
        engine = get_template_engine()
        
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
                
                # LLM generated content
                'llm': llm_content,
                'llm_content': llm_content,  # Alias for consistency
                
                # Navigation
                'nav_items': page_nav,
                'pages': [asdict(p) for p in enabled_pages],
                
                # Report system content blocks
                'content': self.system_def.content_blocks,
                
                # Meta
                'meta_text': f"{stats.get('count', len(data_points))} items · {self.config.location} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            }
            
            # Add plugin-provided context (images, critical points, game aliases, etc.)
            from ..plugins import get_registry
            context_builder_cls = get_registry().get_context_builder(self.system_def.id)
            if context_builder_cls:
                builder = context_builder_cls()
                plugin_context = builder.build(
                    data_points=data_points,
                    stats=stats,
                    config=self.config,
                    system_def=self.system_def,
                    input_dir=input_dir
                )
                context.update(plugin_context)
            
            # Add charts if page has chart configurations - use plugin-provided generator
            if page_config.charts:
                chart_generator_cls = get_registry().get_chart_generator(self.system_def.id)
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
                    if self.config.verbose:
                        import traceback
                        traceback.print_exc()
                    html = f"<html><body><h1>Template Error: {page_config.id}</h1><pre>{e}</pre></body></html>"
                except Exception as e:
                    log_error(f"Unexpected error rendering {page_config.id}: {e}")
                    if self.config.verbose:
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

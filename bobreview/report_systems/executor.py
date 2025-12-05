"""
Report system executor that orchestrates the entire report generation pipeline.

The executor takes a ReportSystemDefinition and executes it:
1. Parse data using configured data source
2. Calculate statistics based on metrics config  
3. Generate LLM content for configured generators
4. Generate HTML pages from page configs
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import os
import random

from .schema import ReportSystemDefinition
from .data_parser_base import DataParser, FilenamePatternParser
from .llm_generator_base import LLMGeneratorTemplate, LLMGeneratorAdapter

# Import from new package structure
from ..core import ReportConfig, analyze_data, log_info, log_verbose, log_warning, log_error, image_to_base64
from ..llm import call_llm, call_llm_chunked
from ..llm.generators import (
    generate_executive_summary,
    generate_metric_deep_dive,
    generate_zones_hotspots,
    generate_optimization_checklist,
    generate_system_recommendations,
    generate_visual_analysis,
    generate_statistical_interpretation
)

# Import page generators
from ..pages import homepage, metrics, zones, visuals, optimization, stats as stats_page


class ReportSystemExecutor:
    """Executes a report system from JSON definition."""
    
    def __init__(self, system_def: ReportSystemDefinition, config: ReportConfig):
        """
        Initialize the executor with a report system definition.
        
        Parameters:
            system_def: Report system definition from JSON
            config: Report configuration (merged with JSON settings)
        """
        self.system_def = system_def
        self.config = config
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
        
        # 1. Parse data
        data_points = self.parse_data(input_dir)
        if not data_points:
            log_warning("No data points found", self.config)
            return False
        
        log_info(f"Parsed {len(data_points)} data points", self.config)
        
        # 2. Calculate statistics
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
        Parse data using configured data source.
        
        Parameters:
            input_dir: Directory containing input files
        
        Returns:
            List of parsed data points
        """
        data_source_config = self.system_def.data_source
        
        # Create appropriate parser based on type
        parser: DataParser
        if data_source_config.type == 'filename_pattern':
            parser = FilenamePatternParser(data_source_config)
        else:
            raise ValueError(f"Unsupported data source type: {data_source_config.type}")
        
        # Parse directory
        data_points = parser.parse_directory(input_dir)
        
        # Apply sampling if configured
        if self.config.sample_size and self.config.sample_size < len(data_points):
            data_points = random.sample(data_points, self.config.sample_size)
        
        # Sort by timestamp if available
        if data_points and 'ts' in data_points[0]:
            data_points.sort(key=lambda x: x.get('ts', 0))
        
        return data_points
    
    def analyze_data(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics based on metrics config.
        
        Parameters:
            data_points: List of parsed data points
        
        Returns:
            Statistical analysis results
        """
        # Validate that data points have required fields
        if data_points:
            first_point = data_points[0]
            required_fields = ['draws', 'tris', 'ts']  # Required by existing analysis
            missing_fields = [f for f in required_fields if f not in first_point]
            
            if missing_fields:
                log_warning(
                    f"Data points missing required fields: {', '.join(missing_fields)}. "
                    f"Available fields: {', '.join(first_point.keys())}",
                    self.config
                )
        
        # Use existing analysis module (it already does what we need)
        # In future, we could make this configurable based on JSON metrics config
        try:
            return analyze_data(data_points, self.config)
        except KeyError as e:
            raise ValueError(
                f"Analysis failed: missing required field {e}. "
                f"Check that your data source configuration produces the required fields."
            ) from e
    
    def generate_llm_content(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate content for all LLM generators.
        
        Parameters:
            data_points: List of data points
            stats: Statistical analysis results
        
        Returns:
            Dictionary mapping generator ID to generated content
        """
        results = {}
        
        # Direct mapping of generator IDs to functions
        generator_funcs = {
            'executive_summary': generate_executive_summary,
            'Executive Summary': generate_executive_summary,
            'metric_deep_dive': generate_metric_deep_dive,
            'Metric Deep Dive': generate_metric_deep_dive,
            'zones_hotspots': generate_zones_hotspots,
            'Zones & Hotspots': generate_zones_hotspots,
            'optimization_checklist': generate_optimization_checklist,
            'Optimization Checklist': generate_optimization_checklist,
            'system_recommendations': generate_system_recommendations,
            'System Recommendations': generate_system_recommendations,
            'visual_analysis': generate_visual_analysis,
            'Visual Analysis': generate_visual_analysis,
            'statistical_interpretation': generate_statistical_interpretation,
            'Statistical Interpretation': generate_statistical_interpretation,
        }
        
        # Get enabled generators
        enabled_generators = [g for g in self.system_def.llm_generators if g.enabled]
        
        log_info(f"Generating LLM content for {len(enabled_generators)} sections...", self.config)
        
        for i, gen_config in enumerate(enabled_generators, 1):
            log_info(f"[{i}/{len(enabled_generators)}] Generating: {gen_config.name}", self.config)
            
            try:
                # Check if there's a direct Python generator
                gen_func = generator_funcs.get(gen_config.id) or generator_funcs.get(gen_config.name)
                if gen_func:
                    # Use direct Python generator
                    log_verbose(f"  Using Python generator: {gen_config.name}", self.config)
                    adapter = LLMGeneratorAdapter(gen_func, gen_config)
                    content = adapter.generate(data_points, stats, self.config, "")
                else:
                    # Use template-based generator
                    log_verbose(f"  Using template generator: {gen_config.name}", self.config)
                    template = LLMGeneratorTemplate(gen_config)
                    
                    # Select data samples
                    selected_data = template.select_data_samples(data_points, stats)
                    
                    # Build prompt
                    context = {
                        'location': self.config.location,
                        'title': self.config.title
                    }
                    context.update(self.system_def.thresholds)
                    
                    prompt = template.build_prompt(stats, selected_data, context)
                    
                    # Format data table
                    data_table = template.format_data_table(selected_data)
                    
                    # Call LLM
                    if self.config.dry_run:
                        content = f"<p>Dry run mode - {gen_config.name} would appear here</p>"
                    else:
                        content = call_llm(prompt, data_table=data_table, config=self.config)
                
                results[gen_config.id] = content
                log_verbose(f"  ✓ Generated {gen_config.name}", self.config)
                
            except Exception as e:
                log_error(f"Failed to generate {gen_config.name}: {e}")
                if self.config.verbose:
                    import traceback
                    traceback.print_exc()
                # Continue with other generators
                results[gen_config.id] = f"<p>Error generating content: {e}</p>"
        
        return results
    
    def generate_pages(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        llm_results: Dict[str, str],
        input_dir: Path,
        output_path: Path
    ):
        """
        Generate all configured pages.
        
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
        
        # Get enabled pages
        enabled_pages = [p for p in self.system_def.pages if p.enabled]
        
        # Map of Python page generators (for builtin templates)
        page_generators = {
            'homepage': homepage.generate_homepage,
            'metrics': metrics.generate_metrics_page,
            'zones': zones.generate_zones_page,
            'visuals': visuals.generate_visuals_page,
            'optimization': optimization.generate_optimization_page,
            'stats': stats_page.generate_stats_page
        }
        
        # Generate each page
        log_info(f"Generating {len(enabled_pages)} HTML pages...", self.config)
        
        for i, page_config in enumerate(enabled_pages, 1):
            page_path = output_dir / page_config.filename
            log_info(f"[{i}/{len(enabled_pages)}] Writing {page_config.filename}...", self.config)
            
            # Collect LLM content for this page
            page_llm_content = {}
            for llm_id in page_config.llm_content:
                if llm_id in llm_results:
                    page_llm_content[llm_id] = llm_results[llm_id]
            
            # Use builtin page generator if available
            if page_config.template.type == 'builtin' and page_config.template.name in page_generators:
                # Build kwargs based on page ID (different pages have different signatures)
                if page_config.id == 'home':
                    html = homepage.generate_homepage(
                        stats=stats,
                        config=self.config,
                        exec_summary=llm_results.get('executive_summary', '')
                    )
                elif page_config.id == 'metrics':
                    html = metrics.generate_metrics_page(
                        data_points=data_points,
                        stats=stats,
                        config=self.config,
                        metric_content=llm_results.get('metric_deep_dive', {})
                    )
                elif page_config.id == 'zones':
                    html = zones.generate_zones_page(
                        stats=stats,
                        images_dir_rel=images_dir_rel,
                        image_data_uris=image_data_uris,
                        config=self.config,
                        zones_content=llm_results.get('zones_hotspots', {})
                    )
                elif page_config.id == 'visuals':
                    html = visuals.generate_visuals_page(
                        data_points=data_points,
                        stats=stats,
                        config=self.config,
                        visual_analysis_content=llm_results.get('visual_analysis', '')
                    )
                elif page_config.id == 'optimization':
                    html = optimization.generate_optimization_page(
                        data_points=data_points,
                        stats=stats,
                        images_dir_rel=images_dir_rel,
                        image_data_uris=image_data_uris,
                        config=self.config,
                        optimization_content=llm_results.get('optimization_checklist', {}),
                        system_recs=llm_results.get('system_recommendations', {})
                    )
                elif page_config.id == 'stats':
                    html = stats_page.generate_stats_page(
                        data_points=data_points,
                        stats=stats,
                        images_dir_rel=images_dir_rel,
                        image_data_uris=image_data_uris,
                        config=self.config,
                        statistical_interpretation=llm_results.get('statistical_interpretation', '')
                    )
                else:
                    log_warning(f"Unknown page ID: {page_config.id}", self.config)
                    continue
            else:
                # Use template-based rendering (not fully implemented yet)
                log_warning(f"Custom templates not yet supported for page: {page_config.id}", self.config)
                continue
            
            # Write HTML file
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(html)


"""
Report system executor that orchestrates the entire report generation pipeline.

The executor takes a ReportSystemDefinition and executes it:
1. Parse data using configured data source
2. Calculate statistics based on metrics config  
3. Generate LLM content for configured generators
4. Generate HTML pages from Jinja2 templates (CMS-style)
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from datetime import datetime
import os
import random
import json
import jinja2

from .schema import ReportSystemDefinition, LabelConfig
from .data_parser_base import DataParser, FilenamePatternParser
from .llm_generator_base import LLMGeneratorTemplate, LLMGeneratorAdapter

# Import from new package structure
from ..core import ReportConfig, analyze_data, log_info, log_verbose, log_warning, log_error, image_to_base64
from ..core.template_engine import get_template_engine
from ..registry.themes import get_theme
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
        
        # Prepare image data for templates
        images = []
        for point in data_points:
            if 'img' in point:
                img_name = point['img']
                if img_name in image_data_uris:
                    src = image_data_uris[img_name]
                elif images_dir_rel:
                    src = f"{images_dir_rel}/{img_name}"
                else:
                    src = img_name
                images.append({
                    'src': src,
                    'testcase': point.get('testcase', ''),
                    'draws': point.get('draws', 0),
                    'tris': point.get('tris', 0)
                })
        
        # Template mapping for pages
        template_map = {
            'home': 'pages/homepage.html.j2',
            'metrics': 'pages/metrics.html.j2',
            'zones': 'pages/zones.html.j2',
            'visuals': 'pages/visuals.html.j2',
            'optimization': 'pages/optimization.html.j2',
            'stats': 'pages/stats.html.j2',
        }
        
        # LLM content mapping
        llm_key_map = {
            'home': {'exec_summary': 'executive_summary'},
            'metrics': {'metrics_analysis': 'metric_deep_dive'},
            'zones': {'zones_analysis': 'zones_hotspots'},
            'visuals': {'visual_analysis': 'visual_analysis'},
            'optimization': {'optimization': 'optimization_checklist', 'recommendations': 'system_recommendations'},
            'stats': {'stats_interpretation': 'statistical_interpretation'},
        }
        
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
            
            # Build LLM content dict for this page
            llm_content = {}
            if page_config.id in llm_key_map:
                for template_key, result_key in llm_key_map[page_config.id].items():
                    llm_content[template_key] = llm_results.get(result_key, '')
            
            # Get critical point for homepage
            critical = {
                'index': stats['critical'][0] if 'critical' in stats else 0,
                'draws': stats['critical'][1]['draws'] if 'critical' in stats else 0,
                'tris': stats['critical'][1]['tris'] if 'critical' in stats else 0,
            } if 'critical' in stats else {'index': 0, 'draws': 0, 'tris': 0}
            
            # Build base context for all templates
            context = {
                'config': self.config,
                'stats': stats,
                'data_points': data_points,
                'llm': llm_content,
                'nav_items': page_nav,
                'pages': [asdict(p) for p in enabled_pages],
                'images': images,
                'has_images': len(images) > 0,
                'critical': critical,
                'meta_text': f"{stats['count']} captures · {self.config.location} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            }
            
            # Add charts for visuals and metrics pages
            if page_config.id == 'visuals':
                context['charts'] = self._generate_charts(data_points, 'visuals', labels)
            elif page_config.id == 'metrics':
                context['charts'] = self._generate_charts(data_points, 'metrics', labels)
            
            # Determine template to use
            template_name = None
            
            # Check for custom template in page config
            if page_config.template.type == 'jinja2' and page_config.template.name:
                template_name = page_config.template.name
            elif page_config.id in template_map:
                template_name = template_map[page_config.id]
            
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
        """Generate Chart.js JavaScript code for charts with performance zones."""
        charts = {}
        labels_dict = asdict(labels)
        
        # Get theme colors for charts
        theme = get_theme()
        
        # Helper to convert hex to rgba
        def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        
        # Theme-based colors
        danger_color = hex_to_rgba(theme.danger, 0.9)
        danger_color_soft = hex_to_rgba(theme.danger, 0.7)
        danger_color_bg = hex_to_rgba(theme.danger, 0.8)
        ok_color = hex_to_rgba(theme.ok, 0.9)
        ok_color_soft = hex_to_rgba(theme.ok, 0.7)
        ok_color_bg = hex_to_rgba(theme.ok, 0.8)
        warn_color = hex_to_rgba(theme.warn, 0.9)
        warn_color_soft = hex_to_rgba(theme.warn, 0.7)
        accent_gradient_top = hex_to_rgba(theme.accent, 0.4)
        accent_gradient_bottom = hex_to_rgba(theme.accent, 0.02)
        accent_strong_gradient_top = hex_to_rgba(theme.accent_strong, 0.4)
        accent_strong_gradient_bottom = hex_to_rgba(theme.accent_strong, 0.02)
        grid_color = hex_to_rgba(theme.border_subtle, 0.5)
        grid_color_light = hex_to_rgba(theme.border_subtle, 0.3)
        tooltip_bg = hex_to_rgba(theme.bg_elevated, 0.95)
        
        # Get labels
        draws_label = labels_dict.get('draw_calls', 'Draw Calls')
        tris_label = labels_dict.get('triangles', 'Triangles')
        frame_index_label = labels_dict.get('frame_index', 'Frame Index')
        frequency_label = labels_dict.get('frequency', 'Frequency')
        
        # Performance thresholds
        high_draw = self.config.high_load_draw_threshold
        low_draw = self.config.low_load_draw_threshold
        high_tris = self.config.high_load_tri_threshold
        low_tris = self.config.low_load_tri_threshold
        
        if page_type == 'visuals':
            # Build data with color-coded points based on performance zones
            draws_points = []
            tris_points = []
            scatter_points = []
            
            for i, p in enumerate(data_points):
                draws = p['draws']
                tris = p['tris']
                testcase = p.get('testcase', f'Frame {i}')
                
                # Color for draw calls
                if draws >= high_draw:
                    draw_color = danger_color  # Red - critical
                elif draws < low_draw:
                    draw_color = ok_color  # Green - good
                else:
                    draw_color = warn_color  # Yellow - warning
                
                # Color for triangles
                if tris >= high_tris:
                    tri_color = danger_color
                elif tris < low_tris:
                    tri_color = ok_color
                else:
                    tri_color = warn_color
                
                # Scatter color (worst of both)
                if draws >= high_draw or tris >= high_tris:
                    scatter_color = hex_to_rgba(theme.danger, 0.8)
                elif draws < low_draw and tris < low_tris:
                    scatter_color = hex_to_rgba(theme.ok, 0.8)
                else:
                    scatter_color = hex_to_rgba(theme.warn, 0.8)
                
                draws_points.append({'x': i, 'y': draws, 'color': draw_color, 'testcase': testcase})
                tris_points.append({'x': i, 'y': tris, 'color': tri_color, 'testcase': testcase})
                scatter_points.append({'x': draws, 'y': tris, 'color': scatter_color, 'testcase': testcase, 'index': i})
            
            draws_data = json.dumps(draws_points)
            tris_data = json.dumps(tris_points)
            scatter_data = json.dumps(scatter_points)
            
            charts['draws_timeline'] = f"""
// Draw Calls Timeline with Performance Zones
(function() {{
    const ctx = document.getElementById('drawsTimeline').getContext('2d');
    const data = {draws_data};
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{accent_gradient_top}');
    gradient.addColorStop(1, '{accent_gradient_bottom}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: {json.dumps(draws_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                borderColor: '{theme.accent}',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: data.map(d => d.color),
                pointBorderColor: data.map(d => d.color),
                pointBorderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{ intersect: false, mode: 'index' }},
            scales: {{
                x: {{ 
                    type: 'linear',
                    title: {{ display: true, text: {json.dumps(frame_index_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(draws_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + items[0].parsed.x; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [
                                d.testcase,
                                {json.dumps(draws_label)} + ': ' + d.y.toLocaleString()
                            ];
                        }}
                    }}
                }},
                annotation: {{
                    annotations: {{
                        criticalLine: {{
                            type: 'line',
                            yMin: {high_draw},
                            yMax: {high_draw},
                            borderColor: '{danger_color_soft}',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {{ display: true, content: 'Critical ({high_draw})', position: 'end', backgroundColor: '{danger_color_bg}' }}
                        }},
                        warningLine: {{
                            type: 'line',
                            yMin: {low_draw},
                            yMax: {low_draw},
                            borderColor: '{ok_color_soft}',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {{ display: true, content: 'Good ({low_draw})', position: 'start', backgroundColor: '{ok_color_bg}' }}
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
            charts['tris_timeline'] = f"""
// Triangles Timeline with Performance Zones
(function() {{
    const ctx = document.getElementById('trisTimeline').getContext('2d');
    const data = {tris_data};
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{accent_strong_gradient_top}');
    gradient.addColorStop(1, '{accent_strong_gradient_bottom}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: {json.dumps(tris_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                borderColor: '{theme.accent_strong}',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: data.map(d => d.color),
                pointBorderColor: data.map(d => d.color),
                pointBorderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{ intersect: false, mode: 'index' }},
            scales: {{
                x: {{ 
                    type: 'linear',
                    title: {{ display: true, text: {json.dumps(frame_index_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(tris_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}', callback: function(v) {{ return v.toLocaleString(); }} }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent_strong}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + items[0].parsed.x; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [d.testcase, {json.dumps(tris_label)} + ': ' + d.y.toLocaleString()];
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
            scatter_label = f"{draws_label} vs {tris_label}"
            charts['scatter'] = f"""
// Scatter Plot with Performance Zone Colors
(function() {{
    const ctx = document.getElementById('scatterPlot').getContext('2d');
    const data = {scatter_data};
    
    new Chart(ctx, {{
        type: 'scatter',
        data: {{
            datasets: [{{
                label: {json.dumps(scatter_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                backgroundColor: data.map(d => d.color),
                borderColor: data.map(d => d.color.replace('0.8', '1')),
                pointRadius: 6,
                pointHoverRadius: 10,
                pointBorderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(draws_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(tris_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}', callback: function(v) {{ return v.toLocaleString(); }} }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + data[items[0].dataIndex].index; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [
                                d.testcase,
                                {json.dumps(draws_label)} + ': ' + d.x.toLocaleString(),
                                {json.dumps(tris_label)} + ': ' + d.y.toLocaleString()
                            ];
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
        elif page_type == 'metrics':
            # Histogram data with color-coded bars
            draws_values = [p['draws'] for p in data_points]
            tris_values = [p['tris'] for p in data_points]
            
            draws_hist = self._compute_histogram(draws_values, high_draw, low_draw)
            tris_hist = self._compute_histogram(tris_values, high_tris, low_tris)
            
            charts['draws_histogram'] = f"""
// Draw Calls Distribution
(function() {{
    const ctx = document.getElementById('drawsHistogram').getContext('2d');
    
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(draws_hist['labels'])},
            datasets: [{{
                label: {json.dumps(frequency_label)},
                data: {json.dumps(draws_hist['counts'])},
                backgroundColor: {json.dumps(draws_hist['colors'])},
                borderColor: {json.dumps([c.replace('0.7', '1') for c in draws_hist['colors']])},
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(draws_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color_light}' }},
                    ticks: {{ color: '{theme.text_soft}', maxRotation: 45 }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(frequency_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }},
                    beginAtZero: true
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1,
                    padding: 10
                }}
            }}
        }}
    }});
}})();
"""
            charts['tris_histogram'] = f"""
// Triangles Distribution
(function() {{
    const ctx = document.getElementById('trisHistogram').getContext('2d');
    
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(tris_hist['labels'])},
            datasets: [{{
                label: {json.dumps(frequency_label)},
                data: {json.dumps(tris_hist['counts'])},
                backgroundColor: {json.dumps(tris_hist['colors'])},
                borderColor: {json.dumps([c.replace('0.7', '1') for c in tris_hist['colors']])},
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(tris_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color_light}' }},
                    ticks: {{ color: '{theme.text_soft}', maxRotation: 45 }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(frequency_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }},
                    beginAtZero: true
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent_strong}',
                    borderWidth: 1,
                    padding: 10
                }}
            }}
        }}
    }});
}})();
"""
        return charts
    
    def _compute_histogram(self, values: List[float], high_threshold: float = None, low_threshold: float = None, num_bins: int = 15) -> Dict[str, Any]:
        """Compute histogram bins with performance zone colors."""
        if not values:
            return {'labels': [], 'counts': [], 'colors': []}
        
        # Get theme colors
        theme = get_theme()
        
        # Helper to convert hex to rgba
        def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        
        danger_rgba = hex_to_rgba(theme.danger, 0.7)
        ok_rgba = hex_to_rgba(theme.ok, 0.7)
        warn_rgba = hex_to_rgba(theme.warn, 0.7)
        accent_rgba = hex_to_rgba(theme.accent, 0.7)
        
        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            return {'labels': [str(int(min_val))], 'counts': [len(values)], 'colors': [accent_rgba]}
        
        bin_width = (max_val - min_val) / num_bins
        counts = [0] * num_bins
        
        for v in values:
            idx = int((v - min_val) / bin_width)
            if idx >= num_bins:
                idx = num_bins - 1
            counts[idx] += 1
        
        labels = []
        colors = []
        for i in range(num_bins):
            bin_center = min_val + (i + 0.5) * bin_width
            labels.append(f"{int(min_val + i * bin_width)}-{int(min_val + (i+1) * bin_width)}")
            
            # Color based on performance zone using theme colors
            if high_threshold and bin_center >= high_threshold:
                colors.append(danger_rgba)  # Red - critical
            elif low_threshold and bin_center < low_threshold:
                colors.append(ok_rgba)  # Green - good
            else:
                colors.append(warn_rgba)  # Yellow - warning
        
        return {'labels': labels, 'counts': counts, 'colors': colors}


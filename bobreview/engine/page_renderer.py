"""
Page Renderer for report generation.

Extracted from ReportSystemExecutor.generate_pages() to reduce class complexity
and provide a reusable, testable component for page rendering.

This class handles:
- Template context building
- Image encoding (base64 or file paths)
- Chart generation via plugin-provided generators
- Context enrichment via plugin-provided context builders
- Jinja2 template rendering
- Multi-page report generation
"""

import os
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import jinja2

from ..core import log_info, log_verbose, log_warning, log_error, image_to_base64
from .schema import PageConfig, LabelConfig

if TYPE_CHECKING:
    from ..core.template_engine import TemplateEngine
    from ..core.plugin_system import IExtensionPoint
    from ..core.config import ReportConfig
    from .schema import ReportSystemDefinition


class PageRenderer:
    """
    Renders HTML pages from templates and data.
    
    Extracted from ReportSystemExecutor for better modularity.
    Handles all aspects of page rendering including context building,
    chart generation, and template rendering.
    """
    
    def __init__(
        self,
        template_engine: 'TemplateEngine',
        extension_point: Optional['IExtensionPoint'],
        config: 'ReportConfig',
        system_def: 'ReportSystemDefinition'
    ):
        """
        Initialize the page renderer.
        
        Parameters:
            template_engine: Jinja2 template engine
            extension_point: Plugin extension point for context/chart lookups
            config: Report configuration
            system_def: Report system definition
        """
        self.engine = template_engine
        self.extension_point = extension_point
        self.config = config
        self.system_def = system_def
        self.labels = system_def.labels
    
    def render_all_pages(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        llm_results: Dict[str, str],
        input_dir: Path,
        output_path: Path
    ) -> None:
        """
        Render all enabled pages to the output directory.
        
        Parameters:
            data_points: Parsed data points
            stats: Statistical analysis results
            llm_results: Generated LLM content
            input_dir: Input directory (for images)
            output_path: Output file path (determines output directory)
        """
        # Pre-encode images if needed
        image_data_uris = self._encode_images(data_points, input_dir)
        
        # Determine output directory
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate relative images directory
        images_dir_rel = os.path.relpath(input_dir, output_dir)
        
        # Get enabled pages
        enabled_pages = [p for p in self.system_def.pages if p.enabled]
        
        # Build navigation items
        nav_items = [
            {'label': page.nav_label, 'url': page.filename, 'active': False}
            for page in enabled_pages
        ]
        
        # Build base context (shared by all pages)
        base_context = self._build_base_context(
            data_points=data_points,
            stats=stats,
            llm_results=llm_results,
            image_data_uris=image_data_uris,
            images_dir_rel=images_dir_rel,
            nav_items=nav_items,
            enabled_pages=enabled_pages,
            input_dir=input_dir
        )
        
        # Generate each page
        log_info(f"Generating {len(enabled_pages)} HTML pages...", self.config)
        
        for i, page_config in enumerate(enabled_pages, 1):
            self._render_page(
                page_config=page_config,
                base_context=base_context,
                data_points=data_points,
                stats=stats,
                output_dir=output_dir,
                page_index=i,
                total_pages=len(enabled_pages)
            )
    
    def _encode_images(
        self,
        data_points: List[Dict[str, Any]],
        input_dir: Path
    ) -> Dict[str, str]:
        """Encode images as base64 data URIs if embedding is enabled."""
        image_data_uris = {}
        
        if self.config.output.embed_images:
            log_info("Embedding images as base64...", self.config)
            unique_images = set(
                point.get('img', '') for point in data_points if 'img' in point
            )
            for img_name in unique_images:
                if img_name:
                    img_path = input_dir / img_name
                    data_uri = image_to_base64(img_path)
                    if data_uri:
                        image_data_uris[img_name] = data_uri
        
        return image_data_uris
    
    def _build_base_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        llm_results: Dict[str, str],
        image_data_uris: Dict[str, str],
        images_dir_rel: str,
        nav_items: List[Dict[str, Any]],
        enabled_pages: List[PageConfig],
        input_dir: Path
    ) -> Dict[str, Any]:
        """Build the base context shared by all pages."""
        from datetime import datetime
        from ..core.themes import get_theme_by_id, theme_to_dict
        
        count = stats.get('count', len(data_points))
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        meta_text = f"{count} items · Generated {timestamp}"
        
        # Theme resolution priority: CLI --theme > JSON preset > fallback dark
        theme_name = "dark"  # Fallback
        
        # Check JSON preset first
        if self.system_def.theme:
            if isinstance(self.system_def.theme, str):
                theme_name = self.system_def.theme
            elif isinstance(self.system_def.theme, dict):
                theme_name = self.system_def.theme.get('preset', 'dark')
        
        # CLI --theme overrides JSON preset
        if hasattr(self.config.output, 'theme_id') and self.config.output.theme_id:
            theme_name = self.config.output.theme_id
        
        # Get theme from built-in themes (fallback to dark if not found)
        theme = get_theme_by_id(theme_name)
        if not theme:
            from ..core.themes import DARK_THEME
            theme = DARK_THEME
        theme_vars = theme_to_dict(theme)
        
        return {
            # Core data
            'config': self.config,
            'stats': stats,
            'data': stats,  # Universal alias
            'data_points': data_points,
            'system_def': self.system_def,
            
            # Theme (for dynamic styling)
            'theme': theme_vars,
            'theme_name': theme_name,
            
            # LLM content (empty initially, populated per-page)
            'llm': {},
            'llm_content': {},
            
            # Navigation
            'nav_items': nav_items,
            'pages': [asdict(p) for p in enabled_pages],
            
            # Content blocks from report system
            'content': self.system_def.content_blocks,
            
            # Images
            'image_data_uris': image_data_uris,
            'images_dir_rel': images_dir_rel,
            
            # Meta
            'meta_text': meta_text,
            
            # For context builder
            'input_dir': input_dir,
            
            # Output options (for template CSS switching)
            'linked_css': self.config.output.linked_css if hasattr(self.config.output, 'linked_css') else True,
        }
    
    def _render_page(
        self,
        page_config: PageConfig,
        base_context: Dict[str, Any],
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        output_dir: Path,
        page_index: int,
        total_pages: int
    ) -> None:
        """Render a single page."""
        page_path = output_dir / page_config.filename
        log_info(f"[{page_index}/{total_pages}] Rendering {page_config.filename}...", self.config)
        
        # Build page-specific context
        context = dict(base_context)
        
        # Update navigation: mark current page as active
        context['nav_items'] = [
            {**nav, 'active': nav['url'] == page_config.filename}
            for nav in base_context['nav_items']
        ]
        
        # Build LLM content for this page
        context['llm'] = self._build_llm_content(page_config, base_context.get('_llm_results', {}))
        context['llm_content'] = context['llm']
        
        # Add context from plugin-provided context builder
        context = self._apply_context_builder(context, data_points, stats)
        
        # Add charts if page has chart configurations
        if page_config.charts:
            charts = self._generate_charts(page_config, data_points, stats)
            if charts:
                context['charts'] = charts
        
        # Render template
        html = self._render_template(page_config, context)
        
        # Write HTML file
        with open(page_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _build_llm_content(
        self,
        page_config: PageConfig,
        llm_results: Dict[str, str]
    ) -> Dict[str, str]:
        """Build LLM content dict for a page."""
        llm_content = {}
        
        if page_config.llm_mappings:
            for template_key, generator_id in page_config.llm_mappings.items():
                llm_content[template_key] = llm_results.get(generator_id, '')
        elif page_config.llm_content:
            for generator_id in page_config.llm_content:
                llm_content[generator_id] = llm_results.get(generator_id, '')
        
        return llm_content
    
    def _apply_context_builder(
        self,
        context: Dict[str, Any],
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply plugin-provided context builder."""
        if not self.extension_point:
            return context
        
        context_builder_cls = self.extension_point.get_context_builder(self.system_def.id)
        if not context_builder_cls:
            return context
        
        try:
            builder = context_builder_cls()
            base_context = {
                'system_def': self.system_def,
                'input_dir': context.get('input_dir'),
                'image_data_uris': context.get('image_data_uris'),
                'images_dir_rel': context.get('images_dir_rel'),
            }
            plugin_context = builder.build_context(
                data_points=data_points,
                stats=stats,
                config=self.config,
                base_context=base_context
            )
            context.update(plugin_context)
        except Exception as e:
            log_warning(f"Context builder failed: {e}", self.config)
        
        return context
    
    def _generate_charts(
        self,
        page_config: PageConfig,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate charts for a page using plugin-provided generator."""
        if not self.extension_point:
            return {}
        
        chart_generator_cls = self.extension_point.get_chart_generator(self.system_def.id)
        if not chart_generator_cls:
            log_warning(
                f"No chart generator found for report system '{self.system_def.id}'",
                self.config
            )
            return {}
        
        try:
            chart_generator = chart_generator_cls()
            labels_dict = self.labels.data if hasattr(self.labels, 'data') else {}
            
            charts_dict = {}
            for chart_config in page_config.charts:
                chart_config_dict = {
                    'id': chart_config.id,
                    'type': chart_config.type,
                    'title': chart_config.title,
                    'x_field': chart_config.x_field,
                    'y_field': chart_config.y_field,
                    'options': chart_config.options,
                    'labels': labels_dict,
                }
                
                try:
                    chart_result = chart_generator.generate_chart(
                        data_points=data_points,
                        stats=stats,
                        config=self.config,
                        chart_config=chart_config_dict
                    )
                    charts_dict[chart_config.id] = chart_result
                    log_verbose(f"Generated chart: {chart_config.id}", self.config)
                except Exception as e:
                    log_warning(f"Failed to generate chart {chart_config.id}: {e}", self.config)
            
            return charts_dict
            
        except Exception as e:
            log_warning(f"Chart generator initialization failed: {e}", self.config)
            return {}
    
    def _render_template(
        self,
        page_config: PageConfig,
        context: Dict[str, Any]
    ) -> str:
        """Render the page template."""
        template_name = None
        
        if page_config.template.name:
            template_name = page_config.template.name
        
        if template_name and self.engine.template_exists(template_name):
            log_verbose(f"  Using template: {template_name}", self.config)
            try:
                return self.engine.render(template_name, context, self.labels)
            except jinja2.TemplateError as e:
                log_error(f"Template error for {page_config.id}: {e}")
                return f"<html><body><h1>Template Error: {page_config.id}</h1><pre>{e}</pre></body></html>"
            except Exception as e:
                log_error(f"Unexpected error rendering {page_config.id}: {e}")
                raise
        else:
            log_warning(f"No template found for page: {page_config.id}", self.config)
            return f"<html><body><h1>No template: {page_config.id}</h1></body></html>"

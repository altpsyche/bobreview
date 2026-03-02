"""
Component Renderer - Renders validated components to HTML.

This module provides the ComponentRenderer which takes validated components
and renders them to HTML using their associated templates.

The renderer is the core of the plugin-first architecture:
1. User defines components in YAML
2. ComponentProcessor validates against plugin-defined schemas
3. ComponentRenderer renders each component using plugin templates
4. Final HTML is assembled from rendered components

Usage:
    from bobreview.core.components import get_component_processor
    from bobreview.core.components.renderer import ComponentRenderer
    
    processor = get_component_processor()
    renderer = ComponentRenderer(template_engine)
    
    # Render a single component
    validated = processor.process(component_yaml)
    html = renderer.render_component(validated, context)
    
    # Render a page of components
    html = renderer.render_page(components_list, context, layout="grid")
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import threading

from .processor import ValidatedComponent, get_component_processor

logger = logging.getLogger(__name__)


@dataclass
class RenderedComponent:
    """Result of rendering a component."""
    html: str
    component_type: str
    component_id: Optional[str] = None


class ComponentRenderer:
    """
    Renders validated components to HTML.
    
    The renderer uses the template engine to render each component's
    template with its validated props and the page context.
    """
    
    def __init__(self, template_engine):
        """
        Initialize renderer with a template engine.
        
        Parameters:
            template_engine: TemplateEngine instance for rendering Jinja2 templates
        """
        self.template_engine = template_engine
        self.processor = get_component_processor()
    
    def render_component(
        self,
        component: ValidatedComponent,
        context: Dict[str, Any]
    ) -> RenderedComponent:
        """
        Render a single validated component to HTML.
        
        Parameters:
            component: ValidatedComponent from ComponentProcessor
            context: Page context (data, stats, theme, etc.)
        
        Returns:
            RenderedComponent with HTML and metadata
        """
        if not component.template:
            logger.warning(
                f"Component '{component.component_type}' has no template, "
                "returning empty HTML"
            )
            return RenderedComponent(
                html="",
                component_type=component.component_type,
                component_id=component.props.get("id")
            )
        
        # Build template context with props and page context
        template_context = {
            **context,
            "props": component.props,
            "component_type": component.component_type,
        }
        
        try:
            html = self.template_engine.render(
                component.template,
                template_context
            )
        except Exception as e:
            logger.error(
                f"Failed to render component '{component.component_type}': {e}"
            )
            # Return error placeholder
            html = f'<div class="component-error">Error rendering {component.component_type}: {e}</div>'
        
        return RenderedComponent(
            html=html,
            component_type=component.component_type,
            component_id=component.props.get("id")
        )
    
    def render_components(
        self,
        components: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[RenderedComponent]:
        """
        Render a list of component definitions to HTML.
        
        Parameters:
            components: List of component YAML definitions
            context: Page context
        
        Returns:
            List of RenderedComponent objects
        """
        rendered = []
        
        for comp_def in components:
            # Process (validate) the component
            try:
                validated = self.processor.process(comp_def)
            except Exception as e:
                logger.error(f"Failed to process component: {e}")
                rendered.append(RenderedComponent(
                    html=f'<div class="component-error">Invalid component: {e}</div>',
                    component_type=comp_def.get("type", "unknown"),
                    component_id=comp_def.get("id")
                ))
                continue
            
            # Render the validated component
            result = self.render_component(validated, context)
            rendered.append(result)
        
        return rendered
    
    def render_page(
        self,
        components: List[Dict[str, Any]],
        context: Dict[str, Any],
        layout: str = "single-column",
        page_template: Optional[str] = None
    ) -> str:
        """
        Render a complete page from component definitions.
        
        Parameters:
            components: List of component YAML definitions
            context: Page context (data, stats, theme, nav, etc.)
            layout: Layout type ("grid", "flex", "single-column")
            page_template: Optional page wrapper template
        
        Returns:
            Complete HTML for the page
        """
        # Render all components
        rendered = self.render_components(components, context)
        
        # Combine into page HTML
        component_html = "\n".join(r.html for r in rendered)
        
        # Apply layout wrapper
        layout_class = f"layout-{layout}"
        wrapped_html = f'<div class="{layout_class}">\n{component_html}\n</div>'
        
        # If page template provided, render through it
        if page_template:
            page_context = {
                **context,
                "content": wrapped_html,
                "components": rendered,
            }
            try:
                return self.template_engine.render(page_template, page_context)
            except Exception as e:
                logger.error(f"Failed to render page template: {e}")
                return wrapped_html
        
        return wrapped_html


# Singleton instance
_renderer_instance: Optional[ComponentRenderer] = None
_renderer_lock = threading.Lock()


def get_component_renderer(template_engine=None) -> ComponentRenderer:
    """
    Get or create the global ComponentRenderer instance (thread-safe).

    Parameters:
        template_engine: TemplateEngine instance (required on first call)

    Returns:
        ComponentRenderer singleton
    """
    global _renderer_instance

    if _renderer_instance is None:
        with _renderer_lock:
            if _renderer_instance is None:
                if template_engine is None:
                    raise ValueError(
                        "template_engine is required when creating ComponentRenderer"
                    )
                _renderer_instance = ComponentRenderer(template_engine)

    return _renderer_instance


def reset_component_renderer():
    """Reset the renderer singleton (for testing)."""
    global _renderer_instance
    with _renderer_lock:
        _renderer_instance = None

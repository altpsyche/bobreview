"""
Jinja2 template engine for CMS-style report generation.

All UI text labels come from JSON configuration - no hardcoded strings.
"""

from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import asdict

from jinja2 import (
    Environment,
    FileSystemLoader,
    PackageLoader,
    ChoiceLoader,
    TemplateNotFound,
    select_autoescape,
)

if TYPE_CHECKING:
    from ..report_systems.schema import LabelConfig

from .utils import format_number
from ..pages.base import sanitize_llm_html, get_shared_css, get_trend_icon


# Global template engine instance
_engine_instance: Optional["TemplateEngine"] = None


class TemplateEngine:
    """
    Jinja2 template engine with multi-source loading.
    
    Load order:
    1. User templates: ~/.bobreview/templates/
    2. Package built-in templates: bobreview/templates/
    """
    
    def __init__(self, custom_paths: Optional[list] = None):
        """
        Initialize the template engine.
        
        Parameters:
            custom_paths: Optional list of additional template directories
        """
        loaders = []
        
        # User templates directory
        user_template_dir = Path.home() / '.bobreview' / 'templates'
        if user_template_dir.exists():
            loaders.append(FileSystemLoader(str(user_template_dir)))
        
        # Custom paths from config
        if custom_paths:
            for path in custom_paths:
                if Path(path).exists():
                    loaders.append(FileSystemLoader(str(path)))
        
        # Package built-in templates
        loaders.append(PackageLoader('bobreview', 'templates'))
        
        self.env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(['html', 'xml', 'j2']),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Register custom filters
        self._register_filters()
        
        # Register custom globals
        self._register_globals()
    
    def _register_filters(self):
        """Register custom Jinja2 filters."""
        self.env.filters['format_number'] = format_number
        self.env.filters['sanitize'] = self._smart_sanitize
        self.env.filters['trend_icon'] = get_trend_icon
        self.env.filters['default_str'] = lambda x, d='': x if x else d
    
    def _smart_sanitize(self, content):
        """
        Sanitize LLM content - handles both string and dict.
        
        If content is a dict, extracts string values and joins them.
        If content is a string, sanitizes directly.
        Returns Markup to prevent double-escaping by Jinja2.
        """
        from markupsafe import Markup
        
        if content is None:
            return Markup('')
        if isinstance(content, dict):
            # Extract all string values from dict and join
            parts = []
            for key, value in content.items():
                if isinstance(value, str):
                    parts.append(sanitize_llm_html(value))
                elif isinstance(value, dict):
                    # Nested dict - recursively extract
                    for k, v in value.items():
                        if isinstance(v, str):
                            parts.append(sanitize_llm_html(v))
            return Markup('\n'.join(parts) if parts else '')
        return Markup(sanitize_llm_html(str(content)))
    
    def _register_globals(self):
        """Register global template functions."""
        self.env.globals['get_css'] = get_shared_css
    
    def render(
        self, 
        template_name: str, 
        context: Dict[str, Any],
        labels: Optional["LabelConfig"] = None
    ) -> str:
        """
        Render a template with the given context.
        
        Parameters:
            template_name: Name of the template file (e.g., 'pages/homepage.html.j2')
            context: Dictionary of template variables
            labels: Optional LabelConfig for UI text labels
        
        Returns:
            Rendered HTML string
        """
        # Always inject labels into context
        if labels:
            context['labels'] = asdict(labels)
        
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def render_string(
        self, 
        template_string: str, 
        context: Dict[str, Any],
        labels: Optional["LabelConfig"] = None
    ) -> str:
        """
        Render an inline template string.
        
        Parameters:
            template_string: Raw Jinja2 template string
            context: Dictionary of template variables
            labels: Optional LabelConfig for UI text labels
        
        Returns:
            Rendered string
        """
        if labels:
            context['labels'] = asdict(labels)
        
        template = self.env.from_string(template_string)
        return template.render(**context)
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            self.env.get_template(template_name)
        except TemplateNotFound:
            return False
        else:
            return True


def get_template_engine(custom_paths: Optional[list] = None) -> TemplateEngine:
    """
    Get or create the global template engine instance.
    
    Parameters:
        custom_paths: Optional list of additional template directories
    
    Returns:
        TemplateEngine instance
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TemplateEngine(custom_paths)
    return _engine_instance


def reset_template_engine():
    """Reset the global template engine (for testing)."""
    global _engine_instance
    _engine_instance = None

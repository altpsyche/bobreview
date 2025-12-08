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
    
    Load order (first match wins):
    1. User templates: ~/.bobreview/templates/
    2. Custom paths (if provided via custom_paths parameter)
    3. Package built-in templates: bobreview/templates/
    """
    
    def __init__(self, custom_paths: Optional[list] = None):
        """
        Initialize the template engine.
        
        Load order (first match wins):
        1. User templates: ~/.bobreview/templates/
        2. Custom paths (if provided)
        3. Plugin-registered templates (from PluginRegistry)
        4. Package built-in templates (fallback)
        
        Parameters:
            custom_paths: Optional list of additional template directories
        """
        loaders = []
        
        # User templates directory (highest priority)
        user_template_dir = Path.home() / '.bobreview' / 'templates'
        if user_template_dir.exists():
            loaders.append(FileSystemLoader(str(user_template_dir)))
        
        # Custom paths from config
        if custom_paths:
            for path in custom_paths:
                if Path(path).exists():
                    loaders.append(FileSystemLoader(str(path)))
        
        # Plugin-registered template paths (in priority order)
        # Lower priority number = higher priority (loaded first)
        try:
            from ..plugins import get_registry
            registry = get_registry()
            # Get template paths with priority information
            template_registrations = registry.template_paths.get_all_registrations()
            # Already sorted by priority (lower number = higher priority)
            sorted_registrations = template_registrations
            for template_path, plugin_name, priority in sorted_registrations:
                if template_path.exists():
                    loaders.append(FileSystemLoader(str(template_path)))
        except ImportError:
            pass
        
        # Package built-in templates (lowest priority fallback)
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
        self.env.filters['interpolate'] = self._interpolate
    
    def _interpolate(self, template_str: str, context: Any = None) -> str:
        """
        Interpolate {key} placeholders in a string with values from context.
        
        Supports:
        - {key} - direct lookup
        - {config.draw_soft_cap} - nested path lookup
        - Multiple placeholders in one string
        
        Example:
            "Soft cap {draw_soft_cap} · hard cap {draw_hard_cap}" | interpolate(config)
        
        Parameters:
            template_str: String with {key} placeholders
            context: Dict or object to look up values from
            
        Returns:
            String with placeholders replaced by values
        """
        import re
        from markupsafe import Markup
        
        if not template_str or context is None:
            return template_str or ''
        
        # Convert dataclass or object to dict if needed
        if hasattr(context, '__dict__') and not isinstance(context, dict):
            ctx = vars(context) if hasattr(context, '__dict__') else {}
        elif isinstance(context, dict):
            ctx = context
        else:
            ctx = {}
        
        def replace_var(match):
            var_path = match.group(1)
            
            # Handle nested paths like config.draw_soft_cap
            parts = var_path.split('.')
            value = ctx
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    # Variable not found, keep original placeholder
                    return match.group(0)
            
            # Format numbers nicely
            # For game dev metrics, most values are counts (draws, tris) so show as integers
            if isinstance(value, float):
                rounded = round(value)
                # Always show as integer if it's a "typical count" value
                if value >= 1000:
                    return f"{rounded:,}"
                # For smaller values, show as integer (no decimals for draws/tris)
                return str(rounded)
            if isinstance(value, int) and value >= 1000:
                return f"{value:,}"
            return str(value)
        
        # Find all {var} or {var.path} patterns
        result = re.sub(r'\{([^}]+)\}', replace_var, template_str)
        return Markup(result)

    
    def _smart_sanitize(self, content):
        """
        Sanitize LLM content - handles both string and dict.
        
        If content is a dict, recursively extracts all string values and joins them.
        If content is a string, sanitizes directly.
        Returns Markup to prevent double-escaping by Jinja2.
        
        Note: All content is sanitized via sanitize_llm_html before wrapping in Markup,
        which is safe from an XSS perspective.
        """
        from markupsafe import Markup
        
        if content is None:
            return Markup('')
        
        def _gather_strings(obj):
            """Recursively gather all string values from nested structures."""
            if isinstance(obj, str):
                return [sanitize_llm_html(obj)]
            if isinstance(obj, dict):
                parts = []
                for _key, v in obj.items():
                    parts.extend(_gather_strings(v))
                return parts
            return []
        
        if isinstance(content, dict):
            # Extract all string leaves from nested dicts and join
            parts = _gather_strings(content)
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
            context: Dictionary of template variables (not mutated)
            labels: Optional LabelConfig for UI text labels
        
        Returns:
            Rendered HTML string
        """
        # Copy context to avoid mutating caller's dict
        data = dict(context)
        if labels:
            # Labels is now a simple wrapper class, not a dataclass
            data['labels'] = labels
        
        template = self.env.get_template(template_name)
        return template.render(**data)
    
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
            context: Dictionary of template variables (not mutated)
            labels: Optional LabelConfig for UI text labels
        
        Returns:
            Rendered string
        """
        # Copy context to avoid mutating caller's dict
        data = dict(context)
        if labels:
            # Labels is now a simple wrapper class, not a dataclass
            data['labels'] = labels
        
        template = self.env.from_string(template_string)
        return template.render(**data)
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            self.env.get_template(template_name)
        except TemplateNotFound:
            return False
        else:
            return True


def get_template_engine(custom_paths: Optional[list] = None, force_refresh: bool = False) -> TemplateEngine:
    """
    Get or create the global template engine instance.
    
    Parameters:
        custom_paths: Optional list of additional template directories (only used on first call).
            Note: This parameter is only honored when the engine is first created.
            Subsequent calls with different custom_paths will return the existing
            instance. To create a new instance with different paths, call
            reset_template_engine() first.
        force_refresh: If True, recreate the engine to pick up new plugin templates.
    
    Returns:
        TemplateEngine instance
    """
    global _engine_instance
    if _engine_instance is None or force_refresh:
        _engine_instance = TemplateEngine(custom_paths)
    return _engine_instance


def reset_template_engine():
    """Reset the global template engine (for testing)."""
    global _engine_instance
    _engine_instance = None

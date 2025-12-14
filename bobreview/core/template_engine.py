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
    from ..engine.schema import Labels

from .utils import format_number
from .html_utils import sanitize_llm_html, get_shared_css, get_trend_icon
from .theme_system import get_theme_css
from .plugin_system import get_extension_point


# Global template engine instance
_engine_instance: Optional["TemplateEngine"] = None


class TemplateEngine:
    """
    Jinja2 template engine with multi-source loading.
    
    Load order (first match wins):
    1. User templates: ~/.bobreview/templates/
    2. Custom paths (if provided via custom_paths parameter)
    3. Plugin-registered templates (from PluginRegistry)
    """
    
    def __init__(self, custom_paths: Optional[list] = None):
        """
        Initialize the template engine.
        
        Load order (first match wins):
        1. User templates: ~/.bobreview/templates/
        2. Custom paths (if provided)
        3. Plugin-registered templates (from PluginRegistry)
        
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
        extension_point = get_extension_point()
        # Get template paths with priority information
        template_registrations = extension_point.get_template_paths()
        # Already sorted by priority (lower number = higher priority)
        sorted_registrations = template_registrations
        for template_path, plugin_name, priority in sorted_registrations:
            if template_path.exists():
                loaders.append(FileSystemLoader(str(template_path)))
        
        # Require at least one template source
        if not loaders:
            raise ValueError(
                "No template sources found. Templates must be provided by plugins. "
                "Ensure at least one plugin with templates is loaded."
            )
        
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
        - {config.threshold_name} - nested path lookup
        - Multiple placeholders in one string
        
        Example:
            "Threshold: {threshold_name} · Value: {value}" | interpolate(context)
        
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
        
        # Keep reference to original context for nested lookups
        original_context = context
        
        # Convert dataclass or object to dict if needed
        # Keep original context for attribute access (dataclasses, objects)
        if isinstance(context, dict):
            ctx = context
        elif hasattr(context, '__dict__'):
            # For dataclasses/objects, create a dict but keep original for attribute access
            ctx = vars(context) if hasattr(context, '__dict__') else {}
        else:
            ctx = {}
        
        def replace_var(match):
            var_path = match.group(1)
            
            # Handle nested paths like config.threshold_name or simple names
            parts = var_path.split('.')
            value = ctx if isinstance(ctx, dict) else original_context
            found = False
            
            # Try direct lookup first (works for dict or object with nested paths)
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                    found = True
                elif hasattr(value, part):
                    value = getattr(value, part)
                    found = True
                elif isinstance(value, dict):
                    # For dict subclasses like ThresholdConfig, try __getitem__ even if hasattr fails
                    try:
                        value = value[part]
                        found = True
                    except (KeyError, TypeError):
                        found = False
                        break
                else:
                    found = False
                    break
            
            # If simple name not found, try looking in thresholds
            # Priority: system_def.thresholds (report system JSON) > config.thresholds (defaults)
            if not found and len(parts) == 1:
                simple_name = parts[0]
                
                # Priority 1: Try system_def.thresholds (from report system JSON) - this is the source of truth
                if isinstance(ctx, dict) and 'system_def' in ctx:
                    system_def = ctx['system_def']
                    if hasattr(system_def, 'thresholds'):
                        thresholds = system_def.thresholds
                        if isinstance(thresholds, dict) and simple_name in thresholds:
                            value = thresholds[simple_name]
                            found = True
                        elif hasattr(thresholds, simple_name):
                            value = getattr(thresholds, simple_name)
                            found = True
                
                # Priority 2: Try if context is a dict with 'config' key
                if not found and isinstance(ctx, dict) and 'config' in ctx:
                    config_obj = ctx['config']
                    if hasattr(config_obj, 'thresholds'):
                        thresholds = config_obj.thresholds
                        # ThresholdConfig is a dict, so use dict access
                        if isinstance(thresholds, dict) and simple_name in thresholds:
                            value = thresholds[simple_name]
                            found = True
                        elif hasattr(thresholds, simple_name):
                            value = getattr(thresholds, simple_name)
                            found = True
                
                # Priority 3: Try if context itself is a config object with thresholds
                if not found:
                    config_obj = original_context
                    # Handle both dict and object contexts
                    if isinstance(config_obj, dict) and 'thresholds' in config_obj:
                        thresholds = config_obj['thresholds']
                        if isinstance(thresholds, dict) and simple_name in thresholds:
                            value = thresholds[simple_name]
                            found = True
                    elif hasattr(config_obj, 'thresholds'):
                        thresholds = config_obj.thresholds
                        # ThresholdConfig is a dict subclass, so check dict access first
                        if isinstance(thresholds, dict) and simple_name in thresholds:
                            value = thresholds[simple_name]
                            found = True
                        elif hasattr(thresholds, simple_name):
                            value = getattr(thresholds, simple_name)
                            found = True
            
            if not found:
                # Variable not found, keep original placeholder
                return match.group(0)
            
            # Format numbers nicely
            if isinstance(value, float):
                if value >= 1000:
                    return f"{round(value):,}"
                # For smaller values, preserve one decimal if fractional
                if value != int(value):
                    return f"{value:.1f}"
                return str(int(value))
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
        self.env.globals['get_theme_css'] = get_theme_css  # Use unified ThemeSystem
        
        def get_image_src(image_name: str, images_dir_rel: str = "", image_data_uris: Optional[dict] = None) -> str:
            """
            Get image source - either base64 data URI or relative file path.
            
            Parameters:
                image_name: Name of the image file
                images_dir_rel: Relative path to images directory (if not embedding)
                image_data_uris: Dict of base64 data URIs (if embedding)
            
            Returns:
                Image src string (base64 URI or file path)
            """
            if image_data_uris and image_name in image_data_uris:
                return image_data_uris[image_name]
            if images_dir_rel:
                return f"{images_dir_rel}/{image_name}".replace('\\', '/')
            return image_name
        
        self.env.globals['get_image_src'] = get_image_src
        
        # Render component - access components via extension point
        def render_component(component_id: str, props: Optional[Dict[str, Any]] = None, **kwargs) -> 'Markup':
            """
            Render a plugin-defined UI component.
            
            Usage in templates:
                {{ render_component('stat_card', {'title': 'Total', 'value': 42}) }}
                {{ render_component('gauge', value=85, max=100) }}
            
            Parameters:
                component_id: Component type ID (e.g., 'stat_card', 'gauge')
                props: Dictionary of component properties
                **kwargs: Additional properties (merged with props)
            
            Returns:
                Rendered HTML (Markup-safe)
            """
            from markupsafe import Markup
            
            # Merge props with kwargs
            all_props = dict(props or {})
            all_props.update(kwargs)
            
            # Get registry via extension point
            extension_point = get_extension_point()
            registry = extension_point.get_registry()
            
            # Render the component
            html = registry.components.render(component_id, all_props, {})
            return Markup(html)
        
        self.env.globals['render_component'] = render_component
    
    def render(
        self, 
        template_name: str, 
        context: Dict[str, Any],
        labels: Optional["Labels"] = None
    ) -> str:
        """
        Render a template with the given context.
        
        Parameters:
            template_name: Name of the template file (e.g., 'pages/homepage.html.j2')
            context: Dictionary of template variables (not mutated)
            labels: Optional Labels for UI text
        
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
        labels: Optional["Labels"] = None
    ) -> str:
        """
        Render an inline template string.
        
        Parameters:
            template_string: Raw Jinja2 template string
            context: Dictionary of template variables (not mutated)
            labels: Optional Labels for UI text
        
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

"""
Python file generators for plugin scaffolding.

Generates source code for plugin components:
- plugin.py (main plugin class)
- csv_parser.py (data parser)
- context_builder.py (template context)
- chart_generator.py (Chart.js generation)
- analysis.py (statistical analysis)
"""


def generate_plugin_py(name: str, safe_name: str, class_name: str, template: str) -> str:
    """Generate the main plugin.py file."""
    
    if template == 'full':
        imports = f"""from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper
from .parsers.csv_parser import {class_name}CsvParser"""

        
        registration = f'''        # Load report system definition
        import json
        report_system_path = Path(__file__).parent / "report_systems" / "{safe_name}.json"
        with open(report_system_path) as f:
            system_def = json.load(f)
        
        # Register core components
        helper.setup_complete_report_system(
            system_id="{safe_name}",
            system_def=system_def,
            parser_class={class_name}CsvParser,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # NOTE: Themes are defined in theme.py and used directly by templates.
        # No core registration needed - themes are fully plugin-owned.'''

    else:
        imports = f"""from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper
from .parsers.csv_parser import {class_name}CsvParser
from .analysis import analyze_{safe_name}_data"""
        
        registration = f'''        # Load report system definition
        import json
        report_system_path = Path(__file__).parent / "report_systems" / "{safe_name}.json"
        with open(report_system_path) as f:
            system_def = json.load(f)
        
        # Register core components
        helper.setup_complete_report_system(
            system_id="{safe_name}",
            system_def=system_def,
            parser_class={class_name}CsvParser,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # NOTE: Pages are user-defined in report_config.yaml, not here.'''
    
    return f'''"""
{name} Plugin - Main plugin class.
"""

{imports}


class {class_name}Plugin(BasePlugin):
    """
    Plugin for analyzing {name} data.
    """
    
    name = "{name}"
    version = "1.0.0"
    author = "Your Name"
    description = "Plugin for {name} analysis"

    def on_load(self, registry) -> None:
        """Register all plugin components using PluginHelper."""
        helper = PluginHelper(registry, self.name)
        
{registration}
    
    def on_report_start(self, context: dict) -> None:
        """Called when report generation begins."""
        pass
    
    def on_report_complete(self, result: dict) -> None:
        """Called when report generation completes."""
        pass
'''


def generate_csv_parser(name: str, class_name: str) -> str:
    """Generate CSV parser file that reads from data_schema.yaml."""
    return f'''"""
CSV Parser for {name} Plugin.

Schema-Driven Parsing:
- Reads field definitions from data_schema.yaml
- Supports string, number, date, category types
- No code changes needed to parse different CSV formats

Data Flow:
    data_schema.yaml → Parser → CSV files → List[Dict]
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import csv
import yaml


def load_schema(plugin_dir: Path) -> Dict[str, Any]:
    """Load data schema from YAML file."""
    schema_path = plugin_dir / 'data_schema.yaml'
    if not schema_path.exists():
        # Fallback to default schema
        return {{
            'fields': [
                {{'name': 'name', 'type': 'string', 'required': True}},
                {{'name': 'score', 'type': 'number', 'required': True}},
                {{'name': 'category', 'type': 'category', 'required': False, 'default': 'General'}},
            ]
        }}
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {{'fields': []}}


def convert_value(value: str, field_def: Dict[str, Any]) -> Any:
    """Convert string value to appropriate type based on schema."""
    if not value or not value.strip():
        return field_def.get('default')
    
    value = value.strip()
    field_type = field_def.get('type', 'string')
    
    try:
        if field_type == 'number':
            # Try int first, then float
            if '.' in value:
                return float(value)
            return int(value)
        
        elif field_type == 'date':
            fmt = field_def.get('format', '%Y-%m-%d')
            return datetime.strptime(value, fmt).isoformat()
        
        elif field_type in ('string', 'category'):
            return value
        
        else:
            return value
            
    except (ValueError, TypeError):
        return field_def.get('default')


class {class_name}CsvParser:
    """
    Schema-driven CSV parser.
    
    Reads field definitions from data_schema.yaml and parses any CSV format.
    Edit data_schema.yaml to change what columns are parsed - no code changes needed.
    """
    
    def __init__(self):
        self._schema = None
        self._plugin_dir = Path(__file__).parent.parent
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Lazy-load schema."""
        if self._schema is None:
            self._schema = load_schema(self._plugin_dir)
        return self._schema
    
    @property
    def fields(self) -> List[Dict[str, Any]]:
        """Get field definitions."""
        return self.schema.get('fields', [])
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single CSV file (not used for multi-row CSVs)."""
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Find all CSV files in the directory."""
        return sorted(directory.glob("*.csv"))
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all CSV files and return combined records."""
        data_points = []
        errors = []
        
        for csv_file in self.discover_files(directory):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                        data_point = self._parse_row(row, csv_file.name, row_num)
                        if data_point:
                            data_points.append(data_point)
            except (OSError, csv.Error) as e:
                errors.append(f"{{csv_file.name}}: {{e}}")
                continue
        
        if errors:
            print(f"Warning: {{len(errors)}} file(s) had errors")
        
        return data_points
    
    def _parse_row(self, row: Dict[str, str], source_file: str, row_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row based on schema."""
        result = {{'_source': source_file, '_row': row_num}}
        
        for field_def in self.fields:
            field_name = field_def.get('name')
            if not field_name:
                continue
            
            raw_value = row.get(field_name, '')
            converted = convert_value(raw_value, field_def)
            
            # Check required fields
            if field_def.get('required') and converted is None:
                return None  # Skip row if required field is missing
            
            result[field_name] = converted
        
        return result
'''


def generate_context_builder(name: str, class_name: str) -> str:
    """Generate context builder file."""
    return f'''"""
Context Builder for {name} Plugin.
"""

from typing import Dict, List, Any, Union


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """
    Convert DataFrame or other iterable to List[Dict].
    
    Uses duck-typing to detect DataFrame-like objects by checking for:
    - __iter__: Iterable interface
    - column_names: Column metadata (Polars, Pandas-like)
    - rows: Row accessor (Polars, custom DataFrame implementations)
    
    Supported DataFrame libraries:
    - Polars: Has column_names and rows attributes
    - Pandas-like: Typically has column_names or columns attribute
    - Custom DataFrame implementations matching this interface
    
    Note: This pragmatic approach may match unintended objects. For stricter
    type checking, consider using isinstance() checks for known DataFrame types.
    """
    # Check if it's a DataFrame (duck-typing with multiple attributes)
    if hasattr(data, '__iter__') and hasattr(data, 'column_names') and hasattr(data, 'rows'):
        return list(data)
    elif isinstance(data, list):
        return data
    else:
        return list(data) if hasattr(data, '__iter__') and not isinstance(data, str) else []


class {class_name}ContextBuilder:
    """Build template context for {name} reports."""
    
    def build_context(
        self,
        data: Union[List[Dict[str, Any]], Any],
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enriched context for template rendering."""
        context = dict(base_context)
        
        # Convert DataFrame to list if needed
        data_points = _normalize_data_to_list(data)
        
        # Sort by score (descending)
        ranked = sorted(data_points, key=lambda x: x.get('score', 0), reverse=True)
        context['ranked_data'] = ranked
        
        # Add rankings
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        
        # Categorize by score
        scores = [d.get('score', 0) for d in data_points]
        if scores:
            context['score_range'] = {{
                'min': min(scores),
                'max': max(scores),
                'spread': max(scores) - min(scores),
            }}
        
        return context
'''



def generate_executor(name: str, safe_name: str, class_name: str) -> str:
    """Generate executor.py with YAML-driven report generation."""
    return '''"""
Report Executor for ''' + name + ''' Plugin.

YAML-Driven Report Generation:
- Reads pages from report_config.yaml
- Generates charts, stats, tables, and LLM content dynamically
- Single HTML file with tabbed pages

Usage:
    bobreview --plugin ''' + name + ''' --dir ./data --output ./output
    bobreview --plugin ''' + name + ''' --dir ./data --dry-run  # Skip LLM calls
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .theme import ''' + safe_name.upper() + '''_MIDNIGHT, ''' + safe_name.upper() + '''_AURORA, ''' + safe_name.upper() + '''_SUNSET, ''' + safe_name.upper() + '''_FROST, get_theme_css_variables, ReportTheme
from .parsers.csv_parser import ''' + class_name + '''CsvParser
from .chart_generator import ''' + class_name + '''ChartGenerator


# Theme mapping
THEMES = {
    "''' + safe_name + '''_midnight": ''' + safe_name.upper() + '''_MIDNIGHT,
    "''' + safe_name + '''_aurora": ''' + safe_name.upper() + '''_AURORA,
    "''' + safe_name + '''_sunset": ''' + safe_name.upper() + '''_SUNSET,
    "''' + safe_name + '''_frost": ''' + safe_name.upper() + '''_FROST,
    "midnight": ''' + safe_name.upper() + '''_MIDNIGHT,
    "aurora": ''' + safe_name.upper() + '''_AURORA,
    "sunset": ''' + safe_name.upper() + '''_SUNSET,
    "frost": ''' + safe_name.upper() + '''_FROST,
}


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load report_config.yaml."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def calculate_stats(data_points: List[Dict]) -> Dict[str, Any]:
    """Calculate stats for all numeric fields."""
    if not data_points:
        return {}
    
    stats = {}
    # Find all numeric fields
    for key in data_points[0].keys():
        values = [d.get(key) for d in data_points if isinstance(d.get(key), (int, float))]
        if values:
            stats[key] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values),
                'sum': sum(values),
            }
    return stats


def generate_llm_content(
    config: Dict[str, Any],
    data_points: List[Dict],
    stats: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, str]:
    """Generate LLM content for all prompts in YAML config."""
    llm_content = {}
    
    for page in config.get('pages', []):
        for comp in page.get('components', []):
            comp_type = comp.get('type', '')
            if '_llm' in comp_type:
                comp_id = comp.get('id', 'unknown')
                prompt = comp.get('prompt', '')
                
                if dry_run:
                    llm_content[comp_id] = f'<div class="llm-dry-run"><em>[LLM Placeholder: {comp.get("title", comp_id)}]</em><br><small>Prompt: {prompt[:100]}...</small></div>'
                else:
                    try:
                        # Format prompt with data context
                        data_summary = f"Data: {len(data_points)} items. Stats: {json.dumps(stats, default=str)[:500]}"
                        full_prompt = f"{prompt}\\n\\nContext:\\n{data_summary}"
                        
                        from bobreview.services.llm.client import call_llm
                        from bobreview.core.config import Config
                        from bobreview.core.cache import init_cache
                        from bobreview.core.html_utils import sanitize_llm_html
                        llm_config = Config()
                        init_cache(llm_config)
                        response = call_llm(full_prompt, config=llm_config)
                        # Convert markdown to HTML and sanitize
                        if response:
                            llm_content[comp_id] = sanitize_llm_html(response)
                        else:
                            llm_content[comp_id] = f'<em>No response for {comp_id}</em>'
                    except Exception as e:
                        llm_content[comp_id] = f'<div class="llm-error">LLM Error: {e}</div>'
    
    return llm_content


class TemplateLoader:
    """Load component templates from YAML file."""
    
    def __init__(self, plugin_dir: Path):
        self.templates_path = plugin_dir / 'component_templates.yaml'
        self._cache: Dict[str, Any] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from YAML file."""
        if not self.templates_path.exists():
            return
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                for comp_type, comp_def in data.items():
                    if isinstance(comp_def, dict) and 'template' in comp_def:
                        self._cache[comp_type] = comp_def
        except Exception as e:
            print(f"Warning: Failed to load component templates: {e}")
    
    def get(self, comp_type: str) -> Dict:
        """Get template definition for a component type."""
        return self._cache.get(comp_type, {})
    
    def has(self, comp_type: str) -> bool:
        """Check if template exists."""
        return comp_type in self._cache


class ComponentRenderer:
    """Render components using YAML templates."""
    
    def __init__(self, data_points: List[Dict], stats: Dict, llm_content: Dict,
                 charts_js: List[str], chart_gen: "''' + class_name + '''ChartGenerator",
                 theme: ReportTheme, safe_name: str, template_loader: TemplateLoader,
                 custom_components: Dict[str, Any] = None):
        self.data_points = data_points
        self.stats = stats
        self.llm_content = llm_content
        self.charts_js = charts_js
        self.chart_gen = chart_gen
        self.theme = theme
        self.safe_name = safe_name
        self.templates = template_loader
        self.custom_components = custom_components or {}
        self.count = len(data_points)
        
        # Jinja2 environment
        from jinja2 import Environment
        self.env = Environment()
        self.env.globals['len'] = len
        self.env.globals['min'] = min
        self.env.globals['max'] = max
        self.env.globals['sum'] = sum
        self.env.globals['round'] = round
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Base context for all templates."""
        return {
            'data_points': self.data_points,
            'stats': self.stats,
            'theme': self.theme,
            'count': self.count,
        }
    
    def _render_template(self, template_str: str, context: Dict) -> str:
        """Render a Jinja2 template."""
        try:
            tpl = self.env.from_string(template_str)
            return tpl.render(**context)
        except Exception as e:
            return f'<div class="error">Template error: {e}</div>'
    
    def render(self, comp: Dict) -> str:
        """Render a component to HTML."""
        comp_type = comp.get('type', '')
        
        # Check inline custom components first
        if comp_type in self.custom_components:
            return self._render_custom(comp_type, comp)
        
        # Check charts first (needs JS generation) - BEFORE YAML templates
        if '_chart' in comp_type:
            return self._render_chart(comp)
        
        # Check YAML templates
        if self.templates.has(comp_type):
            return self._render_yaml(comp_type, comp)
        
        return f'<!-- Unknown: {comp_type} -->'
    
    def _render_yaml(self, comp_type: str, comp: Dict) -> str:
        """Render using YAML template."""
        template_def = self.templates.get(comp_type)
        template_str = template_def.get('template', '')
        
        # Build context - order matters! Prepared context should override raw props
        context = self._get_base_context()
        
        # Add raw component props first
        for key, value in comp.items():
            if key != 'type':
                # Eval Jinja expressions in values
                if isinstance(value, str) and '{{' in value:
                    context[key] = eval_template(value, self.data_points, self.stats)
                else:
                    context[key] = value
        
        # Add prepared context (overwrites raw props where needed)
        context.update(self._prepare_context(comp_type, comp))
        
        return self._render_template(template_str, context)
    
    def _prepare_context(self, comp_type: str, comp: Dict) -> Dict[str, Any]:
        """Prepare component-specific context."""
        ctx = {}
        
        if '_stat_card' in comp_type:
            value_template = comp.get('value', '0')
            ctx['value'] = eval_template(value_template, self.data_points, self.stats)
            ctx['variant'] = comp.get('variant', 'default')
        
        elif '_llm' in comp_type:
            comp_id = comp.get('id', 'unknown')
            ctx['llm_content'] = self.llm_content.get(comp_id, '<em>No content</em>')
        
        elif '_data_table' in comp_type:
            columns = comp.get('columns', ['name', 'score'])
            page_size = comp.get('page_size', 10)
            ctx['columns'] = columns
            ctx['table_rows'] = self.data_points[:page_size]
        
        return ctx
    
    def _render_chart(self, comp: Dict) -> str:
        """Render chart component (needs JS)."""
        chart_id = comp.get('id', f'chart_{len(self.charts_js)}')
        chart_type = comp.get('chart', 'bar')
        title = comp.get('title', 'Chart')
        
        chart_config = {
            'id': chart_id,
            'type': chart_type,
            'title': title,
            'x_field': comp.get('x', 'name'),
            'y_field': comp.get('y', 'score'),
        }
        js = self.chart_gen.generate_chart(self.data_points, self.stats, None, chart_config, self.theme)
        self.charts_js.append(js)
        
        # Use template if available
        comp_type = f'{self.safe_name}_chart'
        if self.templates.has(comp_type):
            template_def = self.templates.get(comp_type)
            context = self._get_base_context()
            context['chart_id'] = chart_id
            context['title'] = title
            return self._render_template(template_def.get('template', ''), context)
        
        return f'<div class="chart-card"><h3>{title}</h3><div class="chart-container"><canvas id="{chart_id}"></canvas></div></div>'
    
    def _render_custom(self, comp_type: str, comp: Dict) -> str:
        """Render inline custom component."""
        custom_def = self.custom_components[comp_type]
        template_str = custom_def.get('template', '')
        if not template_str:
            return f'<!-- {comp_type} has no template -->'
        
        context = self._get_base_context()
        for key, value in comp.items():
            if key != 'type':
                if isinstance(value, str) and '{{' in value:
                    context[key] = eval_template(value, self.data_points, self.stats)
                else:
                    context[key] = value
        
        html = self._render_template(template_str, context)
        css = custom_def.get('css', '')
        if css:
            html = f'<style>{css}</style>\\n{html}'
        return html


def eval_template(template: str, data_points: List[Dict], stats: Dict[str, Any]) -> str:
    """
    Render template using Jinja2 for full expression support.
    
    Supports all Jinja2 features:
    - Filters: {{ value | round(2) }}, {{ items | sum(attribute='score') }}
    - Conditionals: {{ 'Good' if score > 80 else 'Needs work' }}
    - Math: {{ stats.score.mean * 100 }}%
    - List operations: {{ data_points | length }}, {{ data_points | first }}
    
    Context variables available:
    - data_points: List of all data records
    - stats: Dictionary of statistics per field
    - len: Python's len() function
    """
    from jinja2 import Template, Environment
    
    try:
        # Create Jinja2 environment with useful globals
        env = Environment()
        env.globals['len'] = len
        env.globals['min'] = min
        env.globals['max'] = max
        env.globals['sum'] = sum
        env.globals['abs'] = abs
        env.globals['round'] = round
        
        # Prepare context
        context = {
            'data_points': data_points,
            'stats': stats,
        }
        
        # Handle template string - may or may not have {{ }}
        tmpl_str = template.strip()
        if not tmpl_str.startswith('{{'):
            # Wrap in {{ }} if not already a Jinja expression
            if '{{' not in tmpl_str:
                return tmpl_str  # Plain text, return as-is
        
        tpl = env.from_string(tmpl_str)
        result = tpl.render(**context)
        return result
        
    except Exception as e:
        # Fallback: return template as-is if rendering fails
        return template.replace('{{', '').replace('}}', '').strip()


def generate_report(
    data_dir: str,
    output_dir: str,
    config_path: Optional[str] = None,
    theme_id: Optional[str] = None,
    dry_run: bool = False
) -> Path:
    """
    Generate an HTML report from data files using YAML configuration.
    
    Parameters:
        data_dir: Directory containing data files
        output_dir: Directory to write HTML output
        config_path: Path to report_config.yaml (defaults to plugin dir)
        theme_id: Theme ID to use (defaults to config's theme setting)
        dry_run: If True, skip LLM calls
    
    Returns:
        Path to the generated index.html
    """
    import html
    plugin_dir = Path(__file__).parent
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load config
    if config_path:
        config = load_config(Path(config_path))
    else:
        config = load_config(plugin_dir / 'report_config.yaml')
    
    # Get theme
    theme = THEMES.get(theme_id) or THEMES.get(config.get('theme', 'midnight')) or ''' + safe_name.upper() + '''_MIDNIGHT
    theme_css = get_theme_css_variables(theme)
    font_link = f'<link href="{theme.font_url}" rel="stylesheet">' if theme.font_url else ''
    
    # Parse data
    parser = ''' + class_name + '''CsvParser()
    data_points = parser.parse_directory(data_path)
    
    if not data_points:
        raise ValueError(f"No data found in {data_dir}")
    
    # Calculate stats
    stats = calculate_stats(data_points)
    
    # Generate LLM content
    llm_content = generate_llm_content(config, data_points, stats, dry_run)
    
    # Initialize chart generator and template loader
    chart_gen = ''' + class_name + '''ChartGenerator()
    charts_js = []
    template_loader = TemplateLoader(plugin_dir)
    
    # Get custom components from config (if any)
    custom_components = config.get('custom_components', {})
    
    # Create component renderer
    renderer = ComponentRenderer(
        data_points, stats, llm_content, charts_js, chart_gen,
        theme, "''' + safe_name + '''", template_loader, custom_components
    )
    
    # Render pages
    pages = config.get('pages', [])
    nav_html = ''
    pages_html = ''
    
    for i, page in enumerate(pages):
        page_id = page.get('id', f'page_{i}')
        page_title = page.get('title', f'Page {i+1}')
        page_title_escaped = html.escape(page_title)
        active_class = 'active' if i == 0 else ''
        
        # Navigation tab
        nav_html += f'<button class="tab-btn {active_class}" onclick="showPage(\\'{page_id}\\', event)">{page_title_escaped}</button>'
        
        # Page content
        components_html = ''
        layout = page.get('layout', 'grid')
        
        for comp in page.get('components', []):
            comp_html = renderer.render(comp)
            components_html += comp_html
        
        layout_class = {'grid': 'layout-grid', 'single-column': 'layout-single', 'flex': 'layout-flex'}.get(layout, 'layout-grid')
        pages_html += f'<div id="{page_id}" class="page-content {active_class} {layout_class}">{components_html}</div>'
    
    # Build final HTML
    report_name = config.get('name', "''' + name + ''' Report")
    report_name_escaped = html.escape(report_name)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name_escaped}</title>
    {font_link}
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
{theme_css}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ 
    font-family: var(--font-family); 
    background: linear-gradient(135deg, var(--bg) 0%, var(--bg-soft) 50%, var(--bg) 100%);
    background-attachment: fixed;
    color: var(--text-main); 
    min-height: 100vh;
    line-height: 1.6;
}}
.container {{ max-width: 1400px; margin: 0 auto; padding: 2rem 3rem; }}

/* Header - Gradient Title */
header {{ 
    text-align: center; 
    margin-bottom: 2.5rem; 
    padding: 2rem 0;
    position: relative;
}}
header::after {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 200px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}}
header h1 {{ 
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.75rem; 
    font-weight: 800;
    margin-bottom: 0.75rem;
    letter-spacing: -0.02em;
}}
header p {{ color: var(--text-soft); font-size: 1rem; }}

/* Tabs - Pill Style */
.tabs {{ 
    display: flex; 
    gap: 0.5rem; 
    margin-bottom: 2.5rem; 
    flex-wrap: wrap;
    background: var(--bg-elevated);
    padding: 0.5rem;
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-subtle);
}}
.tab-btn {{ 
    background: transparent; 
    color: var(--text-soft); 
    border: none; 
    padding: 0.75rem 1.5rem; 
    border-radius: var(--radius-md); 
    cursor: pointer; 
    font-size: 0.95rem; 
    font-weight: 500;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
}}
.tab-btn:hover {{ 
    background: var(--bg-soft); 
    color: var(--text-main);
}}
.tab-btn.active {{ 
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%); 
    color: var(--bg); 
    box-shadow: 0 4px 15px rgba(34, 211, 238, 0.3);
}}

/* Layouts - defined first so page-content can override */
.layout-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.75rem; }}
.layout-single {{ display: flex; flex-direction: column; gap: 1.75rem; }}
.layout-flex {{ display: flex; flex-wrap: wrap; gap: 1.75rem; }}

/* Pages - MUST come after layouts to override display property */
.page-content {{ display: none !important; animation: fadeIn 0.4s ease; }}
.page-content.active {{ display: block !important; }}
.page-content.active.layout-grid {{ display: grid !important; }}
.page-content.active.layout-single {{ display: flex !important; }}
.page-content.active.layout-flex {{ display: flex !important; }}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* Stats Grid */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.25rem;
    margin-bottom: 1rem;
}}

/* Stat Cards - Glass Effect */
.stat-card {{ 
    background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(30, 41, 59, 0.8) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-subtle); 
    border-radius: var(--radius-lg); 
    padding: 1.75rem; 
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}}
.stat-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent-strong));
    opacity: 0;
    transition: opacity 0.3s;
}}
.stat-card:hover {{ 
    transform: translateY(-4px); 
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    border-color: var(--accent);
}}
.stat-card:hover::before {{ opacity: 1; }}
.stat-value {{ 
    background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.75rem; 
    font-weight: 800;
    line-height: 1;
}}
.stat-label {{ 
    color: var(--text-soft); 
    font-size: 0.8rem; 
    text-transform: uppercase; 
    letter-spacing: 0.1em;
    margin-top: 0.75rem;
    font-weight: 500;
}}
.stat-ok {{ border-left: 4px solid var(--ok); }}
.stat-ok .stat-value {{ background: linear-gradient(135deg, var(--ok), #22c55e); -webkit-background-clip: text; }}
.stat-warn {{ border-left: 4px solid var(--warn); }}
.stat-warn .stat-value {{ background: linear-gradient(135deg, var(--warn), #fbbf24); -webkit-background-clip: text; }}
.stat-danger {{ border-left: 4px solid var(--danger); }}
.stat-danger .stat-value {{ background: linear-gradient(135deg, var(--danger), #ef4444); -webkit-background-clip: text; }}
.stat-info {{ border-left: 4px solid var(--accent); }}

/* Charts - Frosted Glass */
.chart-card {{ 
    background: linear-gradient(180deg, var(--bg-elevated) 0%, rgba(17, 24, 39, 0.95) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-subtle); 
    border-radius: var(--radius-lg); 
    padding: 1.75rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
.chart-card:hover {{
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    border-color: rgba(34, 211, 238, 0.3);
}}
.chart-card h3 {{ 
    color: var(--text-main); 
    font-size: 1.15rem; 
    font-weight: 600;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.chart-card h3::before {{
    content: '';
    width: 4px;
    height: 1.2em;
    background: var(--accent);
    border-radius: 2px;
}}
.chart-container {{ position: relative; height: 300px; }}

/* LLM Content - Premium Card */
.llm-section {{ 
    background: linear-gradient(135deg, var(--bg-elevated) 0%, rgba(30, 41, 59, 0.9) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-subtle); 
    border-radius: var(--radius-lg); 
    padding: 2rem;
    grid-column: 1 / -1;
    position: relative;
    overflow: hidden;
}}
.llm-section::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, var(--accent), var(--accent-strong));
}}
.llm-section h3 {{ 
    color: var(--accent); 
    font-size: 1.2rem; 
    font-weight: 600;
    margin-bottom: 1.25rem;
}}
.llm-content {{ color: var(--text-main); line-height: 1.8; }}
.llm-content p {{ margin-bottom: 1rem; }}
.llm-content ul, .llm-content ol {{ margin: 1rem 0; padding-left: 1.5rem; }}
.llm-content strong {{ color: var(--accent-strong); }}
.llm-dry-run {{ 
    color: var(--text-soft); 
    font-style: italic; 
    padding: 1.25rem; 
    background: linear-gradient(135deg, var(--bg-soft), rgba(30, 41, 59, 0.5));
    border-radius: var(--radius-md);
    border-left: 3px solid var(--accent);
}}
.llm-error {{ color: var(--danger); padding: 1rem; background: var(--danger-soft); border-radius: var(--radius-md); }}

/* Tables - Clean Design */
.table-section {{ 
    background: var(--bg-elevated); 
    border: 1px solid var(--border-subtle); 
    border-radius: var(--radius-lg); 
    padding: 1.75rem; 
    grid-column: 1 / -1; 
    overflow-x: auto;
}}
.table-section h3 {{ 
    color: var(--accent); 
    font-size: 1.15rem; 
    font-weight: 600;
    margin-bottom: 1.25rem;
}}
.data-table {{ width: 100%; border-collapse: collapse; }}
.data-table th {{ 
    background: linear-gradient(180deg, var(--bg-soft), var(--bg-elevated));
    color: var(--accent); 
    text-align: left; 
    padding: 1rem 1.25rem; 
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.data-table td {{ padding: 1rem 1.25rem; border-bottom: 1px solid var(--border-subtle); }}
.data-table tr:hover {{ background: rgba(34, 211, 238, 0.05); }}
.table-info {{ color: var(--text-soft); font-size: 0.85rem; margin-top: 1rem; }}

@media (max-width: 768px) {{
    .layout-grid {{ grid-template-columns: 1fr; }}
    .tabs {{ flex-direction: column; }}
    .container {{ padding: 1rem; }}
    header h1 {{ font-size: 2rem; }}
}}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{report_name_escaped}</h1>
            <p>Theme: {theme.name} | {len(data_points)} items</p>
        </header>
        <nav class="tabs">{nav_html}</nav>
        {pages_html}
    </div>
    <script>
function showPage(pageId, event) {{
    document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    if (event && event.target) {{
        event.target.classList.add('active');
    }}
}}
{''.join(charts_js)}
    </script>
</body>
</html>"""
    
    # Write output
    output_file = output_path / 'index.html'
    output_file.write_text(html, encoding='utf-8')
    
    mode_str = " (dry-run)" if dry_run else ""
    print(f"✓ Report generated{mode_str}: {output_file}")
    print(f"  Pages: {len(pages)}")
    print(f"  Data points: {len(data_points)}")
    print(f"  LLM sections: {len(llm_content)}")
    
    return output_file
'''


def generate_chart_generator(name: str, class_name: str) -> str:
    """Generate chart generator file with theme support."""
    return '''"""
Chart Generator for ''' + name + ''' Plugin.

Generates Chart.js JavaScript code with theme-aware coloring.
"""

import json
from typing import Dict, List, Any, Union
from .theme import ReportTheme


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """Convert DataFrame or other iterable to List[Dict]."""
    if hasattr(data, '__iter__') and hasattr(data, 'column_names') and hasattr(data, 'rows'):
        return list(data)
    elif isinstance(data, list):
        return data
    else:
        return list(data) if hasattr(data, '__iter__') and not isinstance(data, str) else []


class ''' + class_name + '''ChartGenerator:
    """Generate Chart.js JavaScript code with theme support."""
    
    def generate_chart(
        self,
        data: Union[List[Dict[str, Any]], Any],  # DataFrame or List[Dict]
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any],
        theme: ReportTheme = None
    ) -> str:
        """
        Generate Chart.js JavaScript code.
        
        Parameters:
            data: Data points
            stats: Statistics dict
            config: Report config
            chart_config: Chart configuration
            theme: Theme object (required)
        
        Returns JavaScript code that creates the chart, NOT JSON config.
        """
        # Convert DataFrame to list if needed
        data_points = _normalize_data_to_list(data)
        
        chart_id = chart_config.get('id', 'chart')
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'score')
        x_field = chart_config.get('x_field', 'name')
        
        # Use provided theme or create default
        if not theme:
            theme = ReportTheme(id='default', name='Default')
        
        # Build data
        sorted_data = sorted(data_points, key=lambda x: x.get(y_field, 0), reverse=True)[:20]
        labels = [d.get(x_field, d.get('name', f'#{i}')) for i, d in enumerate(sorted_data)]
        values = [d.get(y_field, 0) for d in sorted_data]
        
        # Theme colors
        accent = self._hex_to_rgba(theme.accent, 0.8)
        accent_border = theme.accent
        text_soft = theme.text_soft
        text_main = theme.text_main
        grid = self._hex_to_rgba(theme.text_soft, 0.15)
        bg = self._hex_to_rgba(theme.bg, 0.94)
        
        if chart_type == 'histogram':
            return self._generate_histogram(chart_id, title, values, y_field, theme)
        
        if chart_type in ('pie', 'doughnut'):
            return self._generate_pie_chart(chart_id, title, labels, values, chart_type, theme)
        
        if chart_type == 'line':
            return self._generate_line_chart(chart_id, title, labels, values, theme)
        
        # Default: Bar chart
        js_code = f"""
// {title} Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: '{chart_type}',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: {json.dumps(title)},
                data: {json.dumps(values)},
                backgroundColor: '{accent}',
                borderColor: '{accent_border}',
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ labels: {{ color: '{text_soft}' }} }},
                tooltip: {{
                    backgroundColor: '{bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{accent_border}',
                    borderWidth: 1
                }}
            }},
            scales: {{
                x: {{ 
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }} 
                }},
                y: {{ 
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }},
                    beginAtZero: true
                }}
            }}
        }}
    }});
}})();
"""
        return js_code
    
    def _generate_line_chart(self, chart_id: str, title: str, labels: List[str], values: List[float], theme) -> str:
        """Generate line chart with gradient fill."""
        accent = theme.accent
        text_soft = theme.text_soft
        text_main = theme.text_main
        grid = self._hex_to_rgba(theme.text_soft, 0.15)
        bg = self._hex_to_rgba(theme.bg, 0.94)
        
        return f"""
// {title} Line Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{self._hex_to_rgba(theme.accent, 0.4)}');
    gradient.addColorStop(1, '{self._hex_to_rgba(theme.accent, 0.0)}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: {json.dumps(title)},
                data: {json.dumps(values)},
                borderColor: '{accent}',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '{accent}',
                pointBorderColor: '{text_main}'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ labels: {{ color: '{text_soft}' }} }},
                tooltip: {{
                    backgroundColor: '{bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{accent}',
                    borderWidth: 1
                }}
            }},
            scales: {{
                x: {{ ticks: {{ color: '{text_soft}' }}, grid: {{ color: '{grid}' }} }},
                y: {{ ticks: {{ color: '{text_soft}' }}, grid: {{ color: '{grid}' }}, beginAtZero: true }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_pie_chart(self, chart_id: str, title: str, labels: List[str], values: List[float], chart_type: str, theme) -> str:
        """Generate pie or doughnut chart with theme colors."""
        text_soft = theme.text_soft
        text_main = theme.text_main
        bg = self._hex_to_rgba(theme.bg, 0.94)
        
        # Generate color palette based on theme
        colors = [
            theme.accent,
            getattr(theme, 'ok', '#22c55e'),
            getattr(theme, 'warn', '#eab308'),
            getattr(theme, 'danger', '#ef4444'),
            self._hex_to_rgba(theme.accent, 0.6),
            self._hex_to_rgba(getattr(theme, 'ok', '#22c55e'), 0.6),
        ]
        
        # Extend colors if needed
        while len(colors) < len(values):
            colors.extend(colors)
        colors = colors[:len(values)]
        
        return f"""
// {title} {chart_type.title()} Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: '{chart_type}',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                data: {json.dumps(values)},
                backgroundColor: {json.dumps(colors)},
                borderColor: '{theme.bg}',
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ 
                    position: 'right',
                    labels: {{ color: '{text_soft}', padding: 15 }} 
                }},
                tooltip: {{
                    backgroundColor: '{bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1
                }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_histogram(self, chart_id: str, title: str, values: List[float], field: str, theme) -> str:
        """Generate histogram chart."""
        if not values:
            return f"// {title}: No data"
        
        min_val = min(values)
        max_val = max(values)
        num_bins = min(10, max(len(set(values)), 2))
        bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1
        
        bins = [0] * num_bins
        labels = []
        
        for v in values:
            idx = min(int((v - min_val) / bin_width), num_bins - 1)
            bins[idx] += 1
        
        for i in range(num_bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            labels.append(f"{int(bin_start)}-{int(bin_end)}")
        
        accent = self._hex_to_rgba(theme.accent, 0.75)
        accent_border = theme.accent
        text_soft = theme.text_soft
        text_main = theme.text_main
        grid = self._hex_to_rgba(theme.text_soft, 0.15)
        
        js_code = f"""
// {title} Histogram
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: 'Frequency',
                data: {json.dumps(bins)},
                backgroundColor: '{accent}',
                borderColor: '{accent_border}',
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ display: false }}
            }},
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(field.title())}, color: '{text_soft}' }},
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }} 
                }},
                y: {{ 
                    title: {{ display: true, text: 'Frequency', color: '{text_soft}' }},
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }},
                    beginAtZero: true
                }}
            }}
        }}
    }});
}})();
"""
        return js_code
    
    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        \"\"\"Convert hex color to rgba string.\"\"\"
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be between 0.0 and 1.0, got {alpha}")
        
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color '{hex_color}': expected 3 or 6 hex digits")
        if any(c not in "0123456789abcdefABCDEF" for c in hex_color):
            raise ValueError(f"Invalid hex color '{hex_color}': contains non-hex characters")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
'''


def generate_analysis_module(name: str, safe_name: str) -> str:
    """Generate analysis module with statistical functions."""
    return f'''"""
Statistical Analysis for {name} Plugin.

Provides common statistical functions for data analysis.
Register with: helper.add_analyzer('{safe_name}', analyze_{safe_name}_data)
"""

from typing import List, Dict, Any
import statistics


def analyze_{safe_name}_data(
    data_points: List[Dict[str, Any]],
    config: Any = None,
    **kwargs  # Accept metrics, metric_config from AnalyticsService
) -> Dict[str, Any]:
    """
    Compute statistics from parsed data.
    
    Parameters:
        data_points: List of parsed data points with 'score' field
        config: Optional Config
        **kwargs: Additional args from AnalyticsService (metrics, metric_config)
    
    Returns:
        Dict with computed statistics
    """
    if not data_points:
        return {{'count': 0}}
    
    scores = [p.get('score', 0) for p in data_points]
    sorted_scores = sorted(scores)
    n = len(scores)
    
    def percentile(data: List[float], p: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        idx = int(len(data) * p / 100)
        return data[min(idx, len(data) - 1)]
    
    return {{
        'count': n,
        'score': {{
            'min': min(scores),
            'max': max(scores),
            'mean': statistics.mean(scores),
            'median': statistics.median(scores),
            'stdev': statistics.stdev(scores) if n > 1 else 0,
            'variance': statistics.variance(scores) if n > 1 else 0,
            'q1': percentile(sorted_scores, 25),
            'q3': percentile(sorted_scores, 75),
            'p90': percentile(sorted_scores, 90),
            'p95': percentile(sorted_scores, 95),
            'iqr': percentile(sorted_scores, 75) - percentile(sorted_scores, 25),
        }},
        # Categorized data for templates
        'high_performers': [p for p in data_points if p.get('score', 0) >= percentile(sorted_scores, 75)],
        'low_performers': [p for p in data_points if p.get('score', 0) <= percentile(sorted_scores, 25)],
        'median_performers': [p for p in data_points 
                              if percentile(sorted_scores, 25) < p.get('score', 0) < percentile(sorted_scores, 75)],
    }}
'''


def generate_theme_module(name: str, safe_name: str, class_name: str) -> str:
    """
    Generate theme.py with premium, production-ready themes.
    
    Includes 4 stunning themes:
    - MIDNIGHT: Deep blue with electric cyan accents
    - AURORA: Purple/magenta with northern lights feel
    - SUNSET: Warm amber/orange gradients
    - FROST: Clean icy light theme
    """
    return f'''"""
Premium Themes for {name} Plugin.

Four stunning themes with unique personalities:

1. MIDNIGHT - Deep blue with electric cyan accents (default)
2. AURORA - Purple/magenta with northern lights glow
3. SUNSET - Warm amber and orange gradients
4. FROST - Clean, icy light theme

Themes are fully self-contained - no core imports needed.
"""

from dataclasses import dataclass


def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """
    Convert hex color to rgba string.
    
    Parameters:
        hex_color: Hex color like '#ff6b35'
        alpha: Transparency value 0.0 to 1.0
    
    Returns:
        RGBA string like 'rgba(255, 107, 53, 0.15)'
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({{r}}, {{g}}, {{b}}, {{alpha}})'
    except (ValueError, IndexError):
        # Invalid color, using gray fallback
        # In non-production contexts, consider logging the error or raising it
        # for better debugging: raise ValueError(f"Invalid hex color: {{hex_color}}")
        return f'rgba(128, 128, 128, {{alpha}})'


@dataclass
class ReportTheme:
    """
    Theme definition for plugin reports.
    
    All themes are standalone - define every value explicitly.
    """
    id: str
    name: str
    
    # Backgrounds
    bg: str = '#070b10'
    bg_elevated: str = '#0e141b'
    bg_soft: str = '#151c26'
    
    # Accents
    accent: str = '#4ea1ff'
    accent_soft: str = 'rgba(78, 161, 255, 0.15)'
    accent_strong: str = '#ffb347'
    
    # Text
    text_main: str = '#f5f7fb'
    text_soft: str = '#a8b3c5'
    
    # Status colors
    danger: str = '#ff5c5c'
    danger_soft: str = 'rgba(255, 92, 92, 0.15)'
    warn: str = '#e6b35c'
    warn_soft: str = 'rgba(230, 179, 92, 0.15)'
    ok: str = '#4fd18b'
    ok_soft: str = 'rgba(79, 209, 139, 0.15)'
    
    # Borders and effects
    border_subtle: str = '#1e2835'
    shadow_soft: str = '0 18px 45px rgba(0, 0, 0, 0.55)'
    shadow_strong: str = '0 8px 32px rgba(0, 0, 0, 0.4)'
    radius_sm: str = '4px'
    radius_md: str = '8px'
    radius_lg: str = '12px'
    radius_xl: str = '16px'
    
    # Fonts
    font_mono: str = '"SF Mono", Menlo, Consolas, monospace'
    font_family: str = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    font_url: str = ''
    
    # Chart styling
    chart_grid_opacity: float = 0.5


def get_theme_css_variables(theme: ReportTheme) -> str:
    """Generate CSS :root block with theme variables."""
    return f""":root {{{{
  /* Backgrounds */
  --bg: {{theme.bg}};
  --bg-elevated: {{theme.bg_elevated}};
  --bg-soft: {{theme.bg_soft}};
  
  /* Accents */
  --accent: {{theme.accent}};
  --accent-soft: {{theme.accent_soft}};
  --accent-strong: {{theme.accent_strong}};
  
  /* Text */
  --text-main: {{theme.text_main}};
  --text-soft: {{theme.text_soft}};
  
  /* Status Colors */
  --ok: {{theme.ok}};
  --ok-soft: {{theme.ok_soft}};
  --warn: {{theme.warn}};
  --warn-soft: {{theme.warn_soft}};
  --danger: {{theme.danger}};
  --danger-soft: {{theme.danger_soft}};
  
  /* Borders & Effects */
  --border-subtle: {{theme.border_subtle}};
  --shadow-soft: {{theme.shadow_soft}};
  --shadow-strong: {{theme.shadow_strong}};
  
  /* Border Radius */
  --radius-sm: {{theme.radius_sm}};
  --radius-md: {{theme.radius_md}};
  --radius-lg: {{theme.radius_lg}};
  --radius-xl: {{theme.radius_xl}};
  
  /* Fonts */
  --font-family: {{theme.font_family}};
  --font-mono: {{theme.font_mono}};
}}}}"""


# =============================================================================
# 🌙 MIDNIGHT THEME - Deep blue with electric cyan
# =============================================================================
# Perfect for: Technical reports, developer dashboards, code analysis
# Font: JetBrains Mono + Inter - clean, technical, highly readable

{safe_name.upper()}_MIDNIGHT = ReportTheme(
    id='{safe_name}_midnight',
    name='{class_name} Midnight',
    
    # Deep blue-black backgrounds
    bg='#0a0f1a',
    bg_elevated='#111827',
    bg_soft='#1e293b',
    
    # Electric cyan accents
    accent='#22d3ee',
    accent_soft=hex_to_rgba('#22d3ee', 0.15),
    accent_strong='#67e8f9',
    
    # Cool gray text
    text_main='#f1f5f9',
    text_soft='#94a3b8',
    
    # Vibrant status colors
    ok='#4ade80',
    ok_soft=hex_to_rgba('#4ade80', 0.15),
    warn='#facc15',
    warn_soft=hex_to_rgba('#facc15', 0.15),
    danger='#f87171',
    danger_soft=hex_to_rgba('#f87171', 0.15),
    
    # Sharp edges for technical feel
    border_subtle='#334155',
    shadow_soft='0 8px 32px rgba(0, 0, 0, 0.5)',
    shadow_strong='0 20px 60px rgba(0, 0, 0, 0.7)',
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='16px',
    
    # JetBrains Mono + Inter - technical, clean
    font_family='"Inter", "SF Pro Display", system-ui, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", "SF Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# 🌌 AURORA THEME - Purple/magenta with northern lights glow
# =============================================================================
# Perfect for: Creative projects, marketing reports, analytics dashboards
# Font: Space Grotesk + IBM Plex Mono - modern, geometric, stylish

{safe_name.upper()}_AURORA = ReportTheme(
    id='{safe_name}_aurora',
    name='{class_name} Aurora',
    
    # Deep purple-black backgrounds
    bg='#0c0a1d',
    bg_elevated='#13102a',
    bg_soft='#1e1839',
    
    # Vibrant magenta/pink accents
    accent='#e879f9',
    accent_soft=hex_to_rgba('#e879f9', 0.18),
    accent_strong='#f0abfc',
    
    # Soft lavender text
    text_main='#f5f3ff',
    text_soft='#a5b4fc',
    
    # Colorful neon status colors
    ok='#34d399',
    ok_soft=hex_to_rgba('#34d399', 0.15),
    warn='#fcd34d',
    warn_soft=hex_to_rgba('#fcd34d', 0.15),
    danger='#fb7185',
    danger_soft=hex_to_rgba('#fb7185', 0.15),
    
    # Soft glow effects
    border_subtle='#312e54',
    shadow_soft='0 10px 40px rgba(139, 92, 246, 0.2)',
    shadow_strong='0 25px 80px rgba(139, 92, 246, 0.35)',
    radius_sm='6px',
    radius_md='12px',
    radius_lg='18px',
    radius_xl='24px',
    
    # Space Grotesk + IBM Plex Mono - modern, geometric
    font_family='"Space Grotesk", "Outfit", system-ui, sans-serif',
    font_mono='"IBM Plex Mono", "Source Code Pro", monospace',
    font_url='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap',
    
    chart_grid_opacity=0.3,
)


# =============================================================================
# 🌅 SUNSET THEME - Warm amber and orange gradients
# =============================================================================
# Perfect for: Business reports, executive dashboards, warm presentations
# Font: DM Sans + JetBrains Mono - friendly, professional, approachable

{safe_name.upper()}_SUNSET = ReportTheme(
    id='{safe_name}_sunset',
    name='{class_name} Sunset',
    
    # Warm dark backgrounds with red undertones
    bg='#120c0c',
    bg_elevated='#1a1212',
    bg_soft='#271a1a',
    
    # Warm amber/orange accents
    accent='#fb923c',
    accent_soft=hex_to_rgba('#fb923c', 0.18),
    accent_strong='#fdba74',
    
    # Warm cream text
    text_main='#fef3e2',
    text_soft='#d4a574',
    
    # Fire-inspired status colors
    ok='#86efac',
    ok_soft=hex_to_rgba('#86efac', 0.15),
    warn='#fde047',
    warn_soft=hex_to_rgba('#fde047', 0.15),
    danger='#fca5a5',
    danger_soft=hex_to_rgba('#fca5a5', 0.15),
    
    # Warm, cozy effects
    border_subtle='#3d2a2a',
    shadow_soft='0 12px 40px rgba(251, 146, 60, 0.15)',
    shadow_strong='0 24px 70px rgba(251, 146, 60, 0.25)',
    radius_sm='6px',
    radius_md='10px',
    radius_lg='16px',
    radius_xl='24px',
    
    # DM Sans + JetBrains Mono - friendly, readable
    font_family='"DM Sans", "Nunito", "Poppins", system-ui, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", monospace',
    font_url='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# ❄️ FROST THEME - Clean, icy light theme
# =============================================================================
# Perfect for: Print-friendly reports, light mode preference, formal docs
# Font: Plus Jakarta Sans + Fira Code - elegant, modern, professional

{safe_name.upper()}_FROST = ReportTheme(
    id='{safe_name}_frost',
    name='{class_name} Frost',
    
    # Clean icy backgrounds
    bg='#f0f9ff',
    bg_elevated='#ffffff',
    bg_soft='#e0f2fe',
    
    # Cool blue accent
    accent='#0284c7',
    accent_soft=hex_to_rgba('#0284c7', 0.12),
    accent_strong='#0ea5e9',
    
    # Dark slate text
    text_main='#0f172a',
    text_soft='#475569',
    
    # Clear, vivid status
    ok='#16a34a',
    ok_soft=hex_to_rgba('#16a34a', 0.1),
    warn='#d97706',
    warn_soft=hex_to_rgba('#d97706', 0.1),
    danger='#dc2626',
    danger_soft=hex_to_rgba('#dc2626', 0.1),
    
    # Subtle, clean effects
    border_subtle='#bae6fd',
    shadow_soft='0 4px 20px rgba(14, 165, 233, 0.08)',
    shadow_strong='0 12px 40px rgba(14, 165, 233, 0.15)',
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='20px',
    
    # Plus Jakarta Sans + Fira Code - elegant, modern
    font_family='"Plus Jakarta Sans", "Outfit", "Inter", system-ui, sans-serif',
    font_mono='"Fira Code", "JetBrains Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap',
    
    chart_grid_opacity=0.25,
)


# =============================================================================
# DEFAULT THEME ALIAS
# =============================================================================
# Point to midnight as the default theme for this plugin

{safe_name.upper()}_THEME = {safe_name.upper()}_MIDNIGHT


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Import themes in your executor or templates:
#        from .theme import {safe_name.upper()}_MIDNIGHT, get_theme_css_variables
#
# 2. Generate CSS variables:
#        theme_css = get_theme_css_variables({safe_name.upper()}_MIDNIGHT)
#
# 3. Available themes:
#        {safe_name}_midnight  - Deep blue + cyan (default)
#        {safe_name}_aurora    - Purple + magenta
#        {safe_name}_sunset    - Warm amber + orange
#        {safe_name}_frost     - Clean light blue
'''



def generate_widgets_module(name: str, safe_name: str, class_name: str) -> str:
    """Generate widgets.py with custom widget examples."""
    return f'''"""
Custom Widgets for {name} Plugin.

Widgets are reusable UI components that can be used across templates.
Register widgets with: helper.add_widget('widget_id', WidgetClass)
"""

from typing import Dict, Any


class {class_name}StatCard:
    """
    A reusable stat card widget for displaying key metrics.
    
    Usage in templates:
        {{{{ widgets.{safe_name}_stat_card.render(title="Score", value=85, trend="up") }}}}
    """
    
    @staticmethod
    def render(
        title: str,
        value: Any,
        subtitle: str = "",
        trend: str = "",  # "up", "down", or ""
        status: str = "neutral"  # "ok", "warn", "danger", "neutral"
    ) -> str:
        """
        Render the stat card HTML.
        
        Parameters:
            title: Card title
            value: Main value to display
            subtitle: Optional subtitle text
            trend: Trend indicator ("up", "down", or "")
            status: Status color ("ok", "warn", "danger", "neutral")
        
        Returns:
            HTML string for the stat card
        """
        trend_icon = ""
        if trend == "up":
            trend_icon = '<span class="trend trend-up">↑</span>'
        elif trend == "down":
            trend_icon = '<span class="trend trend-down">↓</span>'
        
        import html
        status_class = f"stat-card--{{status}}" if status != "neutral" else ""
        
        return f"""
        <div class="stat-card {{status_class}}">
            <div class="stat-card__title">{{html.escape(str(title))}}</div>
            <div class="stat-card__value">{{html.escape(str(value))}} {{trend_icon}}</div>
            <div class="stat-card__subtitle">{{html.escape(str(subtitle))}}</div>
        </div>
        """
    
    @staticmethod
    def get_css() -> str:
        """Return CSS for the stat card widget."""
        return """
        .stat-card {{
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            text-align: center;
        }}
        .stat-card__title {{
            font-size: 0.875rem;
            color: var(--text-soft);
            margin-bottom: 0.5rem;
        }}
        .stat-card__value {{
            font-size: 2rem;
            font-weight: 600;
            color: var(--text-main);
        }}
        .stat-card__subtitle {{
            font-size: 0.75rem;
            color: var(--text-soft);
            margin-top: 0.25rem;
        }}
        .stat-card--ok {{ border-color: var(--ok); }}
        .stat-card--warn {{ border-color: var(--warn); }}
        .stat-card--danger {{ border-color: var(--danger); }}
        .trend {{ margin-left: 0.25rem; }}
        .trend-up {{ color: var(--ok); }}
        .trend-down {{ color: var(--danger); }}
        """


# =============================================================================
# USAGE NOTES
# =============================================================================
#
# 1. Register in plugin.py on_load():
#        from .widgets import {class_name}StatCard
#        helper.add_widget("{safe_name}_stat_card", {class_name}StatCard)
#
# 2. Use in Jinja2 templates:
#        {{{{ widgets.{safe_name}_stat_card.render(title="Score", value=85) }}}}
#
# 3. Include widget CSS in your template:
#        <style>{{{{ widgets.{safe_name}_stat_card.get_css() }}}}</style>
'''


def generate_component_module(name: str, safe_name: str, class_name: str) -> str:
    """
    Generate components.py with Property Controls pattern.
    
    Creates example components demonstrating:
    - @register_component decorator
    - PropTypes schema definitions
    - Component templates
    """
    return f'''"""
Component Definitions for {name} plugin.

This module uses the Property Controls pattern where components
define their accepted props using PropTypes. Core validates YAML
against these schemas automatically.

Usage in YAML:
    components:
      - type: {safe_name}_chart
        id: my_chart
        chart: bar
        title: "Score Distribution"
        
      - type: {safe_name}_stat_card
        id: total
        label: "Total Items"
        value: "{{{{ stats.count }}}}"
"""

from bobreview.core.components import register_component, PropTypes


@register_component("{safe_name}_chart", plugin="{safe_name}")
class {class_name}ChartComponent:
    """
    Chart visualization component.
    
    Renders data as bar, line, pie, or other chart types.
    """
    
    props = {{
        "id": PropTypes.string(required=True, description="Unique chart ID"),
        "chart": PropTypes.choice(
            ["bar", "line", "pie", "scatter", "histogram", "doughnut"],
            default="bar",
            description="Chart type"
        ),
        "title": PropTypes.string(default="", description="Chart title"),
        "x": PropTypes.string(description="X-axis data field"),
        "y": PropTypes.string(description="Y-axis data field"),
        "animated": PropTypes.boolean(default=True, description="Enable animations"),
        "height": PropTypes.number(default=300, description="Chart height (px)"),
    }}
    
    template = "{safe_name}/components/chart.html.j2"


@register_component("{safe_name}_stat_card", plugin="{safe_name}")
class {class_name}StatCardComponent:
    """
    Stat card widget displaying a metric with label.
    
    Shows a prominent value with optional label, color, and status.
    """
    
    props = {{
        "id": PropTypes.string(description="Optional card ID"),
        "label": PropTypes.string(default="", description="Card label"),
        "value": PropTypes.template(required=True, description="Value (Jinja2)"),
        "color": PropTypes.color(description="Value color"),
        "icon": PropTypes.string(description="FontAwesome icon"),
        "variant": PropTypes.choice(
            ["default", "ok", "warn", "danger", "info"],
            default="default",
            description="Visual variant"
        ),
    }}
    
    template = "{safe_name}/components/stat_card.html.j2"


@register_component("{safe_name}_data_table", plugin="{safe_name}")
class {class_name}DataTableComponent:
    """
    Data table component for tabular data display.
    
    Renders data with sortable columns and optional pagination.
    """
    
    props = {{
        "id": PropTypes.string(description="Table ID"),
        "title": PropTypes.string(default="", description="Table title"),
        "columns": PropTypes.array(description="Column names"),
        "sortable": PropTypes.boolean(default=True, description="Sortable columns"),
        "paginated": PropTypes.boolean(default=False, description="Enable pagination"),
        "page_size": PropTypes.number(default=25, description="Rows per page"),
        "striped": PropTypes.boolean(default=True, description="Striped rows"),
    }}
    
    template = "{safe_name}/components/data_table.html.j2"


@register_component("{safe_name}_llm", plugin="{safe_name}")
class {class_name}LLMComponent:
    """
    LLM-generated content component.
    
    Generates content using an LLM with the provided prompt template.
    """
    
    props = {{
        "id": PropTypes.string(required=True, description="Unique ID"),
        "title": PropTypes.string(default="", description="Section title"),
        "prompt": PropTypes.template(description="Prompt template (Jinja2)"),
        "generator": PropTypes.string(description="Generator function"),
        "temperature": PropTypes.number(default=0.7, min=0, max=2),
    }}
    
    template = "{safe_name}/components/llm.html.j2"


@register_component("{safe_name}_text", plugin="{safe_name}")
class {class_name}TextComponent:
    """
    Static or templated text content.
    """
    
    props = {{
        "content": PropTypes.template(required=True, description="Content"),
        "markdown": PropTypes.boolean(default=False, description="Render as Markdown"),
        "class_name": PropTypes.string(default="", description="CSS class"),
    }}
    
    template = "{safe_name}/components/text.html.j2"


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Components are auto-registered when this module is imported
#    (via @register_component decorator)
#
# 2. Import in plugin.py __init__():
#        from . import components  # Triggers registration
#
# 3. Use in YAML config:
#        components:
#          - type: {safe_name}_chart
#            id: score_chart
#            chart: bar
#            title: "Scores"
#            x: name
#            y: score
'''


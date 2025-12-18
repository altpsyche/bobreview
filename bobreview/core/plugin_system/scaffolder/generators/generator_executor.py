"""
Generator for executor.py file.

Creates the YAML-driven report generation executor with:
- Page rendering from report_config.yaml
- Chart generation with theme support
- LLM content generation
- Tab-based navigation
"""


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
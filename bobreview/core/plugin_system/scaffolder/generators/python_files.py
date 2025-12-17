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
    """Generate CSV parser file."""
    return f'''"""
CSV Parser for {name} Plugin.

Data Flow:
    CSV → Parser.parse_directory() → List[Dict] → DataFrame
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import csv


class {class_name}CsvParser:
    """
    Parse CSV files with name, score, and category columns.
    
    Expected CSV format:
        name,score,category
        Item1,85,Backend
        Item2,72,Frontend
    """
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single CSV file (not used for multi-row CSVs)."""
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Find all CSV files in the directory."""
        return sorted(directory.glob("*.csv"))
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all CSV files and return combined records."""
        data_points = []
        
        for csv_file in self.discover_files(directory):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data_point = self._parse_row(row, csv_file.name)
                        if data_point:
                            data_points.append(data_point)
            except (OSError, csv.Error):
                continue
        
        return data_points
    
    def _parse_row(self, row: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row."""
        try:
            name = row.get('name', '').strip()
            score_str = row.get('score', '').strip()
            
            if not name or not score_str:
                return None
            
            return {{
                'name': name,
                'score': float(score_str),
                'category': row.get('category', 'General').strip(),
                'source': source_file,
            }}
        except (ValueError, TypeError):
            return None
'''


def generate_context_builder(name: str, class_name: str) -> str:
    """Generate context builder file."""
    return f'''"""
Context Builder for {name} Plugin.
"""

from typing import Dict, List, Any, Union


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """Convert DataFrame or other iterable to List[Dict]."""
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
                        llm_config = Config()
                        response = call_llm(full_prompt, config=llm_config)
                        llm_content[comp_id] = response or f'<em>No response for {comp_id}</em>'
                    except Exception as e:
                        llm_content[comp_id] = f'<div class="llm-error">LLM Error: {e}</div>'
    
    return llm_content


def render_component(
    comp: Dict[str, Any],
    data_points: List[Dict],
    stats: Dict[str, Any],
    llm_content: Dict[str, str],
    charts_js: List[str],
    chart_gen: "''' + class_name + '''ChartGenerator",
    theme: ReportTheme,
    safe_name: str
) -> str:
    """Render a single component to HTML."""
    comp_type = comp.get('type', '')
    
    # Stat Card
    if '_stat_card' in comp_type:
        label = comp.get('label', 'Stat')
        value_template = comp.get('value', '0')
        variant = comp.get('variant', 'default')
        
        # Simple template eval (supports data_points | length, stats.field.metric)
        value = eval_template(value_template, data_points, stats)
        
        variant_class = {'ok': 'stat-ok', 'warn': 'stat-warn', 'danger': 'stat-danger', 'info': 'stat-info'}.get(variant, '')
        return f'<div class="stat-card {variant_class}"><div class="stat-value">{value}</div><div class="stat-label">{label}</div></div>'
    
    # Chart
    elif '_chart' in comp_type:
        chart_id = comp.get('id', f'chart_{len(charts_js)}')
        chart_type = comp.get('chart', 'bar')
        title = comp.get('title', 'Chart')
        x_field = comp.get('x', 'name')
        y_field = comp.get('y', 'score')
        
        chart_config = {
            'id': chart_id,
            'type': chart_type,
            'title': title,
            'x_field': x_field,
            'y_field': y_field,
        }
        js_code = chart_gen.generate_chart(data_points, stats, None, chart_config, theme)
        charts_js.append(js_code)
        
        return f'<div class="chart-card"><h3>{title}</h3><div class="chart-container"><canvas id="{chart_id}"></canvas></div></div>'
    
    # LLM Content
    elif '_llm' in comp_type:
        comp_id = comp.get('id', 'unknown')
        title = comp.get('title', 'AI Analysis')
        content = llm_content.get(comp_id, '<em>No content</em>')
        return f'<div class="llm-section"><h3>{title}</h3><div class="llm-content">{content}</div></div>'
    
    # Data Table
    elif '_data_table' in comp_type:
        title = comp.get('title', 'Data')
        columns = comp.get('columns', ['name', 'score'])
        page_size = comp.get('page_size', 10)
        
        # Build table HTML
        headers = ''.join(f'<th>{col.title()}</th>' for col in columns)
        rows = ''
        for item in data_points[:page_size]:
            cells = ''.join(f'<td>{item.get(col, "")}</td>' for col in columns)
            rows += f'<tr>{cells}</tr>'
        
        table_html = f'<div class="table-section"><h3>{title}</h3>'
        table_html += f'<table class="data-table"><thead><tr>{headers}</tr></thead>'
        table_html += f'<tbody>{rows}</tbody></table>'
        table_html += f'<p class="table-info">Showing {min(page_size, len(data_points))} of {len(data_points)} items</p></div>'
        return table_html
    
    return f'<!-- Unknown component type: {comp_type} -->'


def eval_template(template: str, data_points: List[Dict], stats: Dict[str, Any]) -> str:
    """Simple template evaluation for stat card values."""
    try:
        # Handle common patterns
        if 'data_points | length' in template or 'data_points|length' in template:
            return str(len(data_points))
        
        # Handle stats.field.metric pattern
        if 'stats.' in template:
            import re
            match = re.search(r'stats\\.([\\w]+)\\.([\\w]+)', template)
            if match:
                field, metric = match.groups()
                value = stats.get(field, {}).get(metric, 0)
                # Check for round filter
                if '| round(' in template:
                    round_match = re.search(r'\\| round\\((\\d+)\\)', template)
                    if round_match:
                        digits = int(round_match.group(1))
                        return str(round(value, digits))
                return str(int(value) if value == int(value) else round(value, 2))
        
        return template.replace('{{', '').replace('}}', '').strip()
    except Exception:
        return template


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
    
    # Initialize chart generator
    chart_gen = ''' + class_name + '''ChartGenerator()
    charts_js = []
    
    # Render pages
    pages = config.get('pages', [])
    nav_html = ''
    pages_html = ''
    
    for i, page in enumerate(pages):
        page_id = page.get('id', f'page_{i}')
        page_title = page.get('title', f'Page {i+1}')
        active_class = 'active' if i == 0 else ''
        
        # Navigation tab
        nav_html += f'<button class="tab-btn {active_class}" onclick="showPage(\\'{page_id}\\')">{page_title}</button>'
        
        # Page content
        components_html = ''
        layout = page.get('layout', 'grid')
        
        for comp in page.get('components', []):
            comp_html = render_component(
                comp, data_points, stats, llm_content, charts_js, chart_gen, theme, "''' + safe_name + '''"
            )
            components_html += comp_html
        
        layout_class = {'grid': 'layout-grid', 'single-column': 'layout-single', 'flex': 'layout-flex'}.get(layout, 'layout-grid')
        pages_html += f'<div id="{page_id}" class="page-content {active_class} {layout_class}">{components_html}</div>'
    
    # Build final HTML
    report_name = config.get('name', "''' + name + ''' Report")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name}</title>
    {font_link}
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
{theme_css}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font-family); background: var(--bg); color: var(--text-main); min-height: 100vh; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}

/* Header */
header {{ text-align: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-subtle); }}
header h1 {{ color: var(--accent); font-size: 2.5rem; margin-bottom: 0.5rem; }}
header p {{ color: var(--text-soft); }}

/* Tabs */
.tabs {{ display: flex; gap: 0.5rem; margin-bottom: 2rem; flex-wrap: wrap; }}
.tab-btn {{ background: var(--bg-elevated); color: var(--text-soft); border: 1px solid var(--border-subtle); padding: 0.75rem 1.5rem; border-radius: var(--radius-md); cursor: pointer; font-size: 0.95rem; transition: all 0.2s; }}
.tab-btn:hover {{ background: var(--bg-soft); color: var(--text-main); }}
.tab-btn.active {{ background: var(--accent); color: var(--bg); border-color: var(--accent); }}

/* Pages */
.page-content {{ display: none; }}
.page-content.active {{ display: block; }}

/* Layouts */
.layout-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }}
.layout-single {{ display: flex; flex-direction: column; gap: 1.5rem; }}
.layout-flex {{ display: flex; flex-wrap: wrap; gap: 1.5rem; }}

/* Stat Cards */
.stat-card {{ background: var(--bg-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 1.5rem; text-align: center; }}
.stat-value {{ color: var(--accent); font-size: 2.5rem; font-weight: 700; }}
.stat-label {{ color: var(--text-soft); font-size: 0.85rem; text-transform: uppercase; margin-top: 0.5rem; }}
.stat-ok {{ border-left: 3px solid var(--ok); }}
.stat-warn {{ border-left: 3px solid var(--warn); }}
.stat-danger {{ border-left: 3px solid var(--danger); }}
.stat-info {{ border-left: 3px solid var(--accent); }}

/* Charts */
.chart-card {{ background: var(--bg-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 1.5rem; }}
.chart-card h3 {{ color: var(--accent); font-size: 1.1rem; margin-bottom: 1rem; }}
.chart-container {{ position: relative; height: 300px; }}

/* LLM Content */
.llm-section {{ background: var(--bg-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 1.5rem; grid-column: 1 / -1; }}
.llm-section h3 {{ color: var(--accent); font-size: 1.1rem; margin-bottom: 1rem; }}
.llm-content {{ color: var(--text-main); line-height: 1.7; }}
.llm-content p {{ margin-bottom: 0.75rem; }}
.llm-content ul, .llm-content ol {{ margin: 0.75rem 0; padding-left: 1.5rem; }}
.llm-content strong {{ color: var(--accent-strong); }}
.llm-dry-run {{ color: var(--text-soft); font-style: italic; padding: 1rem; background: var(--bg-soft); border-radius: var(--radius-md); }}
.llm-error {{ color: var(--danger); padding: 1rem; background: var(--danger-soft); border-radius: var(--radius-md); }}

/* Tables */
.table-section {{ background: var(--bg-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 1.5rem; grid-column: 1 / -1; overflow-x: auto; }}
.table-section h3 {{ color: var(--accent); font-size: 1.1rem; margin-bottom: 1rem; }}
.data-table {{ width: 100%; border-collapse: collapse; }}
.data-table th {{ background: var(--bg-soft); color: var(--accent); text-align: left; padding: 0.75rem; font-weight: 600; }}
.data-table td {{ padding: 0.75rem; border-bottom: 1px solid var(--border-subtle); }}
.data-table tr:hover {{ background: var(--bg-soft); }}
.table-info {{ color: var(--text-soft); font-size: 0.85rem; margin-top: 0.75rem; }}

@media (max-width: 768px) {{
    .layout-grid {{ grid-template-columns: 1fr; }}
    .tabs {{ flex-direction: column; }}
}}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{report_name}</h1>
            <p>Theme: {theme.name} | {len(data_points)} items</p>
        </header>
        <nav class="tabs">{nav_html}</nav>
        {pages_html}
    </div>
    <script>
function showPage(pageId) {{
    document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    event.target.classList.add('active');
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
    if hasattr(data, '__iter__') and hasattr(data, 'column_names'):
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
        
        status_class = f"stat-card--{{status}}" if status != "neutral" else ""
        
        return f"""
        <div class="stat-card {{status_class}}">
            <div class="stat-card__title">{{title}}</div>
            <div class="stat-card__value">{{value}} {{trend_icon}}</div>
            <div class="stat-card__subtitle">{{subtitle}}</div>
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


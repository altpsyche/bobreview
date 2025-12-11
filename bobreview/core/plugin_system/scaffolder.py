"""
Plugin scaffolder for creating new plugin skeletons.

Generates a complete plugin directory structure with:
- manifest.json
- plugin.py (main plugin class)
- parsers/ (data parser examples)
- context_builder.py
- chart_generator.py
- report_systems/ (JSON report definition)
- templates/ (Jinja2 templates)
- sample_data/ (example data files)
"""

import json
from pathlib import Path
from typing import Literal, Dict, Any

# Import themes from central module
from ..themes import (
    THEMES_BY_ID, 
    get_theme_by_id, 
    get_available_themes,
    theme_to_dict,
    ReportTheme,
)

def create_plugin(
    name: str,
    output_dir: Path,
    template: Literal['minimal', 'full'] = 'full',
    color_theme: str = 'dark'
) -> Path:
    """
    Create a new plugin directory with all necessary files.
    
    Parameters:
        name: Plugin name (e.g., "my-plugin")
        output_dir: Directory to create the plugin in
        template: 'minimal' for basic plugin, 'full' for all features
        color_theme: Color scheme: 'dark', 'ocean', 'purple', 'terminal', 'sunset'
    
    Returns:
        Path to the created plugin directory
    """
    # Validate theme
    if color_theme not in THEMES_BY_ID:
        available = ", ".join(THEMES_BY_ID.keys())
        raise ValueError(f"Unknown theme '{color_theme}'. Available: {available}")
    
    theme = get_theme_by_id(color_theme)
    
    plugin_dir = output_dir / name.replace('-', '_')
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Normalize name for Python usage
    safe_name = name.replace('-', '_').replace(' ', '_')
    class_name = ''.join(word.capitalize() for word in name.replace('_', '-').split('-'))
    
    # Create manifest.json
    manifest = {
        "name": name,
        "version": "1.0.0",
        "author": "Your Name",
        "description": f"Plugin for {name}",
        "entry_point": f"plugin:{class_name}Plugin",
        "dependencies": [],
        "provides": {
            "report_systems": [safe_name],
            "data_parsers": [f"{safe_name}_csv"],
        }
    }
    
    if template == 'full':
        manifest["provides"]["themes"] = [f"{safe_name}_theme"]
        manifest["provides"]["context_builders"] = [safe_name]
        manifest["provides"]["chart_generators"] = [safe_name]
    
    (plugin_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=4), encoding='utf-8'
    )
    
    # Create __init__.py
    init_content = f'''"""
{name} Plugin for BobReview.

Provides a report system for analyzing {name} data.
"""

from .plugin import {class_name}Plugin

__all__ = ['{class_name}Plugin']
'''
    (plugin_dir / "__init__.py").write_text(init_content, encoding='utf-8')
    
    # Create plugin.py
    plugin_content = _generate_plugin_py(name, safe_name, class_name, template)
    (plugin_dir / "plugin.py").write_text(plugin_content, encoding='utf-8')
    
    # Create parsers directory
    parsers_dir = plugin_dir / "parsers"
    parsers_dir.mkdir(exist_ok=True)
    
    parser_init = f'''"""Data parsers for {name} plugin."""

from .csv_parser import {class_name}CsvParser

__all__ = ['{class_name}CsvParser']
'''
    (parsers_dir / "__init__.py").write_text(parser_init, encoding='utf-8')
    
    parser_content = _generate_csv_parser(name, safe_name, class_name)
    (parsers_dir / "csv_parser.py").write_text(parser_content, encoding='utf-8')
    
    if template == 'full':
        # Create context_builder.py
        context_content = _generate_context_builder(name, safe_name, class_name)
        (plugin_dir / "context_builder.py").write_text(context_content, encoding='utf-8')
        
        # Create chart_generator.py
        chart_content = _generate_chart_generator(name, safe_name, class_name)
        (plugin_dir / "chart_generator.py").write_text(chart_content, encoding='utf-8')
    
    # Create report_systems directory
    rs_dir = plugin_dir / "report_systems"
    rs_dir.mkdir(exist_ok=True)
    
    report_system = _generate_report_system(name, safe_name, template, color_theme)
    (rs_dir / f"{safe_name}.json").write_text(
        json.dumps(report_system, indent=4), encoding='utf-8'
    )
    
    # Create templates directory
    templates_dir = plugin_dir / "templates" / safe_name / "pages"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    base_template = _generate_base_template(name, safe_name, theme)
    (templates_dir / "base.html.j2").write_text(base_template, encoding='utf-8')
    
    home_template = _generate_home_template(name, safe_name)
    (templates_dir / "home.html.j2").write_text(home_template, encoding='utf-8')
    
    # Create static CSS directory
    static_dir = plugin_dir / "templates" / safe_name / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate theme CSS (customizable colors)
    theme_css = _generate_theme_css(name, safe_name, theme, color_theme)
    (static_dir / "theme.css").write_text(theme_css, encoding='utf-8')
    
    # Generate plugin CSS (layout and components)
    plugin_css = _generate_plugin_css(name, safe_name)
    (static_dir / "plugin.css").write_text(plugin_css, encoding='utf-8')
    
    # Create sample_data directory
    sample_dir = plugin_dir / "sample_data"
    sample_dir.mkdir(exist_ok=True)
    
    sample_csv = """name,score,timestamp
Item1,85,2024-01-15
Item2,72,2024-01-16
Item3,91,2024-01-17
"""
    (sample_dir / "sample.csv").write_text(sample_csv, encoding='utf-8')
    
    return plugin_dir


def _generate_plugin_py(name: str, safe_name: str, class_name: str, template: str) -> str:
    """Generate the main plugin.py file."""
    imports = """from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper"""
    
    if template == 'full':
        imports += """
from bobreview.core.themes import ReportTheme
from .parsers.csv_parser import {class_name}CsvParser
from .context_builder import {class_name}ContextBuilder
from .chart_generator import {class_name}ChartGenerator""".format(class_name=class_name)
    else:
        imports += f"""
from .parsers.csv_parser import {class_name}CsvParser"""
    
    theme_section = ""
    if template == 'full':
        theme_section = f'''
    # Custom theme
    CUSTOM_THEME = ReportTheme(
        id="{safe_name}_theme",
        name="{name} Theme",
        bg="#1a1a2e",
        bg_elevated="#16213e",
        bg_soft="#0f3460",
        accent="#e94560",
        accent_soft="rgba(233, 69, 96, 0.15)",
        accent_strong="#ff6b6b",
        text_main="#eaeaea",
        text_soft="#a0a0a0",
        danger="#ff4757",
        danger_soft="rgba(255, 71, 87, 0.15)",
        warn="#ffa502",
        warn_soft="rgba(255, 165, 2, 0.15)",
        ok="#2ed573",
        ok_soft="rgba(46, 213, 115, 0.15)",
        border_subtle="#2f3545",
        shadow_soft="0 4px 12px rgba(0, 0, 0, 0.3)",
        radius_lg="12px",
        radius_md="8px",
    )
'''
    
    registration = f'''        # Register data parser
        helper.add_data_parser("{safe_name}_csv", {class_name}CsvParser)'''
    
    if template == 'full':
        registration += f'''
        
        # Register theme
        helper.add_theme(self.CUSTOM_THEME)
        
        # Register context builder
        helper.add_context_builder("{safe_name}", {class_name}ContextBuilder)
        
        # Register chart generator
        helper.add_chart_generator("{safe_name}", {class_name}ChartGenerator)'''
    
    registration += '''
        
        # Register templates
        template_dir = Path(__file__).parent / "templates"
        helper.add_templates(template_dir)
        
        # Register report systems
        report_systems_dir = Path(__file__).parent / "report_systems"
        helper.add_report_systems_from_dir(report_systems_dir)
        
        # Register default services
        helper.register_default_services()'''
    
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
{theme_section}
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


def _generate_csv_parser(name: str, safe_name: str, class_name: str) -> str:
    """Generate CSV parser file."""
    return f'''"""
CSV Parser for {name} Plugin.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

from bobreview.core.api import DataParserInterface


class {class_name}CsvParser(DataParserInterface):
    """
    Parse CSV files with name, score, and timestamp columns.
    
    Expected CSV format:
        name,score,timestamp
        Item1,85,2024-01-15
        Item2,72,2024-01-16
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
                'timestamp': self._parse_timestamp(row.get('timestamp', '')),
                'source': source_file,
            }}
        except (ValueError, TypeError):
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """Parse timestamp from string."""
        from datetime import datetime
        
        if not timestamp_str:
            return int(datetime.now().timestamp())
        
        try:
            return int(float(timestamp_str))
        except ValueError:
            pass
        
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return int(datetime.strptime(timestamp_str.strip(), fmt).timestamp())
            except ValueError:
                continue
        
        return int(datetime.now().timestamp())
'''


def _generate_context_builder(name: str, safe_name: str, class_name: str) -> str:
    """Generate context builder file."""
    return f'''"""
Context Builder for {name} Plugin.
"""

from typing import Dict, List, Any
from bobreview.core.api import ContextBuilderInterface


class {class_name}ContextBuilder(ContextBuilderInterface):
    """Build template context for {name} reports."""
    
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enriched context for template rendering."""
        context = dict(base_context)
        
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


def _generate_chart_generator(name: str, safe_name: str, class_name: str) -> str:
    """Generate chart generator file."""
    return f'''"""
Chart Generator for {name} Plugin.
"""

import json
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface


class {class_name}ChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js configurations for {name} reports."""
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """Generate a Chart.js configuration."""
        chart_type = chart_config.get('type', 'bar')
        
        sorted_data = sorted(data_points, key=lambda x: x.get('score', 0), reverse=True)
        labels = [d.get('name', 'Unknown') for d in sorted_data]
        values = [d.get('score', 0) for d in sorted_data]
        
        chart_data = {{
            'type': chart_type,
            'data': {{
                'labels': labels,
                'datasets': [{{
                    'label': chart_config.get('title', 'Score'),
                    'data': values,
                    'backgroundColor': 'rgba(233, 69, 96, 0.8)',
                    'borderColor': 'rgba(233, 69, 96, 1)',
                    'borderWidth': 1
                }}]
            }},
            'options': {{
                'responsive': True,
                'plugins': {{
                    'title': {{
                        'display': True,
                        'text': chart_config.get('title', 'Score Comparison')
                    }}
                }}
            }}
        }}
        
        return json.dumps(chart_data)
'''


def _generate_report_system(name: str, safe_name: str, template: str, color_theme: str = 'dark') -> dict:
    """Generate report system JSON with theme preset support."""
    return {
        "schema_version": "1.0",
        "id": safe_name,
        "name": f"{name} Report",
        "version": "1.0.0",
        "description": f"Report system for {name}",
        "author": "Your Name",
        
        "data_source": {
            "type": f"{safe_name}_csv",
            "input_format": "csv",
            "fields": {
                "name": {"type": "string", "required": True},
                "score": {"type": "float", "required": True},
                "timestamp": {"type": "integer", "required": False}
            }
        },
        
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2000,
            "chunk_size": 10
        },
        
        "llm_generators": [
            {
                "id": "summary",
                "name": "Summary",
                "description": "Executive summary of the data analysis",
                "prompt_template": f"Analyze this {name} data and provide a brief executive summary. Highlight key trends, outliers, and notable patterns.",
                "data_table": {
                    "columns": ["name", "score"],
                    "sample_strategy": "all",
                    "max_rows": 50
                },
                "returns": "string",
                "enabled": True
            },
            {
                "id": "recommendations",
                "name": "Recommendations",
                "description": "Actionable recommendations based on the data",
                "prompt_template": f"Based on this {name} data, provide 3-5 actionable recommendations for improvement.",
                "data_table": {
                    "columns": ["name", "score"],
                    "sample_strategy": "all",
                    "max_rows": 50
                },
                "returns": "string",
                "enabled": True
            }
        ],
        
        "theme": {
            "preset": color_theme  # dark, ocean, purple, terminal, sunset
        },
        
        "pages": [
            {
                "id": "home",
                "filename": "index.html",
                "nav_label": "Overview",
                "nav_order": 1,
                "template": {
                    "type": "jinja2",
                    "name": f"{safe_name}/pages/home.html.j2"
                },
                "llm_content": ["summary", "recommendations"],
                "llm_mappings": {
                    "summary": "summary",
                    "recommendations": "recommendations"
                },
                "charts": [
                    {
                        "id": "score_chart",
                        "type": "bar",
                        "title": "Score Comparison",
                        "x_field": "name",
                        "y_field": "score"
                    }
                ],
                "enabled": True
            }
        ],
        
        "output": {
            "default_filename": f"{safe_name}_report.html"
        }
    }


def _generate_base_template(name: str, safe_name: str, theme: ReportTheme) -> str:
    """Generate base Jinja2 template with linked CSS files."""
    t = theme  # shorthand for template interpolation (theme is unused in this function)
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title | default("''' + name + ''' Report") }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    {# Link external CSS files if available, otherwise use embedded styles #}
    {% if linked_css %}
    <link rel="stylesheet" href="static/theme.css">
    <link rel="stylesheet" href="static/plugin.css">
    {% else %}
    <style>
        /* ===== THEME VARIABLES (from JSON preset) ===== */
        :root {
            --bg: {{ theme.bg if theme else '#1a1a2e' }};
            --bg-elevated: {{ theme.bg_elevated if theme else '#16213e' }};
            --bg-soft: {{ theme.bg_soft if theme else '#0f3460' }};
            --bg-hover: {{ theme.accent_soft if theme else 'rgba(78, 161, 255, 0.08)' }};
            --accent: {{ theme.accent if theme else '#4ea1ff' }};
            --accent-soft: {{ theme.accent_soft if theme else 'rgba(78, 161, 255, 0.15)' }};
            --accent-strong: {{ theme.accent_strong if theme else '#ffb347' }};
            --text-main: {{ theme.text_main if theme else '#f5f7fb' }};
            --text-soft: {{ theme.text_soft if theme else '#a8b3c5' }};
            --ok: {{ theme.ok if theme else '#4fd18b' }};
            --ok-soft: {{ theme.ok_soft if theme else 'rgba(79, 209, 139, 0.15)' }};
            --warn: {{ theme.warn if theme else '#e6b35c' }};
            --warn-soft: {{ theme.warn_soft if theme else 'rgba(230, 179, 92, 0.15)' }};
            --danger: {{ theme.danger if theme else '#ff5c5c' }};
            --danger-soft: {{ theme.danger_soft if theme else 'rgba(255, 92, 92, 0.15)' }};
            --border: {{ theme.border if theme else '#2f3545' }};
            --border-subtle: rgba(255, 255, 255, 0.05);
            --shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.3);
            --shadow-strong: 0 8px 32px rgba(0, 0, 0, 0.4);
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'SF Mono', 'Fira Code', Consolas, monospace;
        }
        
        /* ===== BASE STYLES ===== */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: var(--font-family);
            background: var(--bg);
            color: var(--text-main);
            line-height: 1.7;
            -webkit-font-smoothing: antialiased;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        header { text-align: center; padding: 3rem 0; }
        header h1 { color: var(--accent); font-weight: 700; font-size: 2.5rem; }
        header p { color: var(--text-soft); }
        
        /* ===== CARDS ===== */
        .card {
            background: var(--bg-elevated);
            border-radius: var(--radius-lg);
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-soft);
            border: 1px solid var(--border-subtle);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover { transform: translateY(-2px); box-shadow: var(--shadow-strong); }
        .card h2 { color: var(--accent); margin-bottom: 1rem; font-size: 1.25rem; font-weight: 600; }
        
        /* ===== TABLES ===== */
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }
        th { color: var(--text-soft); font-weight: 500; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
        tr:hover { background: var(--bg-hover); }
        
        /* ===== CHARTS ===== */
        .chart-container { position: relative; height: 300px; padding: 1rem 0; }
        
        /* ===== LLM CONTENT ===== */
        .llm-content { line-height: 1.8; }
        .llm-content p { margin-bottom: 1rem; }
        .llm-content strong, .llm-content b { color: var(--accent); font-weight: 600; }
        .llm-content em, .llm-content i { color: var(--text-soft); }
        .llm-content ul, .llm-content ol { margin: 1rem 0; padding-left: 1.5rem; }
        .llm-content li { margin-bottom: 0.5rem; }
        .llm-content li::marker { color: var(--accent); }
        .llm-content h3, .llm-content h4 { color: var(--accent); margin: 1.5rem 0 0.75rem; }
        .llm-content code {
            background: var(--accent-soft);
            padding: 0.15rem 0.4rem;
            border-radius: var(--radius-sm);
            font-size: 0.9em;
            font-family: var(--font-mono);
            color: var(--accent);
        }
        .llm-content pre {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: var(--radius-md);
            overflow-x: auto;
            margin: 1rem 0;
        }
        .llm-content pre code { background: none; padding: 0; color: var(--text-main); }
        .llm-content blockquote {
            border-left: 3px solid var(--accent);
            padding-left: 1rem;
            margin: 1rem 0;
            color: var(--text-soft);
            font-style: italic;
        }
        .llm-content a { color: var(--accent); text-decoration: none; }
        .llm-content a:hover { text-decoration: underline; }
        
        /* ===== BADGES ===== */
        .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: var(--radius-xl); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-ok { background: var(--ok-soft); color: var(--ok); }
        .badge-warn { background: var(--warn-soft); color: var(--warn); }
        .badge-danger { background: var(--danger-soft); color: var(--danger); }
        
        /* ===== UTILITIES ===== */
        .text-soft { color: var(--text-soft); }
        .text-accent { color: var(--accent); }
        .text-ok { color: var(--ok); }
        .text-warn { color: var(--warn); }
        .text-danger { color: var(--danger); }
    </style>
    {% endif %}
    
    {% block head %}{% endblock %}
</head>
<body>
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    {% block scripts %}{% endblock %}
</body>
</html>'''


def _generate_home_template(name: str, safe_name: str) -> str:
    """Generate home page template."""
    return '''{% extends "''' + safe_name + '''/pages/base.html.j2" %}

{% block content %}
<header>
    <h1>{{ config.title | default("''' + name + ''' Report") }}</h1>
    <p>{{ meta_text }}</p>
</header>

{% if llm.summary %}
<div class="card">
    <h2>Executive Summary</h2>
    <div class="llm-content">{{ llm.summary | sanitize }}</div>
</div>
{% endif %}

<div class="card">
    <h2>Score Overview</h2>
    <div class="chart-container">
        <canvas id="scoreChart"></canvas>
    </div>
</div>

<div class="card">
    <h2>Rankings</h2>
    <table>
        <thead>
            <tr><th>Rank</th><th>Name</th><th>Score</th></tr>
        </thead>
        <tbody>
            {% for item in ranked_data %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.score | int }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if llm.recommendations %}
<div class="card">
    <h2>Recommendations</h2>
    <div class="llm-content">{{ llm.recommendations | sanitize }}</div>
</div>
{% endif %}
{% endblock %}

{% block scripts %}
<script>
{% if charts.score_chart %}
const ctx = document.getElementById('scoreChart').getContext('2d');
new Chart(ctx, {{ charts.score_chart | safe }});
{% endif %}
</script>
{% endblock %}'''


def _generate_theme_css(name: str, safe_name: str, theme: ReportTheme, theme_name: str) -> str:
    """Generate customizable theme CSS file with selected theme."""
    t = theme  # shorthand
    
    # Build the alternatives section showing other available themes
    other_themes = []
    for tid, tdata in THEMES_BY_ID.items():
        if tid != theme_name and tid in ('dark', 'ocean', 'purple', 'terminal', 'sunset'):
            other_themes.append(f'''/*
--- {tdata.name} Theme ---
:root {{
    --bg: {tdata.bg};
    --bg-elevated: {tdata.bg_elevated};
    --accent: {tdata.accent};
    --accent-soft: {tdata.accent_soft};
    --text-main: {tdata.text_main};
    --text-soft: {tdata.text_soft};
}}
*/''')
    alternatives = '\n\n'.join(other_themes)
    
    return f'''/*
 * {name} Theme — {t.name}
 * 
 * Customize your plugin's color scheme here.
 * All CSS variables can be overridden per-theme.
 * 
 * Created with: bobreview plugins create {name} --theme {theme_name}
 */

:root {{
    /* ===========================================
       BACKGROUND COLORS
       =========================================== */
    --bg: {t.bg};                          /* Main background */
    --bg-elevated: {t.bg_elevated};                 /* Cards, panels */
    --bg-soft: {t.bg_soft};                     /* Subtle backgrounds */
    --bg-hover: {t.accent_soft};    /* Hover states */
    
    /* ===========================================
       ACCENT COLORS (Primary Brand)
       =========================================== */
    --accent: {t.accent};                      /* Primary accent */
    --accent-soft: {t.accent_soft}; /* Accent backgrounds */
    --accent-strong: {t.accent_strong};               /* Emphasized accent */
    --accent-gradient: linear-gradient(135deg, {t.accent} 0%, {t.accent_strong} 100%);
    
    /* ===========================================
       TEXT COLORS
       =========================================== */
    --text-main: {t.text_main};                   /* Primary text */
    --text-soft: {t.text_soft};                   /* Secondary text */
    --text-muted: #6c7a89;                  /* Muted/disabled text */
    
    /* ===========================================
       STATUS COLORS
       =========================================== */
    --ok: {t.ok};                          /* Success, good */
    --ok-soft: {t.ok_soft};
    --warn: {t.warn};                        /* Warning, caution */
    --warn-soft: {t.warn_soft};
    --danger: {t.danger};                      /* Error, critical */
    --danger-soft: {t.danger_soft};
    
    /* ===========================================
       BORDERS & SHADOWS
       =========================================== */
    --border: {t.border_subtle};                      /* Default borders */
    --border-subtle: rgba(255, 255, 255, 0.05);
    --shadow-soft: {t.shadow_soft};
    
    /* ===========================================
       SIZING & SPACING
       =========================================== */
    --radius-sm: 4px;
    --radius-md: {t.radius_md};
    --radius-lg: {t.radius_lg};
    --radius-xl: 16px;
    
    /* ===========================================
       TYPOGRAPHY
       =========================================== */
    --font-family: {t.font_sans};
    --font-mono: {t.font_mono};
}}

/* ===========================================
   ALTERNATIVE THEMES
   
   Uncomment one of these to use a different scheme,
   or create your own!
   =========================================== */

{alternatives}
'''


def _generate_plugin_css(name: str, safe_name: str) -> str:
    """Generate plugin-specific layout and component CSS."""
    return '''/*
 * ''' + name + ''' Plugin Styles
 * 
 * Layout and component styles for the plugin.
 * Customize these to match your plugin's needs.
 */

/* ===========================================
   BASE RESET & TYPOGRAPHY
   =========================================== */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: var(--font-family);
    background: var(--bg);
    color: var(--text-main);
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
}

/* ===========================================
   LAYOUT
   =========================================== */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

header {
    text-align: center;
    padding: 3rem 0;
}

header h1 {
    color: var(--accent);
    font-weight: 700;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

header p {
    color: var(--text-soft);
}

/* ===========================================
   CARDS
   =========================================== */
.card {
    background: var(--bg-elevated);
    border-radius: var(--radius-lg);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-soft);
    border: 1px solid var(--border-subtle);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-strong);
}

.card h2 {
    color: var(--accent);
    margin-bottom: 1rem;
    font-size: 1.25rem;
    font-weight: 600;
}

/* ===========================================
   TABLES
   =========================================== */
table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

th {
    color: var(--text-soft);
    font-weight: 500;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
}

tr:hover {
    background: var(--bg-hover);
}

/* ===========================================
   CHARTS
   =========================================== */
.chart-container {
    position: relative;
    height: 300px;
    padding: 1rem 0;
}

/* ===========================================
   LLM / MARKDOWN CONTENT
   =========================================== */
.llm-content {
    line-height: 1.8;
}

.llm-content p {
    margin-bottom: 1rem;
}

.llm-content strong,
.llm-content b {
    color: var(--accent);
    font-weight: 600;
}

.llm-content em,
.llm-content i {
    color: var(--text-soft);
}

.llm-content ul,
.llm-content ol {
    margin: 1rem 0;
    padding-left: 1.5rem;
}

.llm-content li {
    margin-bottom: 0.5rem;
}

.llm-content li::marker {
    color: var(--accent);
}

.llm-content h3,
.llm-content h4 {
    color: var(--accent);
    margin: 1.5rem 0 0.75rem;
}

.llm-content code {
    background: var(--accent-soft);
    padding: 0.15rem 0.4rem;
    border-radius: var(--radius-sm);
    font-size: 0.9em;
    font-family: var(--font-mono);
    color: var(--accent);
}

.llm-content pre {
    background: rgba(0, 0, 0, 0.3);
    padding: 1rem;
    border-radius: var(--radius-md);
    overflow-x: auto;
    margin: 1rem 0;
}

.llm-content pre code {
    background: none;
    padding: 0;
    color: var(--text-main);
}

.llm-content blockquote {
    border-left: 3px solid var(--accent);
    padding-left: 1rem;
    margin: 1rem 0;
    color: var(--text-soft);
    font-style: italic;
}

.llm-content a {
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s ease;
}

.llm-content a:hover {
    border-bottom-color: var(--accent);
}

/* ===========================================
   STATUS BADGES
   =========================================== */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-xl);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-ok {
    background: var(--ok-soft);
    color: var(--ok);
}

.badge-warn {
    background: var(--warn-soft);
    color: var(--warn);
}

.badge-danger {
    background: var(--danger-soft);
    color: var(--danger);
}

/* ===========================================
   UTILITIES
   =========================================== */
.text-soft { color: var(--text-soft); }
.text-accent { color: var(--accent); }
.text-ok { color: var(--ok); }
.text-warn { color: var(--warn); }
.text-danger { color: var(--danger); }

.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mt-3 { margin-top: 1.5rem; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
'''

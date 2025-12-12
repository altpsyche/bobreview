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

# Import via ThemeSystem for centralized theme access
from ..theme_system import get_theme_system
from ..themes import (
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
    # Validate and get theme via ThemeSystem
    theme_system = get_theme_system()
    theme = theme_system.get_theme(color_theme)
    
    if not theme:
        available = ", ".join(get_available_themes())
        raise ValueError(f"Unknown theme '{color_theme}'. Available: {available}")
    
    # Normalize name for directory and Python usage
    safe_name = name.replace('-', '_').replace(' ', '_')
    plugin_dir = output_dir / safe_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
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
    
    parser_content = _generate_csv_parser(name, class_name)
    (parsers_dir / "csv_parser.py").write_text(parser_content, encoding='utf-8')
    
    if template == 'full':
        # Create context_builder.py
        context_content = _generate_context_builder(name, class_name)
        (plugin_dir / "context_builder.py").write_text(context_content, encoding='utf-8')
        
        # Create chart_generator.py
        chart_content = _generate_chart_generator(name, class_name)
        (plugin_dir / "chart_generator.py").write_text(chart_content, encoding='utf-8')
    
    # Create report_systems directory
    rs_dir = plugin_dir / "report_systems"
    rs_dir.mkdir(exist_ok=True)
    
    report_system = _generate_report_system(name, safe_name, color_theme)
    (rs_dir / f"{safe_name}.json").write_text(
        json.dumps(report_system, indent=4), encoding='utf-8'
    )
    
    # Create templates directory
    templates_dir = plugin_dir / "templates" / safe_name / "pages"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    base_template = _generate_base_template(name, safe_name)
    (templates_dir / "base.html.j2").write_text(base_template, encoding='utf-8')
    
    home_template = _generate_home_template(name, safe_name)
    (templates_dir / "home.html.j2").write_text(home_template, encoding='utf-8')
    
    # Create details page for multi-page example
    details_template = _generate_details_template(name, safe_name)
    (templates_dir / "details.html.j2").write_text(details_template, encoding='utf-8')
    
    # Create components directory with macros
    components_dir = plugin_dir / "templates" / "components"
    components_dir.mkdir(parents=True, exist_ok=True)
    
    macros_template = _generate_macros_template(name)
    (components_dir / "macros.html.j2").write_text(macros_template, encoding='utf-8')
    
    # Create static CSS directory
    static_dir = plugin_dir / "templates" / safe_name / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Note: theme.css is NOT generated here - it's generated dynamically at runtime
    # based on the theme specified in the report system JSON or CLI --theme flag.
    # This ensures theme changes are always reflected without regenerating plugin files.
    
    # Generate plugin CSS (layout and components)
    plugin_css = _generate_plugin_css(name)
    (static_dir / "plugin.css").write_text(plugin_css, encoding='utf-8')
    
    # Create analysis module (for full template)
    if template == 'full':
        analysis_content = _generate_analysis_module(name, safe_name)
        (plugin_dir / "analysis.py").write_text(analysis_content, encoding='utf-8')
    
    # Create sample_data directory with better sample data
    sample_dir = plugin_dir / "sample_data"
    sample_dir.mkdir(exist_ok=True)
    
    sample_csv = """name,score,category
Alpha Project,95,Backend
Beta Module,82,Frontend
Core System,78,Infrastructure
Delta Service,91,Backend
Echo Framework,65,DevOps
Foxtrot API,88,Backend
Golf Component,73,Frontend
Hotel Library,96,Core
India Utils,84,Utils
Juliet Engine,69,Core
Kilo Dashboard,77,Frontend
Lima Gateway,92,Infrastructure
"""
    (sample_dir / "sample.csv").write_text(sample_csv, encoding='utf-8')
    
    return plugin_dir


def _generate_plugin_py(name: str, safe_name: str, class_name: str, template: str) -> str:
    """Generate the main plugin.py file."""
    imports = """from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper"""
    
    if template == 'full':
        imports += """
from .parsers.csv_parser import {class_name}CsvParser
from .context_builder import {class_name}ContextBuilder
from .chart_generator import {class_name}ChartGenerator""".format(class_name=class_name)
    else:
        imports += f"""
from .parsers.csv_parser import {class_name}CsvParser"""
    
    # No custom theme generation - plugins should use built-in themes via JSON preset
    theme_section = ""
    
    registration = f'''        # Register data parser
        helper.add_data_parser("{safe_name}_csv", {class_name}CsvParser)'''
    
    if template == 'full':
        registration += f'''
        
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


def _generate_csv_parser(name: str, class_name: str) -> str:
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


def _generate_context_builder(name: str, class_name: str) -> str:
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


def _generate_chart_generator(name: str, class_name: str) -> str:
    """Generate chart generator file with theme support."""
    # Use raw strings and careful escaping for the nested f-string template
    return '''"""
Chart Generator for ''' + name + ''' Plugin.

Generates Chart.js JavaScript code with theme-aware coloring.
"""

import json
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME


class ''' + class_name + '''ChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js JavaScript code with theme support."""
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate Chart.js JavaScript code.
        
        Returns JavaScript code that creates the chart, NOT JSON config.
        """
        chart_id = chart_config.get('id', 'chart')
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'score')
        x_field = chart_config.get('x_field', 'name')
        
        # Get theme from config
        theme_id = chart_config.get('theme_id', 'terminal')
        theme = get_theme_by_id(theme_id) or DARK_THEME
        
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
        
        # Build JavaScript code
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
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
'''


def _generate_report_system(name: str, safe_name: str, color_theme: str = 'dark') -> dict:
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
                "category": {"type": "string", "required": False}
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
                "data_requirements": {
                    "data_points": False,
                    "images": False
                },
                "enabled": True
            },
            {
                "id": "details",
                "filename": "details.html",
                "nav_label": "Details",
                "nav_order": 2,
                "card_icon": "fa-chart-bar",
                "card_description": "Detailed statistics and full data table.",
                "template": {
                    "type": "jinja2",
                    "name": f"{safe_name}/pages/details.html.j2"
                },
                "charts": [
                    {
                        "id": "distribution_chart",
                        "type": "histogram",
                        "title": "Score Distribution",
                        "y_field": "score"
                    }
                ],
                "data_requirements": {
                    "data_points": True,
                    "images": False
                },
                "enabled": True
            }
        ],
        
        "output": {
            "default_filename": f"{safe_name}_report.html"
        }
    }


def _generate_base_template(name: str, safe_name: str) -> str:
    """Generate base Jinja2 template using unified theme system."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ config.title | default("''' + name + ''' Report") }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    {# Unified theme system - supports both embedded and linked CSS #}
    {% if linked_css %}
    <link rel="stylesheet" href="static/theme.css">
    <link rel="stylesheet" href="static/plugin.css">
    {% else %}
    <style>
        {# Use unified theme system - theme_name comes from context #}
        {# get_theme_css() includes theme variables AND base styles #}
        {{ get_theme_css(theme_name) }}
    </style>
    <style>
        {# Include plugin-specific styles (layout and components) #}
        {% include "''' + safe_name + '''/static/plugin.css" ignore missing %}
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
    """Generate home page template with macros support."""
    return '''{% extends "''' + safe_name + '''/pages/base.html.j2" %}
{% from "components/macros.html.j2" import stat_card, feature_card %}

{% block content %}
<header>
    <h1>{{ config.title | default("''' + name + ''' Report") }}</h1>
    <p>{{ meta_text }}</p>
    <nav class="nav-links">
        <a href="index.html" class="active">Overview</a>
        <a href="details.html">Details</a>
    </nav>
</header>

{% if llm.summary %}
<div class="card">
    <h2>Executive Summary</h2>
    <div class="llm-content">{{ llm.summary | sanitize }}</div>
</div>
{% endif %}

{# Compute stats from data_points if not provided in stats dict #}
{% set item_count = stats.count|default(data_points|length) %}
{% set scores = data_points|map(attribute="score")|list if data_points else [] %}
{% set avg_score = (scores|sum / scores|length)|round(1) if scores else 0 %}
{% set max_score = scores|max if scores else 0 %}
{% set min_score = scores|min if scores else 0 %}

<div class="card">
    <h2>Quick Stats</h2>
    <div class="stats-grid">
        {{ stat_card("Total Items", item_count) }}
        {{ stat_card("Average", avg_score|format_number(1)) }}
        {{ stat_card("Highest", max_score|format_number(0), variant="ok") }}
        {{ stat_card("Lowest", min_score|format_number(0), variant="danger") }}
    </div>
</div>

<div class="card">
    <h2>Score Overview</h2>
    <div class="chart-container">
        <canvas id="score_chart"></canvas>
    </div>
</div>

<div class="card">
    <h2>Top Rankings</h2>
    <table>
        <thead>
            <tr><th>Rank</th><th>Name</th><th>Score</th></tr>
        </thead>
        <tbody>
            {% for item in ranked_data[:5] %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.score | format_number(0) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <p class="text-soft mt-2"><a href="details.html">View all data</a></p>
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
{% if charts.score_chart %}{{ charts.score_chart | safe }}{% endif %}
</script>
{% endblock %}'''


def _generate_details_template(name: str, safe_name: str) -> str:
    """Generate details page template for multi-page example."""
    return '''{% extends "''' + safe_name + '''/pages/base.html.j2" %}
{% from "components/macros.html.j2" import stat_card, metric_table %}

{% block content %}
<header>
    <h1>Detailed Analysis</h1>
    <nav class="nav-links">
        <a href="index.html">Overview</a>
        <a href="details.html" class="active">Details</a>
    </nav>
</header>

{# Compute stats from data_points #}
{% set scores = data_points|map(attribute="score")|list if data_points else [] %}
{% set item_count = scores|length %}
{% set avg_score = (scores|sum / item_count)|round(1) if item_count > 0 else 0 %}
{% set max_score = scores|max if scores else 0 %}
{% set min_score = scores|min if scores else 0 %}
{% set score_range = max_score - min_score %}

<div class="card">
    <h2>Statistics</h2>
    <div class="stats-grid">
        {{ stat_card("Total Items", item_count) }}
        {{ stat_card("Average", avg_score|format_number(1)) }}
        {{ stat_card("Range", score_range|format_number(0)) }}
        {{ stat_card("Spread", ((max_score - min_score) / max_score * 100)|round(0) if max_score > 0 else 0, subtitle="%") }}
    </div>
</div>

<div class="card">
    <h2>Distribution</h2>
    <div class="chart-container">
        <canvas id="distribution_chart"></canvas>
    </div>
</div>

<div class="card">
    <h2>Full Data Table</h2>
    <table>
        <thead>
            <tr><th>#</th><th>Name</th><th>Score</th><th>Category</th></tr>
        </thead>
        <tbody>
            {% for item in data_points %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ item.name }}</td>
                <td class="{% if item.score >= 90 %}text-ok{% elif item.score < 70 %}text-danger{% endif %}">{{ item.score | format_number(0) }}</td>
                <td><span class="badge">{{ item.category }}</span></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}

{% block scripts %}
<script>
{% if charts.distribution_chart %}{{ charts.distribution_chart | safe }}{% endif %}
</script>
{% endblock %}'''


def _generate_macros_template(name: str) -> str:
    """Generate reusable Jinja2 macros for UI components."""
    return '''{#
 # Reusable UI Macros for ''' + name + '''
 # Import with: {% from "components/macros.html.j2" import stat_card, feature_card %}
 #}

{# Stat Card - displays a key metric with optional variant styling #}
{% macro stat_card(label, value, subtitle='', variant='') %}
<div class="stat-card{% if variant %} stat-card--{{ variant }}{% endif %}">
  <div class="stat-card-label">{{ label }}</div>
  <div class="stat-card-value">{{ value }}</div>
  {% if subtitle %}<div class="stat-card-sub">{{ subtitle }}</div>{% endif %}
</div>
{% endmacro %}

{# Feature Card - navigation link with icon #}
{% macro feature_card(url, icon, title, description) %}
<a href="{{ url }}" class="feature-card">
  <i class="fas {{ icon }}"></i>
  <div class="feature-card-content">
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
  </div>
</a>
{% endmacro %}

{# Metric Table - displays statistics from a stats dict #}
{% macro metric_table(title, stats, labels={}) %}
<h3>{{ title }}</h3>
<table>
  <thead>
    <tr>
      <th>{{ labels.get('metric', 'Metric') }}</th>
      <th>{{ labels.get('value', 'Value') }}</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Minimum</td><td>{{ stats.min|format_number }}</td></tr>
    <tr><td>Maximum</td><td>{{ stats.max|format_number }}</td></tr>
    <tr><td>Mean</td><td>{{ stats.mean|format_number(1) }}</td></tr>
    <tr><td>Median</td><td>{{ stats.median|format_number(1) }}</td></tr>
    {% if stats.stdev %}<tr><td>Std Dev</td><td>{{ stats.stdev|format_number(1) }}</td></tr>{% endif %}
  </tbody>
</table>
{% endmacro %}

{# Progress Bar - horizontal bar showing progress toward a max value #}
{% macro progress_bar(value, max, label='', variant='') %}
{% set pct = (value / max * 100) if max > 0 else 0 %}
<div class="progress-bar{% if variant %} progress-bar--{{ variant }}{% endif %}">
  <div class="progress-bar-label">{{ label }}</div>
  <div class="progress-bar-track">
    <div class="progress-bar-fill" style="width: {{ pct|round }}%"></div>
  </div>
  <div class="progress-bar-value">{{ value|format_number }} / {{ max|format_number }}</div>
</div>
{% endmacro %}

{# Callout/Alert Box - highlights important information #}
{% macro callout(title, variant='info') %}
<div class="callout callout--{{ variant }}">
  <div class="callout-title">{{ title }}</div>
  <div class="callout-content">{{ caller() }}</div>
</div>
{% endmacro %}

{# Badge - small status indicator #}
{% macro badge(text, variant='') %}
<span class="badge{% if variant %} badge-{{ variant }}{% endif %}">{{ text }}</span>
{% endmacro %}
'''


def _generate_analysis_module(name: str, safe_name: str) -> str:
    """Generate analysis module with statistical functions."""
    return f'''"""
Statistical Analysis for {name} Plugin.

Provides common statistical functions for data analysis.
Register with: get_analyzer_registry().register('{safe_name}', analyze_{safe_name}_data)
"""

from typing import List, Dict, Any
import statistics


def analyze_{safe_name}_data(
    data_points: List[Dict[str, Any]],
    config: Any = None
) -> Dict[str, Any]:
    """
    Compute statistics from parsed data.
    
    Parameters:
        data_points: List of parsed data points with 'score' field
        config: Optional ReportConfig
    
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


# Removed - now using unified ThemeSystem.generate_theme_css_file()


def _generate_plugin_css(name: str) -> str:
    """Generate plugin-specific layout and component CSS."""
    return '''/*
 * ''' + name + ''' Plugin Styles
 * 
 * Premium layout and component styles.
 * Theme colors are provided via CSS variables from get_theme_css().
 */

/* ===========================================
   GLOBAL ENHANCEMENTS
   =========================================== */
* {
    box-sizing: border-box;
}

body {
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: linear-gradient(180deg, var(--bg) 0%, var(--bg-soft) 100%);
    min-height: 100vh;
}

/* ===========================================
   LAYOUT
   =========================================== */
.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 2.5rem;
}

/* ===========================================
   HEADER - Premium Hero Section
   =========================================== */
header {
    text-align: center;
    padding: 3rem 2rem 2rem;
    margin-bottom: 1rem;
    position: relative;
}

header::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100px;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    border-radius: 2px;
}

header h1 {
    background: linear-gradient(135deg, var(--accent) 0%, var(--text-main) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    font-size: 2.75rem;
    letter-spacing: -0.02em;
    margin-bottom: 0.75rem;
}

header p {
    color: var(--text-soft);
    font-size: 1.05rem;
    max-width: 600px;
    margin: 0 auto;
}

/* ===========================================
   CARDS - Glassmorphism Style
   =========================================== */
.card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 
        0 4px 24px rgba(0, 0, 0, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.12);
}

.card:hover::before {
    opacity: 1;
}

.card h2 {
    color: var(--accent);
    margin-bottom: 1.25rem;
    font-size: 1.35rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.5rem;
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
    border-bottom: 1px solid var(--border-subtle);
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
   STAT CARDS & STATS GRID
   =========================================== */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.stat-card {
    background: var(--bg-soft);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    text-align: center;
    border: 1px solid var(--border-subtle);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-soft);
}

.stat-card-label {
    color: var(--text-soft);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

.stat-card-value {
    color: var(--text-main);
    font-size: 1.75rem;
    font-weight: 700;
}

.stat-card-sub {
    color: var(--text-soft);
    font-size: 0.8rem;
    margin-top: 0.25rem;
}

.stat-card--ok .stat-card-value { color: var(--ok); }
.stat-card--warn .stat-card-value { color: var(--warn); }
.stat-card--danger .stat-card-value { color: var(--danger); }

/* ===========================================
   NAVIGATION LINKS
   =========================================== */
.nav-links {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.nav-links a {
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    color: var(--text-soft);
    text-decoration: none;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}

.nav-links a:hover {
    color: var(--text-main);
    background: var(--bg-soft);
}

.nav-links a.active {
    color: var(--accent);
    background: var(--accent-soft);
    border-color: var(--accent);
}

/* ===========================================
   PROGRESS BARS
   =========================================== */
.progress-bar {
    margin: 0.75rem 0;
}

.progress-bar-label {
    color: var(--text-soft);
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
}

.progress-bar-track {
    background: var(--bg-soft);
    border-radius: var(--radius-md);
    height: 8px;
    overflow: hidden;
}

.progress-bar-fill {
    background: var(--accent);
    height: 100%;
    border-radius: var(--radius-md);
    transition: width 0.3s ease;
}

.progress-bar-value {
    color: var(--text-soft);
    font-size: 0.75rem;
    text-align: right;
    margin-top: 0.25rem;
}

.progress-bar--ok .progress-bar-fill { background: var(--ok); }
.progress-bar--warn .progress-bar-fill { background: var(--warn); }
.progress-bar--danger .progress-bar-fill { background: var(--danger); }

/* ===========================================
   CALLOUTS / ALERTS
   =========================================== */
.callout {
    padding: 1rem 1.25rem;
    border-radius: var(--radius-md);
    margin: 1rem 0;
    border-left: 4px solid;
}

.callout-title {
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.callout-content {
    color: var(--text-soft);
}

.callout--info {
    background: var(--accent-soft);
    border-color: var(--accent);
}
.callout--info .callout-title { color: var(--accent); }

.callout--warn {
    background: var(--warn-soft);
    border-color: var(--warn);
}
.callout--warn .callout-title { color: var(--warn); }

.callout--danger {
    background: var(--danger-soft);
    border-color: var(--danger);
}
.callout--danger .callout-title { color: var(--danger); }

.callout--ok {
    background: var(--ok-soft);
    border-color: var(--ok);
}
.callout--ok .callout-title { color: var(--ok); }

/* ===========================================
   FEATURE CARDS
   =========================================== */
.feature-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.25rem;
    background: var(--bg-soft);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-subtle);
    text-decoration: none;
    transition: all 0.2s ease;
}

.feature-card:hover {
    background: var(--bg-hover);
    border-color: var(--accent);
    transform: translateX(4px);
}

.feature-card i {
    font-size: 1.5rem;
    color: var(--accent);
}

.feature-card-content h3 {
    color: var(--text-main);
    font-size: 1rem;
    margin-bottom: 0.25rem;
}

.feature-card-content p {
    color: var(--text-soft);
    font-size: 0.85rem;
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

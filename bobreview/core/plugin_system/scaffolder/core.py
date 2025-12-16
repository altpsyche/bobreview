"""
Plugin scaffolder core - main orchestration for creating plugin skeletons.

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
from typing import Literal

# Themes are now plugin-owned - no core imports needed

# Import generators
from .generators import (
    generate_plugin_py,
    generate_csv_parser,
    generate_context_builder,
    generate_executor,
    generate_chart_generator,
    generate_analysis_module,
    generate_theme_module,
    generate_widgets_module,
    generate_component_module,
    generate_manifest,
    generate_report_system,
    generate_user_report_config,
)


# Path to scaffolder templates
TEMPLATES_DIR = Path(__file__).parent / "templates"


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
    # color_theme is just a hint for generated theme styling
    # No validation needed - plugins create their own themes

    # Ensure output_dir is a Path
    output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
    
    # Normalize name for directory and Python usage
    safe_name = name.replace('-', '_').replace(' ', '_')
    plugin_dir = output_dir / safe_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    class_name = ''.join(word.capitalize() for word in name.replace('_', '-').split('-'))
    
    # Create manifest.json
    manifest = generate_manifest(name, safe_name, class_name, template)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=4), encoding='utf-8'
    )
    
    # Create __init__.py
    init_content = f'''"""
{name} Plugin for BobReview.

Provides a report system for analyzing {name} data.
"""

from .plugin import {class_name}Plugin
from .executor import generate_report

__all__ = ['{class_name}Plugin', 'generate_report']
'''
    (plugin_dir / "__init__.py").write_text(init_content, encoding='utf-8')
    
    # Create plugin.py
    plugin_content = generate_plugin_py(name, safe_name, class_name, template)
    (plugin_dir / "plugin.py").write_text(plugin_content, encoding='utf-8')
    
    # Create parsers directory
    parsers_dir = plugin_dir / "parsers"
    parsers_dir.mkdir(exist_ok=True)
    
    parser_init = f'''"""Data parsers for {name} plugin."""

from .csv_parser import {class_name}CsvParser

__all__ = ['{class_name}CsvParser']
'''
    (parsers_dir / "__init__.py").write_text(parser_init, encoding='utf-8')
    
    parser_content = generate_csv_parser(name, class_name)
    (parsers_dir / "csv_parser.py").write_text(parser_content, encoding='utf-8')
    
    if template == 'full':
        # Create context_builder.py
        context_content = generate_context_builder(name, class_name)
        (plugin_dir / "context_builder.py").write_text(context_content, encoding='utf-8')
        
        # Create chart_generator.py
        chart_content = generate_chart_generator(name, class_name)
        (plugin_dir / "chart_generator.py").write_text(chart_content, encoding='utf-8')
        
        # Create executor.py (for CLI integration)
        executor_content = generate_executor(name, safe_name, class_name)
        (plugin_dir / "executor.py").write_text(executor_content, encoding='utf-8')
        
        # Create widgets.py (custom UI components)
        widgets_content = generate_widgets_module(name, safe_name, class_name)
        (plugin_dir / "widgets.py").write_text(widgets_content, encoding='utf-8')
        
        # Create components.py (Property Controls pattern)
        components_content = generate_component_module(name, safe_name, class_name)
        (plugin_dir / "components.py").write_text(components_content, encoding='utf-8')
    
    # Create report_systems directory
    rs_dir = plugin_dir / "report_systems"
    rs_dir.mkdir(exist_ok=True)
    
    report_system = generate_report_system(name, safe_name, color_theme)
    (rs_dir / f"{safe_name}.json").write_text(
        json.dumps(report_system, indent=4), encoding='utf-8'
    )
    
    # Create templates directory
    templates_dir = plugin_dir / "templates" / safe_name / "pages"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Read and interpolate template files
    base_template = _read_template("pages/base.html.j2", name=name, safe_name=safe_name)
    (templates_dir / "base.html.j2").write_text(base_template, encoding='utf-8')
    
    home_template = _read_template("pages/overview.html.j2", name=name, safe_name=safe_name)
    (templates_dir / "overview.html.j2").write_text(home_template, encoding='utf-8')
    
    # Create details page for multi-page example
    details_template = _read_template("pages/details.html.j2", name=name, safe_name=safe_name)
    (templates_dir / "details.html.j2").write_text(details_template, encoding='utf-8')
    
    # Create summary page (for custom page registration demo)
    if template == 'full':
        summary_template = _generate_summary_template(name, safe_name)
        (templates_dir / "summary.html.j2").write_text(summary_template, encoding='utf-8')
    
    # Create components directory with macros
    components_dir = plugin_dir / "templates" / "components"
    components_dir.mkdir(parents=True, exist_ok=True)
    
    macros_template = _read_template("components/macros.html.j2", name=name, safe_name=safe_name)
    (components_dir / "macros.html.j2").write_text(macros_template, encoding='utf-8')
    
    # Create static CSS directory
    static_dir = plugin_dir / "templates" / safe_name / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Note: theme.css is NOT generated here - it's generated dynamically at runtime
    # based on the theme specified in the report system JSON or CLI --theme flag.
    # This ensures theme changes are always reflected without regenerating plugin files.
    
    # Generate plugin CSS (layout and components)
    plugin_css = _read_template("static/plugin.css", name=name, safe_name=safe_name)
    (static_dir / "plugin.css").write_text(plugin_css, encoding='utf-8')
    
    # Create analysis module (for full template)
    if template == 'full':
        analysis_content = generate_analysis_module(name, safe_name)
        (plugin_dir / "analysis.py").write_text(analysis_content, encoding='utf-8')
        
        # Create custom theme module
        theme_content = generate_theme_module(name, safe_name, class_name)
        (plugin_dir / "theme.py").write_text(theme_content, encoding='utf-8')
    
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
    
    # Create user-facing report_config.yaml
    # This is the CMS-style config that end users edit to compose reports
    user_config = generate_user_report_config(name, safe_name, color_theme)
    (plugin_dir / "report_config.yaml").write_text(user_config, encoding='utf-8')
    
    return plugin_dir


def _read_template(relative_path: str, **kwargs) -> str:
    """
    Read a template file and interpolate placeholders.
    
    Placeholders use {{key}} format (double braces to avoid
    conflicts with Jinja2 which uses single braces).
    
    Parameters:
        relative_path: Path relative to scaffolder/templates/
        **kwargs: Key-value pairs for placeholder substitution
    
    Returns:
        Template content with placeholders replaced
    """
    template_path = TEMPLATES_DIR / relative_path
    content = template_path.read_text(encoding='utf-8')
    
    # Replace {{key}} placeholders
    for key, value in kwargs.items():
        content = content.replace("{{" + key + "}}", value)
    
    return content


def _generate_summary_template(name: str, safe_name: str) -> str:
    """Generate summary.html.j2 template for custom page demo."""
    return f'''{{% extends "{safe_name}/pages/base.html.j2" %}}

{{% block title %}}{name} - Summary{{% endblock %}}

{{% block content %}}
<div class="summary-page">
    <h1>Summary</h1>
    <p class="page-intro">
        This page demonstrates how users can compose reports using plugin components.
        Pages are defined in <code>report_config.yaml</code>.
    </p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-card__title">Total Items</div>
            <div class="stat-card__value">{{{{ data_points | length }}}}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card__title">Average Score</div>
            <div class="stat-card__value">{{{{ "%.1f" | format(stats.score.mean | default(0)) }}}}</div>
        </div>
        <div class="stat-card">
            <div class="stat-card__title">Top Score</div>
            <div class="stat-card__value">{{{{ stats.score.max | default(0) }}}}</div>
        </div>
    </div>
    
    <div class="info-box">
        <h3>Define Pages in YAML</h3>
        <p>Users compose reports in <code>report_config.yaml</code>:</p>
        <pre><code>pages:
  - id: summary
    title: "Summary"
    components:
      - type: widget
        widget: {safe_name}_stat_card
      - type: chart
        chart: bar
        x: name
        y: score</code></pre>
    </div>
</div>
{{% endblock %}}
'''


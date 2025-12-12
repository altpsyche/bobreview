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

# Import via ThemeSystem for centralized theme access
from ...theme_system import get_theme_system
from ...themes import get_available_themes

# Import generators
from .generators import (
    generate_plugin_py,
    generate_csv_parser,
    generate_context_builder,
    generate_chart_generator,
    generate_analysis_module,
    generate_manifest,
    generate_report_system,
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

__all__ = ['{class_name}Plugin']
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
    
    home_template = _read_template("pages/home.html.j2", name=name, safe_name=safe_name)
    (templates_dir / "home.html.j2").write_text(home_template, encoding='utf-8')
    
    # Create details page for multi-page example
    details_template = _read_template("pages/details.html.j2", name=name, safe_name=safe_name)
    (templates_dir / "details.html.j2").write_text(details_template, encoding='utf-8')
    
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

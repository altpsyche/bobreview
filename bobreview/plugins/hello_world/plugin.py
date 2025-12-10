"""
Hello World Plugin - Main plugin class.

Demonstrates how to use PluginHelper for simplified registration.
"""

from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper
from bobreview.core.themes import ReportTheme

from .parsers.csv_parser import HelloCsvParser
from .context_builder import HelloContextBuilder
from .chart_generator import HelloChartGenerator


class HelloWorldPlugin(BasePlugin):
    """
    Example plugin demonstrating all BobReview extension points.
    
    This plugin:
    1. Parses CSV files with name, score, timestamp columns
    2. Calculates statistics per entry
    3. Generates LLM-powered summaries
    4. Renders interactive charts
    5. Outputs a multi-page HTML report
    """
    
    name = "hello-world"
    version = "1.0.0"
    author = "BobReview Team"
    description = "Complete example plugin demonstrating all core extension points"
    
    # Custom bright theme for demo reports
    HELLO_THEME = ReportTheme(
        id="hello_bright",
        name="Hello Bright",
        # Light background
        bg="#ffffff",
        bg_elevated="#f8f9fa",
        bg_soft="#e9ecef",
        # Blue accent
        accent="#0d6efd",
        accent_soft="rgba(13, 110, 253, 0.15)",
        accent_strong="#ffc107",
        # Dark text
        text_main="#212529",
        text_soft="#6c757d",
        # Status colors
        danger="#dc3545",
        danger_soft="rgba(220, 53, 69, 0.15)",
        warn="#ffc107",
        warn_soft="rgba(255, 193, 7, 0.15)",
        ok="#198754",
        ok_soft="rgba(25, 135, 84, 0.15)",
        # Borders and effects
        border_subtle="#dee2e6",
        shadow_soft="0 4px 12px rgba(0, 0, 0, 0.1)",
        radius_lg="12px",
        radius_md="8px",
    )
    
    def on_load(self, registry) -> None:
        """
        Register all plugin components using PluginHelper.
        
        This demonstrates the simplified registration API.
        """
        helper = PluginHelper(registry, self.name)
        
        # 1. Register data parser (for CSV files)
        helper.add_data_parser("hello_csv", HelloCsvParser)
        
        # 2. Register custom theme
        helper.add_theme(self.HELLO_THEME)
        
        # 3. Register templates directory
        template_dir = Path(__file__).parent / "templates"
        helper.add_templates(template_dir)
        
        # 4. Register context builder (adds custom data to templates)
        helper.add_context_builder("hello_world", HelloContextBuilder)
        
        # 5. Register chart generator
        helper.add_chart_generator("hello_world", HelloChartGenerator)
        
        # 6. Register report systems from JSON files
        report_systems_dir = Path(__file__).parent / "report_systems"
        helper.add_report_systems_from_dir(report_systems_dir)
        
        # 7. Auto-register default services if needed
        helper.register_default_services()
    
    def on_report_start(self, context: dict) -> None:
        """Called when report generation begins."""
        # Could initialize resources here
        pass
    
    def on_report_complete(self, result: dict) -> None:
        """Called when report generation completes."""
        # Could cleanup or log results here
        pass

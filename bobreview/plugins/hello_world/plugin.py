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
    
    # Custom Cyberpunk/Neon theme for demo reports
    # Demonstrates how plugins can create their own themes
    HELLO_THEME = ReportTheme(
        id="hello_cyberpunk",
        name="Cyberpunk Neon",
        # Deep dark with pink/cyan glow
        bg="#0a0a0f",
        bg_elevated="#13131a",
        bg_soft="#1a1a25",
        # Neon pink accent
        accent="#ff2d95",
        accent_soft="rgba(255, 45, 149, 0.15)",
        accent_strong="#00f0ff",  # Cyan highlight
        # Off-white text
        text_main="#e4e4f0",
        text_soft="#8888a0",
        # Status colors (neon style)
        danger="#ff3366",
        danger_soft="rgba(255, 51, 102, 0.15)",
        warn="#ffcc00",
        warn_soft="rgba(255, 204, 0, 0.15)",
        ok="#00ff88",
        ok_soft="rgba(0, 255, 136, 0.15)",
        # Borders and effects
        border_subtle="#2a2a3a",
        shadow_soft="0 0 30px rgba(255, 45, 149, 0.2), 0 0 60px rgba(0, 240, 255, 0.1)",
        radius_lg="8px",
        radius_md="4px",
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

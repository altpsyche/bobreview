"""
mayhem-reports Plugin - Main plugin class.

Provides performance analysis similar to MayhemAutomation but using
the new plugin patterns with PluginHelper and registry-based registration.

Components:
- PNG filename parser for performance data
- Performance-specific context builder
- Chart generator for histogram/timeline/scatter charts
- Performance analyzer function
- Built-in themes
"""

from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper
from .parsers import MayhemReportsParser
from .context_builder import MayhemReportsContextBuilder
from .chart_generator import MayhemReportsChartGenerator


class MayhemReportsPlugin(BasePlugin):
    """
    Plugin for game performance analysis.
    
    Analyzes PNG filenames with pattern: {testcase}_{tris}_{draws}_{timestamp}.png
    Generates reports with:
    - Performance overview with grade and budget bars
    - Quick statistics
    - Navigation to detailed analysis pages
    - LLM-generated insights
    """
    
    name = "mayhem-reports"
    version = "1.0.0"
    author = "BobReview Team"
    description = "Game performance analysis from PNG filename metadata"
    dependencies = []

    def on_load(self, registry) -> None:
        """Register all plugin components using PluginHelper."""
        config = self.get_config()
        helper = PluginHelper(registry, self.name)
        
        # 1. Register data parser for PNG filenames
        helper.add_data_parser("mayhem_reports_parser", MayhemReportsParser)
        
        # 2. Register context builder
        helper.add_context_builder("mayhem_reports", MayhemReportsContextBuilder)
        
        # 3. Register chart generator
        helper.add_chart_generator("mayhem_reports", MayhemReportsChartGenerator)
        
        # 4. Register templates
        template_dir = Path(__file__).parent / "templates"
        helper.add_templates(template_dir)
        
        # 5. Register report systems from JSON
        report_systems_dir = Path(__file__).parent / "report_systems"
        helper.add_report_systems_from_dir(report_systems_dir)
        
        # 6. Register default services
        # Note: Themes are registered by the first plugin that calls add_builtin_themes()
        # (typically MayhemAutomation). We don't need to register them again.
        if config.get('register_services', True):
            helper.register_default_services()
        
        # 8. Register analyzer function
        self._register_analyzer()
    
    def _register_analyzer(self) -> None:
        """Register the performance analyzer function."""
        from bobreview.core.plugin_system.registries import get_analyzer_registry
        from .analysis import analyze_performance_data
        
        analyzer_registry = get_analyzer_registry()
        analyzer_registry.register(
            'performance', 
            analyze_performance_data, 
            default=True
        )
    
    def on_report_start(self, context: dict) -> None:
        """Called when report generation begins."""
        pass
    
    def on_report_complete(self, result: dict) -> None:
        """Called when report generation completes."""
        pass

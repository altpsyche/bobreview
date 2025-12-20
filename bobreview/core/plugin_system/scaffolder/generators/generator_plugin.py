"""
Generator for plugin.py file.

Creates the main plugin class that registers components with the core registry.
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

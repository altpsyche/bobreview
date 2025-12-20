"""
Plugin helper for simplified component registration.

Plugin-First Architecture:
- Minimal helper for template and parser registration
- Themes are now plugin-owned entirely - not managed by core
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

if TYPE_CHECKING:
    from .registry import PluginRegistry


class PluginHelper:
    """
    Simplified registration facade for plugin development.
    
    Plugin-First Architecture:
    - Templates: Registered for discovery
    - Report Systems: Registered for loading
    - Data Parsers: Registered for parsing
    - Themes: Plugins handle internally (not managed by core)
    
    Example:
        class MyPlugin(BasePlugin):
            name = "my-plugin"
            
            def on_load(self, registry):
                helper = PluginHelper(registry, self.name)
                
                # Register templates
                helper.add_templates(Path(__file__).parent / "templates")
                
                # Register report systems
                helper.add_report_systems_from_dir(Path(__file__).parent / "report_systems")
    """
    
    def __init__(self, registry: 'PluginRegistry', plugin_name: str):
        """
        Initialize helper with registry and plugin name.
        
        Parameters:
            registry: PluginRegistry instance from on_load()
            plugin_name: Name of the plugin (for ownership tracking)
        """
        self.registry = registry
        self.plugin_name = plugin_name
    
    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------
    
    def add_templates(self, template_dir: Union[str, Path]) -> None:
        """
        Register a directory of Jinja2 templates.
        
        Templates will be discoverable by the template engine.
        
        Parameters:
            template_dir: Path to directory containing .html.j2 templates
        """
        self.registry.template_paths.register(str(template_dir), plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Data Parsing
    # -------------------------------------------------------------------------
    
    def add_data_parser(self, parser_id: str, parser_class: Type) -> None:
        """
        Register a data parser.
        
        Parameters:
            parser_id: Unique identifier (e.g., "csv", "json")
            parser_class: Parser class implementation
        """
        if not hasattr(parser_class, 'parser_name'):
            parser_class.parser_name = parser_id
        self.registry.data_parsers.register(parser_class, plugin_name=self.plugin_name)
    
    # -------------------------------------------------------------------------
    # Report Systems
    # -------------------------------------------------------------------------
    
    def add_report_system(self, system_id: str, system_def: Dict[str, Any]) -> None:
        """
        Register a report system from a dictionary definition.
        
        Parameters:
            system_id: Unique identifier for the report system
            system_def: Report system definition dict
        """
        self.registry.report_systems.register(system_id, system_def, plugin_name=self.plugin_name)
    
    def add_report_systems_from_dir(self, report_systems_dir: Union[str, Path]) -> List[str]:
        """
        Register all report systems from JSON files in a directory.
        
        Parameters:
            report_systems_dir: Directory containing report system JSON files
            
        Returns:
            List of registered system IDs
        """
        import json
        
        registered = []
        dir_path = Path(report_systems_dir)
        
        if not dir_path.exists():
            return registered
        
        for json_file in dir_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                system_id = data.get('id', json_file.stem)
                self.add_report_system(system_id, data)
                registered.append(system_id)
            except (json.JSONDecodeError, OSError):
                continue
        
        return registered
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    def setup_complete_report_system(
        self,
        system_id: str,
        system_def: Dict[str, Any],
        parser_class: Optional[Type] = None,
        template_dir: Optional[Union[str, Path]] = None,
        **kwargs  # Accept but ignore legacy parameters
    ) -> None:
        """
        Convenience method to register a report system with parser and templates.
        
        Plugin-First: Other components (analyzer, chart_generator, context_builder)
        should be handled internally by the plugin.
        
        Parameters:
            system_id: Unique identifier for the report system
            system_def: Report system definition dict
            parser_class: Optional data parser class
            template_dir: Optional templates directory
            **kwargs: Ignored (for backward compatibility)
        """
        # Register report system
        self.add_report_system(system_id, system_def)
        
        # Register parser if provided
        if parser_class:
            parser_type = system_def.get('data_source', {}).get('type', system_id)
            self.add_data_parser(parser_type, parser_class)
        
        # Register templates if provided
        if template_dir:
            self.add_templates(template_dir)

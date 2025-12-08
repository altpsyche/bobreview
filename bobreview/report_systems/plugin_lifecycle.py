"""
Plugin lifecycle manager for report systems.

Responsible for calling plugin lifecycle hooks during report generation.
"""

from typing import Dict, Any, List, Optional
from ..plugins import PluginLoader
from ..core import ReportConfig
from ..core.plugin_utils import safe_plugin_call


class PluginLifecycleManager:
    """
    Manages plugin lifecycle hooks during report generation.
    
    Single Responsibility: Plugin lifecycle management only.
    """
    
    def __init__(self, loader: PluginLoader):
        """
        Initialize plugin lifecycle manager.
        
        Parameters:
            loader: PluginLoader instance
        """
        self.loader = loader
    
    def get_loaded_plugins(self) -> List[Any]:
        """
        Get all loaded plugin instances.
        
        Returns:
            List of plugin instances
        """
        plugins = []
        # Use get_loaded_plugins() to get plugin info, then get instances
        plugin_infos = self.loader.get_loaded_plugins()
        for plugin_info in plugin_infos:
            if plugin_info.loaded:
                plugin_instance = self.loader.get_loaded_plugin(plugin_info.name)
                if plugin_instance:
                    plugins.append(plugin_instance)
        return plugins
    
    def call_report_start(self, context: Dict[str, Any], config: Optional[ReportConfig] = None) -> None:
        """
        Call on_report_start hook on all loaded plugins.
        
        Parameters:
            context: Report context dictionary
            config: Optional ReportConfig for logging
        """
        plugins = self.get_loaded_plugins()
        for plugin in plugins:
            safe_plugin_call(plugin, 'on_report_start', context, config=config)
    
    def call_report_complete(self, result: Dict[str, Any], config: Optional[ReportConfig] = None) -> None:
        """
        Call on_report_complete hook on all loaded plugins.
        
        Parameters:
            result: Report result dictionary
            config: Optional ReportConfig for logging
        """
        plugins = self.get_loaded_plugins()
        for plugin in plugins:
            safe_plugin_call(plugin, 'on_report_complete', result, config=config)


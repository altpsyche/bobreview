"""
Hello World Example Plugin for BobReview.

This plugin demonstrates how to create a BobReview plugin that:
1. Implements the BasePlugin interface
2. Registers a custom theme
3. Uses lifecycle hooks

Usage:
    1. Copy this folder to ~/.bobreview/plugins/
    2. Run: bob plugins list
    3. The plugin will be auto-loaded on next report generation
"""

from bobreview.plugins import BasePlugin, PluginRegistry


class HelloTheme:
    """A simple custom theme registered by the plugin."""
    
    name = "hello_theme"
    display_name = "Hello World Theme"
    
    # Theme colors (CSS variables)
    colors = {
        '--bg-primary': '#1a1a2e',
        '--bg-secondary': '#16213e',
        '--text-primary': '#eee',
        '--accent': '#e94560',
    }


class HelloWorldPlugin(BasePlugin):
    """
    Example plugin demonstrating the BobReview plugin system.
    
    This plugin registers a custom theme and logs lifecycle events.
    """
    
    name = "Hello World"
    version = "1.0.0"
    author = "BobReview Team"
    description = "Example plugin demonstrating the plugin system"
    dependencies = []
    
    def __init__(self):
        super().__init__()
    
    def on_load(self, registry: PluginRegistry) -> None:
        """
        Called when the plugin is loaded.
        
        Register components with the registry here.
        """
        print(f"[{self.name}] Plugin loaded!")
        
        # Register our custom theme
        registry.register_theme(HelloTheme(), plugin_name=self.name)
        
        print(f"[{self.name}] Registered theme: {HelloTheme.name}")
    
    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        print(f"[{self.name}] Plugin unloaded!")
    
    def on_report_start(self, context: dict) -> None:
        """Called when report generation begins."""
        print(f"[{self.name}] Report generation starting...")
    
    def on_report_complete(self, result: dict) -> None:
        """Called when report generation completes."""
        print(f"[{self.name}] Report generation complete!")


# For direct testing
if __name__ == "__main__":
    plugin = HelloWorldPlugin()
    print(f"Plugin: {plugin.name} v{plugin.version}")
    print(f"Author: {plugin.author}")
    print(f"Description: {plugin.description}")

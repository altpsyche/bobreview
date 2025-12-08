"""
Plugin manifest schema and validation.

The manifest.json file describes a plugin's metadata and capabilities.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


@dataclass
class PluginManifest:
    """
    Plugin manifest data from manifest.json.
    
    Example manifest.json:
        {
            "name": "my-plugin",
            "version": "1.0.0",
            "author": "Developer",
            "description": "Adds custom features",
            "entry_point": "plugin:MyPlugin",
            "dependencies": [],
            "provides": {
                "widgets": ["custom_widget"],
                "themes": ["dark_theme"]
            },
            "config_schema": {},
            "min_bobreview_version": "1.0.0"
        }
    """
    
    # Required fields
    name: str
    version: str
    entry_point: str  # Format: "module:ClassName"
    
    # Optional metadata
    author: str = "Unknown"
    description: str = ""
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    min_bobreview_version: str = "1.0.0"
    
    # What the plugin provides
    provides: Dict[str, List[str]] = field(default_factory=dict)
    
    # Plugin configuration schema (JSON Schema format)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Resolved path to the plugin directory
    plugin_path: Optional[Path] = None
    
    @classmethod
    def from_json(cls, data: Dict[str, Any], plugin_path: Optional[Path] = None) -> 'PluginManifest':
        """
        Create a PluginManifest from parsed JSON data.
        
        Parameters:
            data: Parsed manifest.json contents
            plugin_path: Path to the plugin directory
            
        Returns:
            PluginManifest instance
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required = ['name', 'version', 'entry_point']
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required fields in manifest: {missing}")
        
        # Handle provides - can be either a list (legacy format) or a dict
        provides_raw = data.get('provides', {})
        if isinstance(provides_raw, list):
            # Convert list format ["widgets", "themes"] to dict format {"widgets": [], "themes": []}
            # Legacy format: just lists the extension point types without specific items
            provides = {item: [] for item in provides_raw}
        elif isinstance(provides_raw, dict):
            provides = provides_raw
        else:
            provides = {}
        
        return cls(
            name=data['name'],
            version=data['version'],
            entry_point=data['entry_point'],
            author=data.get('author', 'Unknown'),
            description=data.get('description', ''),
            dependencies=data.get('dependencies', []),
            min_bobreview_version=data.get('min_bobreview_version', '1.0.0'),
            provides=provides,
            config_schema=data.get('config_schema', {}),
            plugin_path=plugin_path,
        )
    
    @classmethod
    def from_file(cls, manifest_path: Path) -> 'PluginManifest':
        """
        Load a PluginManifest from a manifest.json file.
        
        Parameters:
            manifest_path: Path to manifest.json
            
        Returns:
            PluginManifest instance
        """
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_json(data, plugin_path=manifest_path.parent)
    
    def get_module_and_class(self) -> tuple:
        """
        Parse entry_point into module and class name.
        
        Returns:
            Tuple of (module_name, class_name)
            
        Raises:
            ValueError: If entry_point format is invalid
        """
        if ':' not in self.entry_point:
            raise ValueError(
                f"Invalid entry_point format: {self.entry_point}. "
                "Expected 'module:ClassName'"
            )
        
        module_name, class_name = self.entry_point.split(':', 1)
        return module_name, class_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'entry_point': self.entry_point,
            'author': self.author,
            'description': self.description,
            'dependencies': self.dependencies,
            'min_bobreview_version': self.min_bobreview_version,
            'provides': self.provides,
            'config_schema': self.config_schema,
        }
    
    def __repr__(self) -> str:
        return f"<PluginManifest: {self.name} v{self.version}>"


def validate_manifest(manifest: PluginManifest) -> List[str]:
    """
    Validate a plugin manifest for common issues.
    
    Parameters:
        manifest: The manifest to validate
        
    Returns:
        List of warning/error messages (empty if valid)
    """
    issues = []
    
    # Check name format
    if not manifest.name:
        issues.append("Plugin name cannot be empty")
    elif not manifest.name.replace('-', '').replace('_', '').isalnum():
        issues.append(f"Plugin name should be alphanumeric with dashes/underscores: {manifest.name}")
    
    # Check version format (basic semver check)
    version_parts = manifest.version.split('.')
    if len(version_parts) < 2:
        issues.append(f"Version should follow semver format (e.g., 1.0.0): {manifest.version}")
    
    # Check entry point format
    try:
        manifest.get_module_and_class()
    except ValueError as e:
        issues.append(str(e))
    
    # Check provides format
    # Accept both hyphenated (manifest.json format) and underscore (Python format) names
    valid_extension_points = {
        'widgets', 'parsers', 'themes', 'charts', 'pages', 'llm_generators', 'services',
        'llm-generators', 'data-parsers', 'report-systems', 'templates',  # Hyphenated versions
        'data_parsers', 'report_systems', 'template_paths', 'chart-generators', 'chart_generators',
        'context-builders', 'context_builders'
    }
    for key in manifest.provides:
        if key not in valid_extension_points:
            issues.append(f"Unknown extension point in 'provides': {key}")
        if not isinstance(manifest.provides[key], list):
            issues.append(f"'provides.{key}' should be a list")
    
    return issues

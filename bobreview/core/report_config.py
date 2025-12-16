"""
User Report Configuration Schema for YAML-based Report Composition.

This module defines the schema for USER report configurations (YAML files).
End users create reports by composing plugin-provided components.

Components are validated by ComponentProcessor against plugin-defined schemas.
See core/components/ for the Property Controls pattern.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Literal
from dataclasses import dataclass, field
import yaml


# Note: Individual component configs (chart, widget, llm, data_table) are 
# now defined by plugins via Property Controls. See core/components/.


@dataclass
class UserPageConfig:
    """Configuration for a single page in a user report."""
    id: str
    title: str
    layout: Literal["grid", "flex", "single-column"] = "single-column"
    nav_order: int = 0
    enabled: bool = True
    # Components are Dict[str, Any] - validated by ComponentProcessor
    components: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UserConfig:
    """
    User-defined report configuration (YAML).
    
    This is the top-level schema for user report configs.
    Users create these as YAML files to define their reports.
    
    Example:
        name: "Performance Report"
        plugin: "performance-analyzer"
        data_source: "./data/*.csv"
        pages:
          - id: overview
            title: Overview
            components:
              - type: widget
                widget: stat_card
    """
    name: str
    plugin: str  # Plugin that provides the components
    data_source: str  # Path pattern for data files
    theme: str = "dark"
    output_dir: str = "./output"
    
    pages: List[UserPageConfig] = field(default_factory=list)
    
    # Plugin-specific config (overrides JSON extensions)
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Optional metadata
    version: str = "1.0"
    author: str = ""
    description: str = ""


def load_user_config(config_path: Union[str, Path]) -> UserConfig:
    """
    Load a user report configuration from a YAML file.
    
    Parameters:
        config_path: Path to the YAML configuration file
        
    Returns:
        Parsed UserConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Report config not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not data:
        raise ValueError(f"Empty config file: {path}")
    
    # Parse pages
    pages = []
    for page_data in data.get('pages', []):
        pages.append(UserPageConfig(
            id=page_data.get('id', ''),
            title=page_data.get('title', ''),
            layout=page_data.get('layout', 'single-column'),
            nav_order=page_data.get('nav_order', 0),
            enabled=page_data.get('enabled', True),
            components=page_data.get('components', [])
        ))
    
    return UserConfig(
        name=data.get('name', 'Untitled Report'),
        plugin=data.get('plugin', ''),
        data_source=data.get('data_source', ''),
        theme=data.get('theme', 'dark'),
        output_dir=data.get('output_dir', './output'),
        pages=pages,
        config=data.get('config', {}),  # Plugin-specific config
        version=data.get('version', '1.0'),
        author=data.get('author', ''),
        description=data.get('description', '')
    )


def validate_user_config(config: UserConfig) -> List[str]:
    """
    Validate a user report configuration.
    
    Parameters:
        config: UserConfig to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    if not config.name:
        errors.append("Report 'name' is required")
    
    if not config.plugin:
        errors.append("Report 'plugin' is required - specifies which plugin provides components")
    
    if not config.data_source:
        errors.append("Report 'data_source' is required - path to data files")
    
    if not config.pages:
        errors.append("Report must have at least one page")
    
    # Validate pages
    page_ids = set()
    for page in config.pages:
        if not page.id:
            errors.append("Page is missing 'id'")
        elif page.id in page_ids:
            errors.append(f"Duplicate page id: {page.id}")
        else:
            page_ids.add(page.id)
        
        if not page.title:
            errors.append(f"Page '{page.id}' is missing 'title'")
        
        # Validate components - only structural validation here
        # Component-specific validation is done by ComponentProcessor using plugin PropTypes
        for i, comp in enumerate(page.components):
            comp_type = comp.get('type', '')
            
            if not comp_type:
                errors.append(f"Page '{page.id}' component {i} missing 'type'")
    
    return errors


def save_user_config(config: UserConfig, output_path: Union[str, Path]) -> None:
    """
    Save a user report configuration to a YAML file.
    
    Parameters:
        config: UserConfig to save
        output_path: Path to save the YAML file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    data = {
        'name': config.name,
        'plugin': config.plugin,
        'data_source': config.data_source,
        'theme': config.theme,
        'output_dir': config.output_dir,
        'version': config.version,
        'pages': []
    }
    
    if config.author:
        data['author'] = config.author
    if config.description:
        data['description'] = config.description
    
    if config.config:
        data['config'] = config.config
    
    for page in config.pages:
        page_data = {
            'id': page.id,
            'title': page.title,
            'layout': page.layout,
            'nav_order': page.nav_order,
            'components': page.components
        }
        if not page.enabled:
            page_data['enabled'] = False
        data['pages'].append(page_data)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

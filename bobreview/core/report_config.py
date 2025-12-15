"""
User Report Configuration Schema for YAML-based Report Composition.

This module defines the schema for USER report configurations (YAML files).
End users create reports by composing plugin-provided components.

IMPORTANT: These classes are prefixed with "User" to distinguish from
internal config classes in config_classes.py and engine/schema.py.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Literal
from dataclasses import dataclass, field
import yaml


@dataclass
class UserComponentConfig:
    """Base configuration for a component in a user page."""
    type: Literal["widget", "chart", "data_table", "llm", "custom"]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserWidgetConfig(UserComponentConfig):
    """Configuration for a widget component."""
    type: Literal["widget"] = "widget"
    widget: str = ""  # Widget ID from plugin registry
    

@dataclass  
class UserChartConfig(UserComponentConfig):
    """Configuration for a chart component."""
    type: Literal["chart"] = "chart"
    chart: str = "bar"  # Chart type: bar, line, scatter, histogram, gauge
    title: str = ""
    x: Optional[str] = None  # X-axis field
    y: Optional[str] = None  # Y-axis field


@dataclass
class UserDataTableConfig(UserComponentConfig):
    """Configuration for a data table component."""
    type: Literal["data_table"] = "data_table"
    columns: List[str] = field(default_factory=list)
    sortable: bool = True
    paginated: bool = False
    page_size: int = 25


@dataclass
class UserLLMConfig(UserComponentConfig):
    """Configuration for an LLM-generated content component."""
    type: Literal["llm"] = "llm"
    generator: str = ""  # LLM generator ID from plugin
    prompt_override: Optional[str] = None


@dataclass
class UserPageConfig:
    """Configuration for a single page in a user report."""
    id: str
    title: str
    layout: Literal["grid", "flex", "single-column"] = "single-column"
    nav_order: int = 0
    enabled: bool = True
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
            errors.append(f"Page is missing 'id'")
        elif page.id in page_ids:
            errors.append(f"Duplicate page id: {page.id}")
        else:
            page_ids.add(page.id)
        
        if not page.title:
            errors.append(f"Page '{page.id}' is missing 'title'")
        
        # Validate components
        for i, comp in enumerate(page.components):
            comp_type = comp.get('type', '')
            
            if not comp_type:
                errors.append(f"Page '{page.id}' component {i} missing 'type'")
                continue
            
            # Chart validation
            if comp_type == 'chart':
                chart_type = comp.get('chart', 'bar')
                # Most charts need x and y fields
                if chart_type in ['bar', 'line', 'scatter', 'doughnut']:
                    if not comp.get('x'):
                        errors.append(f"Page '{page.id}' chart '{comp.get('title', i)}' missing 'x' field")
                    if not comp.get('y'):
                        errors.append(f"Page '{page.id}' chart '{comp.get('title', i)}' missing 'y' field")
                elif chart_type == 'histogram':
                    # Histogram only needs y field
                    if not comp.get('y'):
                        errors.append(f"Page '{page.id}' histogram '{comp.get('title', i)}' missing 'y' field")
            
            # LLM validation
            elif comp_type == 'llm':
                # Must have either 'prompt' (inline) or 'generator' (reference)
                if not comp.get('prompt') and not comp.get('generator'):
                    errors.append(f"Page '{page.id}' LLM component {i} needs 'prompt' or 'generator'")
            
            # Widget validation  
            elif comp_type == 'widget':
                if not comp.get('widget'):
                    errors.append(f"Page '{page.id}' widget {i} missing 'widget' type")
    
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

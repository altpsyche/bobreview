"""
Chart configuration registry for modular Chart.js setup.

This module provides a registry pattern for chart configurations,
with dataset styles and chart type definitions. Chart colors are
pulled directly from the report theme registry.
"""

from dataclasses import dataclass
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .themes import ReportTheme


@dataclass
class ChartDataset:
    """
    Defines a dataset style for charts.
    
    Attributes:
        id: Unique identifier (e.g., 'draws', 'tris')
        label: Display label
        primary_color: Main color (rgba format)
        secondary_color: Border/accent color
        point_radius: Size of data points (for line charts)
        tension: Line tension (0 = straight, 1 = curved)
    """
    id: str
    label: str
    primary_color: str
    secondary_color: str = ''
    point_radius: int = 4
    tension: float = 0.2
    
    def __post_init__(self):
        if not self.secondary_color:
            self.secondary_color = self.primary_color


@dataclass
class ChartConfig:
    """
    Complete chart configuration.
    
    Attributes:
        id: Unique identifier for this chart config
        chart_type: Chart.js type ('line', 'bar', 'scatter', etc.)
        aspect_ratio: Width/height ratio
        show_legend: Whether to display legend
        x_axis_label: Label for X axis
        y_axis_label: Label for Y axis
        begin_at_zero: Whether Y axis starts at 0
    """
    id: str
    chart_type: str
    aspect_ratio: float = 2.5
    show_legend: bool = False
    x_axis_label: str = ''
    y_axis_label: str = ''
    begin_at_zero: bool = True


# Global registries
_DATASET_REGISTRY: Dict[str, ChartDataset] = {}
_CHART_REGISTRY: Dict[str, ChartConfig] = {}


def register_dataset(dataset: ChartDataset) -> None:
    """Register a dataset style."""
    _DATASET_REGISTRY[dataset.id] = dataset


def register_chart(config: ChartConfig) -> None:
    """Register a chart configuration."""
    _CHART_REGISTRY[config.id] = config


def get_dataset(dataset_id: str) -> Optional[ChartDataset]:
    """Get a dataset style by ID."""
    return _DATASET_REGISTRY.get(dataset_id)


def get_chart(chart_id: str) -> Optional[ChartConfig]:
    """Get a chart config by ID."""
    return _CHART_REGISTRY.get(chart_id)


def _get_grid_color_with_opacity(hex_color: str, opacity: float) -> str:
    """Apply opacity to hex color as hex alpha."""
    alpha_hex = format(int(opacity * 255), '02x')
    color = hex_color.lstrip('#')
    if len(color) == 6:
        return f'#{color}{alpha_hex}'
    return hex_color


def get_chart_defaults_js(theme_id: str = 'dark') -> str:
    """
    Generate JavaScript code for Chart.js defaults.
    
    Uses colors from the report theme registry.
    
    Parameters:
        theme_id: Report theme ID
    
    Returns:
        JavaScript string to set Chart.defaults
    """
    from .themes import get_theme
    theme = get_theme(theme_id)
    
    # Escape single quotes in font family for JS string
    font_escaped = theme.font_sans.replace("'", "\\'")
    
    return f"""
        Chart.defaults.color = '{theme.text_soft}';
        Chart.defaults.borderColor = '{theme.border_subtle}';
        Chart.defaults.font.family = '{font_escaped}';
        Chart.defaults.font.size = 12;
    """


def get_scale_options_js(config: ChartConfig, theme_id: str = 'dark') -> str:
    """
    Generate JavaScript for Chart.js scale options.
    
    Uses colors from the report theme registry.
    
    Parameters:
        config: Chart configuration
        theme_id: Report theme ID
    
    Returns:
        JavaScript object string for scales config
    """
    from .themes import get_theme
    theme = get_theme(theme_id)
    
    grid_color = _get_grid_color_with_opacity(theme.border_subtle, theme.chart_grid_opacity)
    
    x_title = f"display: true, text: '{config.x_axis_label}', color: '{theme.text_soft}'" if config.x_axis_label else "display: false"
    y_title = f"display: true, text: '{config.y_axis_label}', color: '{theme.text_soft}'" if config.y_axis_label else "display: false"
    
    return f"""{{
        x: {{
          title: {{ {x_title} }},
          grid: {{ color: '{grid_color}' }}
        }},
        y: {{
          title: {{ {y_title} }},
          grid: {{ color: '{grid_color}' }},
          beginAtZero: {'true' if config.begin_at_zero else 'false'}
        }}
      }}"""


# Register standard dataset styles
register_dataset(ChartDataset(
    id='draws',
    label='Draw Calls',
    primary_color='rgba(78, 161, 255, 0.8)',
    secondary_color='rgba(78, 161, 255, 1)',
    point_radius=4,
    tension=0.2
))

register_dataset(ChartDataset(
    id='tris',
    label='Triangles',
    primary_color='rgba(255, 159, 28, 0.8)',
    secondary_color='rgba(255, 159, 28, 1)',
    point_radius=4,
    tension=0.2
))

register_dataset(ChartDataset(
    id='histogram_draws',
    label='Frequency',
    primary_color='rgba(78, 161, 255, 0.6)',
    secondary_color='rgba(78, 161, 255, 1)'
))

register_dataset(ChartDataset(
    id='histogram_tris',
    label='Frequency',
    primary_color='rgba(255, 159, 28, 0.6)',
    secondary_color='rgba(255, 159, 28, 1)'
))

# Register standard chart configurations
register_chart(ChartConfig(
    id='timeline_draws',
    chart_type='line',
    aspect_ratio=2.5,
    x_axis_label='Capture Index',
    y_axis_label='Draw Calls'
))

register_chart(ChartConfig(
    id='timeline_tris',
    chart_type='line',
    aspect_ratio=2.5,
    x_axis_label='Capture Index',
    y_axis_label='Triangles'
))

register_chart(ChartConfig(
    id='scatter_correlation',
    chart_type='scatter',
    aspect_ratio=1.5,
    x_axis_label='Draw Calls',
    y_axis_label='Triangles'
))

register_chart(ChartConfig(
    id='histogram_draws',
    chart_type='bar',
    aspect_ratio=2.5,
    x_axis_label='Draw Calls (bin center)',
    y_axis_label='Frequency'
))

register_chart(ChartConfig(
    id='histogram_tris',
    chart_type='bar',
    aspect_ratio=2.5,
    x_axis_label='Triangles (bin center)',
    y_axis_label='Frequency'
))

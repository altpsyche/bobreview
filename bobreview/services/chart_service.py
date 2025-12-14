"""
Chart service for generating Chart.js configurations.

This service handles chart generation:
- Timeline charts
- Distribution histograms
- Scatter plots
- Performance zone coloring
"""

from typing import List, Dict, Any, Optional, Tuple, Union, TYPE_CHECKING
import json
import logging

from .base import BaseService, ChartServiceError

if TYPE_CHECKING:
    from ..core.dataframe import DataFrame

logger = logging.getLogger(__name__)


class ChartService(BaseService):
    """
    Service for generating Chart.js chart configurations.
    
    Extracted from ReportSystemExecutor._generate_charts() to enable:
    - Independent testing
    - Plugin replacement with custom chart types
    - Easier theme integration
    
    Example:
        service = ChartService(theme=get_theme())
        charts = service.generate_page_charts(
            data=data,  # DataFrame or List[Dict]
            page_type='visuals',
            thresholds={'high_draw': 600, 'low_draw': 400}
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize chart service."""
        super().__init__(config)
        self._theme = None
        self._chart_types: Dict[str, type] = {}
    
    @property
    def theme(self):
        """Get current theme, loading default if not set."""
        if self._theme is None:
            from ..core.theme_utils import get_theme
            self._theme = get_theme()
        return self._theme
    
    def set_theme(self, theme) -> None:
        """Set the theme for chart colors."""
        self._theme = theme
    
    def hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get commonly used colors from theme."""
        theme = self.theme
        return {
            'danger': self.hex_to_rgba(theme.danger, 0.9),
            'danger_soft': self.hex_to_rgba(theme.danger, 0.7),
            'danger_bg': self.hex_to_rgba(theme.danger, 0.8),
            'ok': self.hex_to_rgba(theme.ok, 0.9),
            'ok_soft': self.hex_to_rgba(theme.ok, 0.7),
            'ok_bg': self.hex_to_rgba(theme.ok, 0.8),
            'warn': self.hex_to_rgba(theme.warn, 0.9),
            'warn_soft': self.hex_to_rgba(theme.warn, 0.7),
            'accent_top': self.hex_to_rgba(theme.accent, 0.4),
            'accent_bottom': self.hex_to_rgba(theme.accent, 0.02),
            'accent_strong_top': self.hex_to_rgba(theme.accent_strong, 0.4),
            'accent_strong_bottom': self.hex_to_rgba(theme.accent_strong, 0.02),
            'grid': self.hex_to_rgba(theme.border_subtle, 0.5),
            'grid_light': self.hex_to_rgba(theme.border_subtle, 0.3),
            'tooltip_bg': self.hex_to_rgba(theme.bg_elevated, 0.95),
        }
    
    def get_point_color(
        self,
        value: float,
        high_threshold: float,
        low_threshold: float
    ) -> str:
        """
        Get color for a data point based on performance zone.
        
        Parameters:
            value: The data point value
            high_threshold: Threshold for danger zone
            low_threshold: Threshold for safe zone
            
        Returns:
            RGBA color string
        """
        colors = self.get_theme_colors()
        
        if value >= high_threshold:
            return colors['danger']
        elif value < low_threshold:
            return colors['ok']
        else:
            return colors['warn']
    
    def generate_timeline_chart(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        value_field: str,
        high_threshold: float,
        low_threshold: float,
        chart_id: str,
        label: str = 'Value',
        x_label: str = 'Frame Index',
        y_label: str = 'Value'
    ) -> str:
        """
        Generate a timeline chart with performance zone coloring.
        
        Parameters:
            data: DataFrame or List[Dict] with data points
            value_field: Field name for y-axis values
            high_threshold: High-load threshold
            low_threshold: Low-load threshold
            chart_id: HTML canvas element ID
            label: Dataset label
            x_label: X-axis label
            y_label: Y-axis label
            
        Returns:
            JavaScript code for Chart.js
        """
        # Convert DataFrame to list for internal use
        data_points = list(data) if hasattr(data, '__iter__') else data
        
        colors = self.get_theme_colors()
        
        # Build data with colors
        points = []
        for i, p in enumerate(data_points):
            value = p.get(value_field, 0)
            testcase = p.get('testcase', f'Frame {i}')
            color = self.get_point_color(value, high_threshold, low_threshold)
            points.append({
                'x': i,
                'y': value,
                'color': color,
                'testcase': testcase
            })
        
        data_json = json.dumps(points)
        
        return f"""
// {label} Timeline with Performance Zones
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const data = {data_json};
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{colors['accent_top']}');
    gradient.addColorStop(1, '{colors['accent_bottom']}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: '{label}',
                data: data.map(p => ({{x: p.x, y: p.y}})),
                borderColor: data.map(p => p.color),
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointBackgroundColor: data.map(p => p.color),
                pointBorderColor: data.map(p => p.color),
                segment: {{
                    borderColor: ctx => {{
                        const idx = ctx.p1DataIndex;
                        return data[idx] ? data[idx].color : '{colors['warn']}';
                    }}
                }}
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    backgroundColor: '{colors['tooltip_bg']}',
                    callbacks: {{
                        title: ctx => data[ctx[0].dataIndex]?.testcase || '',
                        label: ctx => '{label}: ' + ctx.parsed.y.toLocaleString()
                    }}
                }}
            }},
            scales: {{
                x: {{
                    type: 'linear',
                    title: {{ display: true, text: '{x_label}' }},
                    grid: {{ color: '{colors['grid_light']}' }}
                }},
                y: {{
                    title: {{ display: true, text: '{y_label}' }},
                    grid: {{ color: '{colors['grid']}' }}
                }}
            }}
        }}
    }});
}})();
"""
    
    def generate_histogram_chart(
        self,
        values: List[float],
        chart_id: str,
        high_threshold: Optional[float] = None,
        low_threshold: Optional[float] = None,
        num_bins: int = 15,
        label: str = 'Value',
        x_label: str = 'Value',
        y_label: str = 'Frequency'
    ) -> str:
        """
        Generate a histogram chart with performance zone coloring.
        
        Parameters:
            values: List of values to histogram
            chart_id: HTML canvas element ID
            high_threshold: High-load threshold for coloring
            low_threshold: Low-load threshold for coloring
            num_bins: Number of histogram bins
            label: Dataset label
            
        Returns:
            JavaScript code for Chart.js
        """
        if not values:
            return f"// No data for {chart_id}"
        
        colors = self.get_theme_colors()
        
        # Compute histogram
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1
        
        bins = [0] * num_bins
        bin_edges = []
        
        for i in range(num_bins):
            edge = min_val + (i * bin_width)
            bin_edges.append(edge)
        bin_edges.append(max_val)
        
        for v in values:
            if v == max_val:
                bins[-1] += 1
            else:
                bin_idx = int((v - min_val) / bin_width)
                if 0 <= bin_idx < num_bins:
                    bins[bin_idx] += 1
        
        # Color bins by zone
        bin_colors = []
        for i in range(num_bins):
            center = bin_edges[i] + (bin_width / 2)
            if high_threshold and center >= high_threshold:
                bin_colors.append(colors['danger_bg'])
            elif low_threshold and center < low_threshold:
                bin_colors.append(colors['ok_bg'])
            else:
                bin_colors.append(colors['warn_soft'])
        
        labels_json = json.dumps([f"{bin_edges[i]:.0f}" for i in range(num_bins)])
        data_json = json.dumps(bins)
        colors_json = json.dumps(bin_colors)
        
        return f"""
// {label} Distribution Histogram
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {labels_json},
            datasets: [{{
                label: '{label}',
                data: {data_json},
                backgroundColor: {colors_json},
                borderWidth: 0,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }}
            }},
            scales: {{
                x: {{
                    title: {{ display: true, text: '{x_label}' }},
                    grid: {{ display: false }}
                }},
                y: {{
                    title: {{ display: true, text: '{y_label}' }},
                    grid: {{ color: '{colors['grid']}' }}
                }}
            }}
        }}
    }});
}})();
"""
    
    def generate_scatter_chart(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        x_field: str,
        y_field: str,
        chart_id: str,
        x_high: float,
        y_high: float,
        x_low: float,
        y_low: float,
        x_label: str = 'X',
        y_label: str = 'Y'
    ) -> str:
        """
        Generate a scatter plot with performance zone coloring.
        
        Parameters:
            data: DataFrame or List[Dict] with data points
            x_field: Field for x-axis
            y_field: Field for y-axis
            chart_id: HTML canvas element ID
            x_high/y_high: High thresholds
            x_low/y_low: Low thresholds
            
        Returns:
            JavaScript code for Chart.js
        """
        # Convert DataFrame to list for internal use
        data_points = list(data) if hasattr(data, '__iter__') else data
        
        colors = self.get_theme_colors()
        
        points = []
        for i, p in enumerate(data_points):
            x = p.get(x_field, 0)
            y = p.get(y_field, 0)
            testcase = p.get('testcase', f'Point {i}')
            
            # Color based on worst metric
            if x >= x_high or y >= y_high:
                color = colors['danger_bg']
            elif x < x_low and y < y_low:
                color = colors['ok_bg']
            else:
                color = colors['warn_soft']
            
            points.append({
                'x': x,
                'y': y,
                'color': color,
                'testcase': testcase
            })
        
        data_json = json.dumps(points)
        
        return f"""
// Scatter Plot: {x_label} vs {y_label}
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const data = {data_json};
    
    new Chart(ctx, {{
        type: 'scatter',
        data: {{
            datasets: [{{
                label: 'Data Points',
                data: data.map(p => ({{x: p.x, y: p.y}})),
                backgroundColor: data.map(p => p.color),
                pointRadius: 6,
                pointHoverRadius: 8
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        title: ctx => data[ctx[0].dataIndex]?.testcase || '',
                        label: ctx => `{x_label}: ${{ctx.parsed.x}}, {y_label}: ${{ctx.parsed.y}}`
                    }}
                }}
            }},
            scales: {{
                x: {{
                    title: {{ display: true, text: '{x_label}' }},
                    grid: {{ color: '{colors['grid']}' }}
                }},
                y: {{
                    title: {{ display: true, text: '{y_label}' }},
                    grid: {{ color: '{colors['grid']}' }}
                }}
            }}
        }}
    }});
}})();
"""

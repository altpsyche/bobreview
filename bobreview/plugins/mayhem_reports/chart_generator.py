"""
Chart Generator for mayhem-reports Plugin.

Generates Chart.js configurations for performance visualization:
- Histogram charts for draws/tris distribution
- Timeline charts for performance over time
- Scatter plots for correlation analysis
- Bar charts for score comparisons

Implements ChartGeneratorInterface from core.api.
"""

import json
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface


class MayhemReportsChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js configurations for performance reports."""
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate a Chart.js configuration.
        
        Parameters:
            data_points: List of parsed data points
            stats: Statistical analysis results
            config: ReportConfig
            chart_config: Chart-specific configuration with type, title, fields
        
        Returns:
            JSON string with Chart.js configuration
        """
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'draws')
        x_field = chart_config.get('x_field', 'index')
        
        if chart_type == 'histogram':
            return self._generate_histogram(data_points, stats, y_field, title)
        elif chart_type == 'timeline':
            return self._generate_timeline(data_points, stats, y_field, title)
        elif chart_type == 'scatter':
            return self._generate_scatter(data_points, stats, x_field, y_field, title)
        else:
            return self._generate_bar(data_points, stats, x_field, y_field, title)
    
    def _generate_bar(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        x_field: str,
        y_field: str,
        title: str
    ) -> str:
        """Generate bar chart configuration."""
        # Sort by y_field descending
        sorted_data = sorted(data_points, key=lambda x: x.get(y_field, 0), reverse=True)
        
        labels = []
        values = []
        for i, d in enumerate(sorted_data[:20]):  # Limit to top 20
            label = d.get('testcase') or d.get('name') or f"#{i+1}"
            labels.append(label)
            values.append(d.get(y_field, 0))
        
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': title,
                    'data': values,
                    'backgroundColor': 'rgba(233, 69, 96, 0.8)',
                    'borderColor': 'rgba(233, 69, 96, 1)',
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'color': '#e8e8e8'
                    },
                    'legend': {
                        'labels': {'color': '#a0a0a0'}
                    }
                },
                'scales': {
                    'x': {
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    },
                    'y': {
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def _generate_histogram(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        field: str,
        title: str
    ) -> str:
        """Generate histogram chart configuration."""
        values = [d.get(field, 0) for d in data_points]
        
        if not values:
            return json.dumps({'type': 'bar', 'data': {'labels': [], 'datasets': []}})
        
        # Create histogram bins
        min_val = min(values)
        max_val = max(values)
        num_bins = min(20, len(set(values)))
        if num_bins < 2:
            num_bins = 2
        
        bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1
        bins = [0] * num_bins
        labels = []
        
        for v in values:
            bin_idx = min(int((v - min_val) / bin_width), num_bins - 1)
            bins[bin_idx] += 1
        
        for i in range(num_bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            labels.append(f"{int(bin_start)}-{int(bin_end)}")
        
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': f'{title} Distribution',
                    'data': bins,
                    'backgroundColor': 'rgba(99, 179, 237, 0.7)',
                    'borderColor': 'rgba(99, 179, 237, 1)',
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'color': '#e8e8e8'
                    }
                },
                'scales': {
                    'x': {
                        'title': {'display': True, 'text': field.title(), 'color': '#a0a0a0'},
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    },
                    'y': {
                        'title': {'display': True, 'text': 'Frequency', 'color': '#a0a0a0'},
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def _generate_timeline(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        field: str,
        title: str
    ) -> str:
        """Generate timeline chart configuration."""
        labels = [str(i) for i in range(len(data_points))]
        values = [d.get(field, 0) for d in data_points]
        
        # Get threshold line if available
        annotations = {}
        field_stats = stats.get(field, {})
        if field_stats:
            mean_val = field_stats.get('mean', 0)
            annotations = {
                'meanLine': {
                    'type': 'line',
                    'yMin': mean_val,
                    'yMax': mean_val,
                    'borderColor': 'rgba(255, 193, 7, 0.8)',
                    'borderWidth': 2,
                    'borderDash': [5, 5],
                    'label': {
                        'display': True,
                        'content': f'Mean: {int(mean_val)}',
                        'color': '#ffc107'
                    }
                }
            }
        
        chart_data = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': title,
                    'data': values,
                    'borderColor': 'rgba(233, 69, 96, 1)',
                    'backgroundColor': 'rgba(233, 69, 96, 0.1)',
                    'fill': True,
                    'tension': 0.1
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'color': '#e8e8e8'
                    },
                    'annotation': {
                        'annotations': annotations
                    } if annotations else {}
                },
                'scales': {
                    'x': {
                        'title': {'display': True, 'text': 'Frame Index', 'color': '#a0a0a0'},
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    },
                    'y': {
                        'title': {'display': True, 'text': field.title(), 'color': '#a0a0a0'},
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def _generate_scatter(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        x_field: str,
        y_field: str,
        title: str
    ) -> str:
        """Generate scatter plot configuration."""
        scatter_data = [
            {'x': d.get(x_field, 0), 'y': d.get(y_field, 0)}
            for d in data_points
        ]
        
        chart_data = {
            'type': 'scatter',
            'data': {
                'datasets': [{
                    'label': title,
                    'data': scatter_data,
                    'backgroundColor': 'rgba(99, 179, 237, 0.6)',
                    'borderColor': 'rgba(99, 179, 237, 1)',
                    'pointRadius': 4
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'color': '#e8e8e8'
                    }
                },
                'scales': {
                    'x': {
                        'title': {'display': True, 'text': x_field.title(), 'color': '#a0a0a0'},
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    },
                    'y': {
                        'title': {'display': True, 'text': y_field.title(), 'color': '#a0a0a0'},
                        'ticks': {'color': '#a0a0a0'},
                        'grid': {'color': 'rgba(255, 255, 255, 0.1)'}
                    }
                }
            }
        }
        
        return json.dumps(chart_data)

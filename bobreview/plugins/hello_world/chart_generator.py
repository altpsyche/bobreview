"""
Chart Generator for Hello World Plugin.

Implements ChartGeneratorInterface to create Chart.js configurations.
"""

import json
from typing import Dict, List, Any

from bobreview.core.api import ChartGeneratorInterface


class HelloChartGenerator(ChartGeneratorInterface):
    """
    Generate Chart.js configurations for Hello World reports.
    
    Supports chart types:
    - bar: Score comparison bar chart
    - line: Score timeline
    - doughnut: Category distribution
    """
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate a Chart.js configuration.
        
        Returns JSON string for embedding in templates.
        """
        chart_type = chart_config.get('type', 'bar')
        chart_id = chart_config.get('id', 'chart')
        
        if chart_type == 'bar':
            return self._generate_bar_chart(data_points, chart_config)
        elif chart_type == 'line':
            return self._generate_line_chart(data_points, chart_config)
        elif chart_type == 'doughnut':
            return self._generate_doughnut_chart(data_points, chart_config)
        else:
            return self._generate_bar_chart(data_points, chart_config)
    
    def _generate_bar_chart(
        self,
        data_points: List[Dict[str, Any]],
        chart_config: Dict[str, Any]
    ) -> str:
        """Generate a bar chart showing scores by name."""
        # Sort by score descending
        sorted_data = sorted(data_points, key=lambda x: x.get('score', 0), reverse=True)
        
        labels = [d.get('name', 'Unknown') for d in sorted_data]
        values = [d.get('score', 0) for d in sorted_data]
        
        # Color based on score
        colors = []
        for score in values:
            if score >= 90:
                colors.append('rgba(25, 135, 84, 0.8)')  # Green
            elif score >= 70:
                colors.append('rgba(255, 193, 7, 0.8)')  # Yellow
            else:
                colors.append('rgba(220, 53, 69, 0.8)')  # Red
        
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': chart_config.get('title', 'Scores'),
                    'data': values,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'legend': {'display': False},
                    'title': {
                        'display': True,
                        'text': chart_config.get('title', 'Score Comparison')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'title': {'display': True, 'text': 'Score'}
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def _generate_line_chart(
        self,
        data_points: List[Dict[str, Any]],
        chart_config: Dict[str, Any]
    ) -> str:
        """Generate a line chart showing scores over time."""
        # Sort by timestamp
        sorted_data = sorted(data_points, key=lambda x: x.get('timestamp', 0))
        
        from datetime import datetime
        labels = []
        for d in sorted_data:
            ts = d.get('timestamp', 0)
            try:
                dt = datetime.fromtimestamp(ts)
                labels.append(dt.strftime('%Y-%m-%d'))
            except (OSError, OverflowError, ValueError):
                labels.append(d.get('name', 'Unknown'))
        
        values = [d.get('score', 0) for d in sorted_data]
        
        chart_data = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Score',
                    'data': values,
                    'borderColor': 'rgba(13, 110, 253, 1)',
                    'backgroundColor': 'rgba(13, 110, 253, 0.1)',
                    'fill': True,
                    'tension': 0.3
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': chart_config.get('title', 'Score Timeline')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'title': {'display': True, 'text': 'Score'}
                    }
                }
            }
        }
        
        return json.dumps(chart_data)
    
    def _generate_doughnut_chart(
        self,
        data_points: List[Dict[str, Any]],
        chart_config: Dict[str, Any]
    ) -> str:
        """Generate a doughnut chart showing score category distribution."""
        excellent = len([d for d in data_points if d.get('score', 0) >= 90])
        good = len([d for d in data_points if 70 <= d.get('score', 0) < 90])
        needs_improvement = len([d for d in data_points if d.get('score', 0) < 70])
        
        chart_data = {
            'type': 'doughnut',
            'data': {
                'labels': ['Excellent (90+)', 'Good (70-89)', 'Needs Work (<70)'],
                'datasets': [{
                    'data': [excellent, good, needs_improvement],
                    'backgroundColor': [
                        'rgba(25, 135, 84, 0.8)',
                        'rgba(255, 193, 7, 0.8)',
                        'rgba(220, 53, 69, 0.8)'
                    ],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': chart_config.get('title', 'Score Distribution')
                    },
                    'legend': {
                        'position': 'bottom'
                    }
                }
            }
        }
        
        return json.dumps(chart_data)

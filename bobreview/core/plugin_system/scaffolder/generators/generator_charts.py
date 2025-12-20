"""
Generator for chart_generator.py file.

Creates the Chart.js chart generator with theme support.
"""


def generate_chart_generator(name: str, class_name: str) -> str:
    """Generate chart generator file with theme support."""
    return '''"""
Chart Generator for ''' + name + ''' Plugin.

Generates Chart.js JavaScript code with theme-aware coloring.
"""

import json
from typing import Dict, List, Any, Union
from .theme import ReportTheme


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """Convert DataFrame or other iterable to List[Dict]."""
    if hasattr(data, '__iter__') and hasattr(data, 'column_names') and hasattr(data, 'rows'):
        return list(data)
    elif isinstance(data, list):
        return data
    else:
        return list(data) if hasattr(data, '__iter__') and not isinstance(data, str) else []


class ''' + class_name + '''ChartGenerator:
    """Generate Chart.js JavaScript code with theme support."""
    
    def generate_chart(
        self,
        data: Union[List[Dict[str, Any]], Any],  # DataFrame or List[Dict]
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any],
        theme: ReportTheme = None
    ) -> str:
        """
        Generate Chart.js JavaScript code.
        
        Parameters:
            data: Data points
            stats: Statistics dict
            config: Report config
            chart_config: Chart configuration
            theme: Theme object (required)
        
        Returns JavaScript code that creates the chart, NOT JSON config.
        """
        # Convert DataFrame to list if needed
        data_points = _normalize_data_to_list(data)
        
        chart_id = chart_config.get('id', 'chart')
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'score')
        x_field = chart_config.get('x_field', 'name')
        
        # Use provided theme or create default
        if not theme:
            theme = ReportTheme(id='default', name='Default')
        
        # Build data
        sorted_data = sorted(data_points, key=lambda x: x.get(y_field, 0), reverse=True)[:20]
        labels = [d.get(x_field, d.get('name', f'#{i}')) for i, d in enumerate(sorted_data)]
        values = [d.get(y_field, 0) for d in sorted_data]
        
        # Theme colors
        accent = self._hex_to_rgba(theme.accent, 0.8)
        accent_border = theme.accent
        text_soft = theme.text_soft
        text_main = theme.text_main
        grid = self._hex_to_rgba(theme.text_soft, 0.15)
        bg = self._hex_to_rgba(theme.bg, 0.94)
        
        if chart_type == 'histogram':
            return self._generate_histogram(chart_id, title, values, y_field, theme)
        
        if chart_type in ('pie', 'doughnut'):
            return self._generate_pie_chart(chart_id, title, labels, values, chart_type, theme)
        
        if chart_type == 'line':
            return self._generate_line_chart(chart_id, title, labels, values, theme)
        
        # Default: Bar chart
        js_code = f"""
// {title} Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: '{chart_type}',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: {json.dumps(title)},
                data: {json.dumps(values)},
                backgroundColor: '{accent}',
                borderColor: '{accent_border}',
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ labels: {{ color: '{text_soft}' }} }},
                tooltip: {{
                    backgroundColor: '{bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{accent_border}',
                    borderWidth: 1
                }}
            }},
            scales: {{
                x: {{ 
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }} 
                }},
                y: {{ 
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }},
                    beginAtZero: true
                }}
            }}
        }}
    }});
}})();
"""
        return js_code
    
    def _generate_line_chart(self, chart_id: str, title: str, labels: List[str], values: List[float], theme) -> str:
        """Generate line chart with gradient fill."""
        accent = theme.accent
        text_soft = theme.text_soft
        text_main = theme.text_main
        grid = self._hex_to_rgba(theme.text_soft, 0.15)
        bg = self._hex_to_rgba(theme.bg, 0.94)
        
        return f"""
// {title} Line Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{self._hex_to_rgba(theme.accent, 0.4)}');
    gradient.addColorStop(1, '{self._hex_to_rgba(theme.accent, 0.0)}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: {json.dumps(title)},
                data: {json.dumps(values)},
                borderColor: '{accent}',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '{accent}',
                pointBorderColor: '{text_main}'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ labels: {{ color: '{text_soft}' }} }},
                tooltip: {{
                    backgroundColor: '{bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{accent}',
                    borderWidth: 1
                }}
            }},
            scales: {{
                x: {{ ticks: {{ color: '{text_soft}' }}, grid: {{ color: '{grid}' }} }},
                y: {{ ticks: {{ color: '{text_soft}' }}, grid: {{ color: '{grid}' }}, beginAtZero: true }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_pie_chart(self, chart_id: str, title: str, labels: List[str], values: List[float], chart_type: str, theme) -> str:
        """Generate pie or doughnut chart with theme colors."""
        text_soft = theme.text_soft
        text_main = theme.text_main
        bg = self._hex_to_rgba(theme.bg, 0.94)
        
        # Generate color palette based on theme
        colors = [
            theme.accent,
            getattr(theme, 'ok', '#22c55e'),
            getattr(theme, 'warn', '#eab308'),
            getattr(theme, 'danger', '#ef4444'),
            self._hex_to_rgba(theme.accent, 0.6),
            self._hex_to_rgba(getattr(theme, 'ok', '#22c55e'), 0.6),
        ]
        
        # Extend colors if needed
        while len(colors) < len(values):
            colors.extend(colors)
        colors = colors[:len(values)]
        
        return f"""
// {title} {chart_type.title()} Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: '{chart_type}',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                data: {json.dumps(values)},
                backgroundColor: {json.dumps(colors)},
                borderColor: '{theme.bg}',
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ 
                    position: 'right',
                    labels: {{ color: '{text_soft}', padding: 15 }} 
                }},
                tooltip: {{
                    backgroundColor: '{bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1
                }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_histogram(self, chart_id: str, title: str, values: List[float], field: str, theme) -> str:
        """Generate histogram chart."""
        if not values:
            return f"// {title}: No data"
        
        min_val = min(values)
        max_val = max(values)
        num_bins = min(10, max(len(set(values)), 2))
        bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1
        
        bins = [0] * num_bins
        labels = []
        
        for v in values:
            idx = min(int((v - min_val) / bin_width), num_bins - 1)
            bins[idx] += 1
        
        for i in range(num_bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            labels.append(f"{int(bin_start)}-{int(bin_end)}")
        
        accent = self._hex_to_rgba(theme.accent, 0.75)
        accent_border = theme.accent
        text_soft = theme.text_soft
        text_main = theme.text_main
        grid = self._hex_to_rgba(theme.text_soft, 0.15)
        
        js_code = f"""
// {title} Histogram
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: 'Frequency',
                data: {json.dumps(bins)},
                backgroundColor: '{accent}',
                borderColor: '{accent_border}',
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{ display: true, text: {json.dumps(title)}, color: '{text_main}' }},
                legend: {{ display: false }}
            }},
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(field.title())}, color: '{text_soft}' }},
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }} 
                }},
                y: {{ 
                    title: {{ display: true, text: 'Frequency', color: '{text_soft}' }},
                    ticks: {{ color: '{text_soft}' }}, 
                    grid: {{ color: '{grid}' }},
                    beginAtZero: true
                }}
            }}
        }}
    }});
}})();
"""
        return js_code
    
    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        \"\"\"Convert hex color to rgba string.\"\"\"
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be between 0.0 and 1.0, got {alpha}")
        
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color '{hex_color}': expected 3 or 6 hex digits")
        if any(c not in "0123456789abcdefABCDEF" for c in hex_color):
            raise ValueError(f"Invalid hex color '{hex_color}': contains non-hex characters")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
'''
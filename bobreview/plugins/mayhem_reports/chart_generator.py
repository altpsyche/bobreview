"""
Chart Generator for mayhem-reports Plugin.

Generates Chart.js JavaScript code for performance visualization:
- Histogram charts for draws/tris distribution
- Timeline charts for performance over time
- Scatter plots for correlation analysis

Implements ChartGeneratorInterface from core.api.
"""

import json
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME


class MayhemReportsChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js JavaScript code for performance reports."""
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate Chart.js JavaScript code.
        
        Parameters:
            data_points: List of parsed data points
            stats: Statistical analysis results
            config: ReportConfig
            chart_config: Chart-specific configuration with type, title, fields
        
        Returns:
            JavaScript code string that creates the chart
        """
        chart_id = chart_config.get('id', 'chart')
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'draws')
        x_field = chart_config.get('x_field', 'index')
        
        # Get theme for colors - try terminal theme first, then dark theme as fallback
        theme = get_theme_by_id('terminal') or get_theme_by_id('dark') or DARK_THEME
        
        accent = theme.accent
        accent_strong = theme.accent_strong
        danger = theme.danger
        ok = theme.ok
        warn = theme.warn
        text_soft = theme.text_soft
        text_main = theme.text_main
        bg = theme.bg
        
        # Generate chart based on type
        if chart_type == 'histogram':
            return self._generate_histogram_js(data_points, stats, y_field, title, chart_id, 
                                                accent, text_soft, text_main)
        elif chart_type == 'timeline':
            return self._generate_timeline_js(data_points, stats, y_field, title, chart_id,
                                               accent, accent_strong, danger, ok, warn, text_soft, text_main, bg)
        elif chart_type == 'scatter':
            return self._generate_scatter_js(data_points, stats, x_field, y_field, title, chart_id,
                                              accent, danger, ok, warn, text_soft, text_main, bg)
        else:
            return self._generate_bar_js(data_points, stats, y_field, title, chart_id,
                                          accent, text_soft, text_main)
    
    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    def _generate_bar_js(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        y_field: str,
        title: str,
        chart_id: str,
        accent: str,
        text_soft: str,
        text_main: str
    ) -> str:
        """Generate bar chart JavaScript code."""
        # Sort by y_field descending
        sorted_data = sorted(data_points, key=lambda x: x.get(y_field, 0), reverse=True)
        
        labels = []
        values = []
        for i, d in enumerate(sorted_data[:20]):  # Limit to top 20
            label = d.get('testcase') or d.get('name') or f"#{i+1}"
            labels.append(label)
            values.append(d.get(y_field, 0))
        
        accent_rgba = self._hex_to_rgba(accent, 0.8)
        accent_border = self._hex_to_rgba(accent, 1)
        
        return f"""
// {title} Bar Chart
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: {json.dumps(title)},
                data: {json.dumps(values)},
                backgroundColor: '{accent_rgba}',
                borderColor: '{accent_border}',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{
                    display: true,
                    text: {json.dumps(title)},
                    color: '{text_main}'
                }},
                legend: {{
                    labels: {{ color: '{text_soft}' }}
                }}
            }},
            scales: {{
                x: {{
                    ticks: {{ color: '{text_soft}' }},
                    grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                }},
                y: {{
                    ticks: {{ color: '{text_soft}' }},
                    grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_histogram_js(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        field: str,
        title: str,
        chart_id: str,
        accent: str,
        text_soft: str,
        text_main: str
    ) -> str:
        """Generate histogram chart JavaScript code."""
        values = [d.get(field, 0) for d in data_points]
        
        if not values:
            return f"// {title}: No data"
        
        # Create histogram bins
        min_val = min(values)
        max_val = max(values)
        num_bins = min(15, len(set(values)))
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
        
        accent_rgba = self._hex_to_rgba(accent, 0.7)
        accent_border = self._hex_to_rgba(accent, 1)
        
        return f"""
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
                backgroundColor: '{accent_rgba}',
                borderColor: '{accent_border}',
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{
                    display: true,
                    text: {json.dumps(title)},
                    color: '{text_main}'
                }},
                legend: {{
                    labels: {{ color: '{text_soft}' }}
                }}
            }},
            scales: {{
                x: {{
                    title: {{ display: true, text: {json.dumps(field.title())}, color: '{text_soft}' }},
                    ticks: {{ color: '{text_soft}', maxRotation: 45 }},
                    grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                }},
                y: {{
                    title: {{ display: true, text: 'Frequency', color: '{text_soft}' }},
                    ticks: {{ color: '{text_soft}' }},
                    grid: {{ color: 'rgba(255, 255, 255, 0.1)' }},
                    beginAtZero: true
                }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_timeline_js(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        field: str,
        title: str,
        chart_id: str,
        accent: str,
        accent_strong: str,
        danger: str,
        ok: str,
        warn: str,
        text_soft: str,
        text_main: str,
        bg: str
    ) -> str:
        """Generate timeline chart JavaScript code with performance zone colors."""
        # Build data with color-coded points
        points = []
        for i, p in enumerate(data_points):
            value = p.get(field, 0)
            testcase = p.get('testcase', f'Frame {i}')
            points.append({'x': i, 'y': value, 'testcase': testcase})
        
        data_json = json.dumps(points)
        
        # Get mean for annotation line
        field_stats = stats.get(field, {})
        mean_val = field_stats.get('mean', 0) if field_stats else 0
        
        gradient_top = self._hex_to_rgba(accent, 0.3)
        gradient_bottom = self._hex_to_rgba(accent, 0.05)
        grid_color = self._hex_to_rgba(text_soft, 0.2)
        tooltip_bg = self._hex_to_rgba(bg, 0.94)
        warn_rgba = self._hex_to_rgba(warn, 0.8)
        
        return f"""
// {title} Timeline
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const data = {data_json};
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{gradient_top}');
    gradient.addColorStop(1, '{gradient_bottom}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: {json.dumps(title)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                borderColor: '{accent}',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: '{accent}',
                pointBorderColor: '{accent}',
                pointBorderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{ intersect: false, mode: 'index' }},
            scales: {{
                x: {{ 
                    type: 'linear',
                    title: {{ display: true, text: 'Frame Index', color: '{text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(field.title())}, color: '{text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{text_soft}', callback: function(v) {{ return v.toLocaleString(); }} }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{accent}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + items[0].parsed.x; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [d.testcase, {json.dumps(field.title())} + ': ' + d.y.toLocaleString()];
                        }}
                    }}
                }},
                annotation: {{
                    annotations: {{
                        meanLine: {{
                            type: 'line',
                            yMin: {mean_val},
                            yMax: {mean_val},
                            borderColor: '{warn_rgba}',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {{ display: true, content: 'Mean: {int(mean_val)}', position: 'end' }}
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
    
    def _generate_scatter_js(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        x_field: str,
        y_field: str,
        title: str,
        chart_id: str,
        accent: str,
        danger: str,
        ok: str,
        warn: str,
        text_soft: str,
        text_main: str,
        bg: str
    ) -> str:
        """Generate scatter plot JavaScript code with performance zone colors."""
        points = []
        for i, p in enumerate(data_points):
            x_val = p.get(x_field, 0)
            y_val = p.get(y_field, 0)
            testcase = p.get('testcase', f'Frame {i}')
            points.append({'x': x_val, 'y': y_val, 'testcase': testcase, 'index': i})
        
        scatter_data = json.dumps(points)
        scatter_label = f"{x_field.title()} vs {y_field.title()}"
        
        accent_rgba = self._hex_to_rgba(accent, 0.7)
        accent_border = self._hex_to_rgba(accent, 1)
        grid_color = self._hex_to_rgba(text_soft, 0.2)
        tooltip_bg = self._hex_to_rgba(bg, 0.94)
        
        return f"""
// {title} Scatter Plot
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const data = {scatter_data};
    
    new Chart(ctx, {{
        type: 'scatter',
        data: {{
            datasets: [{{
                label: {json.dumps(scatter_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                backgroundColor: '{accent_rgba}',
                borderColor: '{accent_border}',
                pointRadius: 6,
                pointHoverRadius: 10,
                pointBorderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(x_field.title())}, color: '{text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(y_field.title())}, color: '{text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{text_soft}', callback: function(v) {{ return v.toLocaleString(); }} }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{text_main}',
                    bodyColor: '{text_soft}',
                    borderColor: '{accent}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + data[items[0].dataIndex].index; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [
                                d.testcase,
                                {json.dumps(x_field.title())} + ': ' + d.x.toLocaleString(),
                                {json.dumps(y_field.title())} + ': ' + d.y.toLocaleString()
                            ];
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""

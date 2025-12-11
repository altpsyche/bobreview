"""
Chart Generator for mayhem-reports Plugin.

Generates Chart.js JavaScript code for performance visualization:
- Histogram charts for draws/tris distribution with zone colors
- Timeline charts with performance zone coloring
- Scatter plots with zone-based coloring

Implements ChartGeneratorInterface from core.api.
"""

import json
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME


class MayhemReportsChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js JavaScript code with multi-color theme support."""
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate Chart.js JavaScript code with performance zone colors.
        
        Parameters:
            data_points: List of parsed data points
            stats: Statistical analysis results
            config: ReportConfig with thresholds
            chart_config: Chart-specific configuration
        
        Returns:
            JavaScript code string that creates the chart
        """
        chart_id = chart_config.get('id', 'chart')
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'draws')
        x_field = chart_config.get('x_field', 'index')
        
        # Get theme for colors
        theme = get_theme_by_id('terminal') or get_theme_by_id('dark') or DARK_THEME
        
        # Get thresholds from config
        thresholds = {}
        if config and hasattr(config, 'thresholds'):
            thresholds = config.thresholds or {}
        
        high_draw = thresholds.get('high_load_draw_threshold', 600)
        low_draw = thresholds.get('low_load_draw_threshold', 400)
        high_tris = thresholds.get('high_load_tri_threshold', 100000)
        low_tris = thresholds.get('low_load_tri_threshold', 50000)
        
        # Generate chart based on type
        if chart_type == 'histogram':
            if y_field == 'draws':
                return self._generate_histogram_js(data_points, stats, y_field, title, chart_id, 
                                                    theme, high_draw, low_draw)
            else:
                return self._generate_histogram_js(data_points, stats, y_field, title, chart_id, 
                                                    theme, high_tris, low_tris)
        elif chart_type == 'timeline':
            if y_field == 'draws':
                return self._generate_timeline_js(data_points, stats, y_field, title, chart_id,
                                                   theme, high_draw, low_draw)
            else:
                return self._generate_timeline_js(data_points, stats, y_field, title, chart_id,
                                                   theme, high_tris, low_tris)
        elif chart_type == 'scatter':
            return self._generate_scatter_js(data_points, stats, x_field, y_field, title, chart_id,
                                              theme, high_draw, low_draw, high_tris, low_tris)
        else:
            return self._generate_bar_js(data_points, stats, y_field, title, chart_id, theme)
    
    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    
    def _get_zone_color(self, value: float, high_threshold: float, low_threshold: float, theme) -> str:
        """Get performance zone color based on value and thresholds."""
        if value >= high_threshold:
            return self._hex_to_rgba(theme.danger, 0.8)
        elif value < low_threshold:
            return self._hex_to_rgba(theme.ok, 0.8)
        else:
            return self._hex_to_rgba(theme.warn, 0.8)
    
    def _generate_bar_js(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        y_field: str,
        title: str,
        chart_id: str,
        theme
    ) -> str:
        """Generate bar chart JavaScript code with gradient colors."""
        sorted_data = sorted(data_points, key=lambda x: x.get(y_field, 0), reverse=True)
        
        labels = []
        values = []
        for i, d in enumerate(sorted_data[:20]):
            label = d.get('testcase') or d.get('name') or f"#{i+1}"
            labels.append(label)
            values.append(d.get(y_field, 0))
        
        # Use multiple theme colors for visual interest
        colors = [
            self._hex_to_rgba(theme.accent, 0.8),
            self._hex_to_rgba(theme.accent_strong, 0.8),
            self._hex_to_rgba(theme.ok, 0.8),
            self._hex_to_rgba(theme.warn, 0.8),
        ]
        
        bg_colors = [colors[i % len(colors)] for i in range(len(values))]
        
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
                backgroundColor: {json.dumps(bg_colors)},
                borderColor: {json.dumps([c.replace('0.8', '1') for c in bg_colors])},
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
                    color: '{theme.text_main}'
                }},
                legend: {{
                    labels: {{ color: '{theme.text_soft}' }}
                }}
            }},
            scales: {{
                x: {{
                    ticks: {{ color: '{theme.text_soft}' }},
                    grid: {{ color: 'rgba(255, 255, 255, 0.1)' }}
                }},
                y: {{
                    ticks: {{ color: '{theme.text_soft}' }},
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
        theme,
        high_threshold: float,
        low_threshold: float
    ) -> str:
        """Generate histogram chart with performance zone colors."""
        values = [d.get(field, 0) for d in data_points]
        
        if not values:
            return f"// {title}: No data"
        
        min_val = min(values)
        max_val = max(values)
        num_bins = min(15, max(len(set(values)), 2))
        
        bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1
        bins = [0] * num_bins
        labels = []
        colors = []
        
        for v in values:
            bin_idx = min(int((v - min_val) / bin_width), num_bins - 1)
            bins[bin_idx] += 1
        
        # Color each bin based on its center value's performance zone
        for i in range(num_bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            bin_center = (bin_start + bin_end) / 2
            labels.append(f"{int(bin_start)}-{int(bin_end)}")
            
            # Assign zone color
            if bin_center >= high_threshold:
                colors.append(self._hex_to_rgba(theme.danger, 0.75))
            elif bin_center < low_threshold:
                colors.append(self._hex_to_rgba(theme.ok, 0.75))
            else:
                colors.append(self._hex_to_rgba(theme.warn, 0.75))
        
        border_colors = [c.replace('0.75', '1') for c in colors]
        grid_color = self._hex_to_rgba(theme.text_soft, 0.15)
        
        return f"""
// {title} Histogram with Performance Zones
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: 'Frequency',
                data: {json.dumps(bins)},
                backgroundColor: {json.dumps(colors)},
                borderColor: {json.dumps(border_colors)},
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
                    color: '{theme.text_main}'
                }},
                legend: {{
                    display: false
                }},
                tooltip: {{
                    backgroundColor: '{self._hex_to_rgba(theme.bg, 0.94)}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1,
                    callbacks: {{
                        label: function(ctx) {{
                            const val = ctx.parsed.y;
                            const label = ctx.label;
                            return val + ' frames in range ' + label;
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    title: {{ display: true, text: {json.dumps(field.title())}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    ticks: {{ color: '{theme.text_soft}', maxRotation: 45 }},
                    grid: {{ color: '{grid_color}' }}
                }},
                y: {{
                    title: {{ display: true, text: 'Frequency', color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    ticks: {{ color: '{theme.text_soft}' }},
                    grid: {{ color: '{grid_color}' }},
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
        theme,
        high_threshold: float,
        low_threshold: float
    ) -> str:
        """Generate timeline chart with per-point zone coloring."""
        points = []
        point_colors = []
        point_border_colors = []
        
        for i, p in enumerate(data_points):
            value = p.get(field, 0)
            testcase = p.get('testcase', f'Frame {i}')
            points.append({'x': i, 'y': value, 'testcase': testcase})
            
            # Color based on performance zone
            if value >= high_threshold:
                color = self._hex_to_rgba(theme.danger, 0.9)
            elif value < low_threshold:
                color = self._hex_to_rgba(theme.ok, 0.9)
            else:
                color = self._hex_to_rgba(theme.warn, 0.9)
            
            point_colors.append(color)
            point_border_colors.append(color.replace('0.9', '1'))
        
        data_json = json.dumps(points)
        
        # Get mean for annotation line
        field_stats = stats.get(field, {})
        mean_val = field_stats.get('mean', 0) if field_stats else 0
        
        # Create gradient with accent colors
        gradient_top = self._hex_to_rgba(theme.accent, 0.25)
        gradient_bottom = self._hex_to_rgba(theme.accent, 0.02)
        grid_color = self._hex_to_rgba(theme.text_soft, 0.15)
        tooltip_bg = self._hex_to_rgba(theme.bg, 0.94)
        warn_rgba = self._hex_to_rgba(theme.warn, 0.8)
        danger_rgba = self._hex_to_rgba(theme.danger, 0.5)
        ok_rgba = self._hex_to_rgba(theme.ok, 0.5)
        
        return f"""
// {title} Timeline with Performance Zones
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const data = {data_json};
    const pointColors = {json.dumps(point_colors)};
    const pointBorderColors = {json.dumps(point_border_colors)};
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{gradient_top}');
    gradient.addColorStop(1, '{gradient_bottom}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: {json.dumps(title)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                borderColor: '{theme.accent}',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 8,
                pointBackgroundColor: pointColors,
                pointBorderColor: pointBorderColors,
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
                    title: {{ display: true, text: 'Frame Index', color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(field.title())}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}', callback: function(v) {{ return v.toLocaleString(); }} }}
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + items[0].parsed.x; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            const val = d.y;
                            let zone = val >= {high_threshold} ? '🔴 High' : (val < {low_threshold} ? '🟢 Low' : '🟡 Medium');
                            return [d.testcase, {json.dumps(field.title())} + ': ' + val.toLocaleString(), 'Zone: ' + zone];
                        }}
                    }}
                }},
                annotation: {{
                    annotations: {{
                        criticalLine: {{
                            type: 'line',
                            yMin: {high_threshold},
                            yMax: {high_threshold},
                            borderColor: '{danger_rgba}',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {{ display: true, content: 'High ({int(high_threshold)})', position: 'end', backgroundColor: '{self._hex_to_rgba(theme.danger, 0.2)}', color: '{theme.danger}' }}
                        }},
                        goodLine: {{
                            type: 'line',
                            yMin: {low_threshold},
                            yMax: {low_threshold},
                            borderColor: '{ok_rgba}',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {{ display: true, content: 'Good ({int(low_threshold)})', position: 'start', backgroundColor: '{self._hex_to_rgba(theme.ok, 0.2)}', color: '{theme.ok}' }}
                        }},
                        meanLine: {{
                            type: 'line',
                            yMin: {mean_val},
                            yMax: {mean_val},
                            borderColor: '{warn_rgba}',
                            borderWidth: 2,
                            borderDash: [4, 4],
                            label: {{ display: true, content: 'Mean: {int(mean_val):,}', position: 'center', backgroundColor: '{self._hex_to_rgba(theme.warn, 0.2)}', color: '{theme.warn}' }}
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
        theme,
        high_x: float,
        low_x: float,
        high_y: float,
        low_y: float
    ) -> str:
        """Generate scatter plot with performance zone coloring per point."""
        points = []
        point_colors = []
        point_border_colors = []
        
        for i, p in enumerate(data_points):
            x_val = p.get(x_field, 0)
            y_val = p.get(y_field, 0)
            testcase = p.get('testcase', f'Frame {i}')
            points.append({'x': x_val, 'y': y_val, 'testcase': testcase, 'index': i})
            
            # Color based on worst metric (if either is in danger zone, use danger)
            if x_val >= high_x or y_val >= high_y:
                color = self._hex_to_rgba(theme.danger, 0.8)
            elif x_val < low_x and y_val < low_y:
                color = self._hex_to_rgba(theme.ok, 0.8)
            else:
                color = self._hex_to_rgba(theme.warn, 0.8)
            
            point_colors.append(color)
            point_border_colors.append(color.replace('0.8', '1'))
        
        scatter_data = json.dumps(points)
        scatter_label = f"{x_field.title()} vs {y_field.title()}"
        
        grid_color = self._hex_to_rgba(theme.text_soft, 0.15)
        tooltip_bg = self._hex_to_rgba(theme.bg, 0.94)
        
        return f"""
// {title} Scatter Plot with Performance Zones
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    const data = {scatter_data};
    const pointColors = {json.dumps(point_colors)};
    const pointBorderColors = {json.dumps(point_border_colors)};
    
    new Chart(ctx, {{
        type: 'scatter',
        data: {{
            datasets: [{{
                label: {json.dumps(scatter_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                backgroundColor: pointColors,
                borderColor: pointBorderColors,
                pointRadius: 7,
                pointHoverRadius: 11,
                pointBorderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(x_field.title())}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(y_field.title())}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}', callback: function(v) {{ return v.toLocaleString(); }} }}
                }}
            }},
            plugins: {{
                legend: {{ 
                    display: true,
                    labels: {{ 
                        color: '{theme.text_main}', 
                        font: {{ size: 12 }},
                        generateLabels: function(chart) {{
                            return [
                                {{ text: '🟢 Optimized', fillStyle: '{self._hex_to_rgba(theme.ok, 0.8)}', strokeStyle: '{theme.ok}' }},
                                {{ text: '🟡 Normal', fillStyle: '{self._hex_to_rgba(theme.warn, 0.8)}', strokeStyle: '{theme.warn}' }},
                                {{ text: '🔴 Hotspot', fillStyle: '{self._hex_to_rgba(theme.danger, 0.8)}', strokeStyle: '{theme.danger}' }}
                            ];
                        }}
                    }}
                }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + data[items[0].dataIndex].index; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            const xZone = d.x >= {high_x} ? 'High' : (d.x < {low_x} ? 'Low' : 'Medium');
                            const yZone = d.y >= {high_y} ? 'High' : (d.y < {low_y} ? 'Low' : 'Medium');
                            return [
                                d.testcase,
                                {json.dumps(x_field.title())} + ': ' + d.x.toLocaleString() + ' (' + xZone + ')',
                                {json.dumps(y_field.title())} + ': ' + d.y.toLocaleString() + ' (' + yZone + ')'
                            ];
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""

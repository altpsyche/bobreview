"""
Performance chart generator for MayhemAutomation.

This module contains all the Chart.js chart generation code for
performance analysis reports (draws/tris timelines, scatter plots, histograms).
Moved from executor.py to make it plugin-specific.
"""
import json
from typing import Dict, List, Any

from bobreview.core.theme_utils import get_theme


class PerformanceChartGenerator:
    """
    Generates Chart.js JavaScript code for performance analysis charts.
    
    This generator is specific to the MayhemAutomation plugin and handles
    draws/tris metrics with performance zone coloring.
    """
    
    def __init__(self, config, thresholds: Dict[str, Any]):
        """
        Initialize with config and thresholds.
        
        Args:
            config: ReportConfig with threshold values
            thresholds: Dict of threshold values from report system JSON
        """
        self.config = config
        self.thresholds = thresholds
        
    def generate(self, data_points: List[Dict[str, Any]], page_id: str, labels: Dict[str, str]) -> Dict[str, str]:
        """
        Generate chart JavaScript for a page.
        
        Args:
            data_points: List of data points with draws, tris, testcase
            page_id: Page ID ('visuals' or 'metrics')
            labels: Dict of label strings
            
        Returns:
            Dict mapping chart_name to JavaScript code
        """
        charts = {}
        
        # Get theme colors
        theme = get_theme()
        colors = self._get_theme_colors(theme)
        
        # Get labels with defaults
        draws_label = labels.get('draw_calls', 'Draw Calls')
        tris_label = labels.get('triangles', 'Triangles')
        frame_index_label = labels.get('frame_index', 'Frame Index')
        frequency_label = labels.get('frequency', 'Frequency')
        
        # Performance thresholds
        high_draw = self._get_threshold('high_load_draw_threshold', 600)
        low_draw = self._get_threshold('low_load_draw_threshold', 400)
        high_tris = self._get_threshold('high_load_tri_threshold', 100000)
        low_tris = self._get_threshold('low_load_tri_threshold', 50000)
        
        if page_id == 'visuals':
            charts = self._generate_visuals_charts(
                data_points, theme, colors, labels,
                draws_label, tris_label, frame_index_label,
                high_draw, low_draw, high_tris, low_tris
            )
        elif page_id == 'metrics':
            charts = self._generate_metrics_charts(
                data_points, theme, colors, labels,
                draws_label, tris_label, frequency_label,
                high_draw, low_draw, high_tris, low_tris
            )
            
        return charts
    
    def _get_threshold(self, key: str, default: float) -> float:
        """Get threshold from config or thresholds dict."""
        if hasattr(self.config, key):
            return getattr(self.config, key)
        return self.thresholds.get(key, default)
    
    def _get_theme_colors(self, theme) -> Dict[str, str]:
        """Get all theme colors for charts."""
        def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        
        return {
            'danger': hex_to_rgba(theme.danger, 0.8),
            'danger_soft': f"{theme.danger}80",
            'danger_bg': f"{theme.danger}20",
            'ok': hex_to_rgba(theme.ok, 0.8),
            'ok_soft': f"{theme.ok}80",
            'ok_bg': f"{theme.ok}20",
            'warn': hex_to_rgba(theme.warn, 0.8),
            'warn_soft': f"{theme.warn}80",
            'accent_top': hex_to_rgba(theme.accent, 0.3),
            'accent_bottom': hex_to_rgba(theme.accent, 0.05),
            'accent_strong_top': hex_to_rgba(theme.accent_strong, 0.3),
            'accent_strong_bottom': hex_to_rgba(theme.accent_strong, 0.05),
            'grid': f"{theme.text_soft}20",
            'grid_light': f"{theme.text_soft}15",
            'tooltip_bg': f"{theme.bg}F0",
        }
    
    def _generate_visuals_charts(
        self, data_points, theme, colors, labels,
        draws_label, tris_label, frame_index_label,
        high_draw, low_draw, high_tris, low_tris
    ) -> Dict[str, str]:
        """Generate charts for visuals page."""
        charts = {}
        
        def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        
        danger_color = colors['danger']
        ok_color = colors['ok']
        warn_color = colors['warn']
        danger_color_soft = colors['danger_soft']
        danger_color_bg = colors['danger_bg']
        ok_color_soft = colors['ok_soft']
        ok_color_bg = colors['ok_bg']
        accent_gradient_top = colors['accent_top']
        accent_gradient_bottom = colors['accent_bottom']
        accent_strong_gradient_top = colors['accent_strong_top']
        accent_strong_gradient_bottom = colors['accent_strong_bottom']
        grid_color = colors['grid']
        tooltip_bg = colors['tooltip_bg']
        
        # Build data with color-coded points
        draws_points = []
        tris_points = []
        scatter_points = []
        
        for i, p in enumerate(data_points):
            draws = p['draws']
            tris = p['tris']
            testcase = p.get('testcase', f'Frame {i}')
            
            # Color for draw calls
            if draws >= high_draw:
                draw_color = danger_color
            elif draws < low_draw:
                draw_color = ok_color
            else:
                draw_color = warn_color
            
            # Color for triangles
            if tris >= high_tris:
                tri_color = danger_color
            elif tris < low_tris:
                tri_color = ok_color
            else:
                tri_color = warn_color
            
            # Scatter color (worst of both)
            if draws >= high_draw or tris >= high_tris:
                scatter_color = hex_to_rgba(theme.danger, 0.8)
            elif draws < low_draw and tris < low_tris:
                scatter_color = hex_to_rgba(theme.ok, 0.8)
            else:
                scatter_color = hex_to_rgba(theme.warn, 0.8)
            
            draws_points.append({'x': i, 'y': draws, 'color': draw_color, 'testcase': testcase})
            tris_points.append({'x': i, 'y': tris, 'color': tri_color, 'testcase': testcase})
            scatter_points.append({'x': draws, 'y': tris, 'color': scatter_color, 'testcase': testcase, 'index': i})
        
        draws_data = json.dumps(draws_points)
        tris_data = json.dumps(tris_points)
        scatter_data = json.dumps(scatter_points)
        
        charts['draws_timeline'] = f"""
// Draw Calls Timeline with Performance Zones
(function() {{
    const ctx = document.getElementById('drawsTimeline').getContext('2d');
    const data = {draws_data};
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{accent_gradient_top}');
    gradient.addColorStop(1, '{accent_gradient_bottom}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: {json.dumps(draws_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                borderColor: '{theme.accent}',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: data.map(d => d.color),
                pointBorderColor: data.map(d => d.color),
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
                    title: {{ display: true, text: {json.dumps(frame_index_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(draws_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
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
                            return [d.testcase, {json.dumps(draws_label)} + ': ' + d.y.toLocaleString()];
                        }}
                    }}
                }},
                annotation: {{
                    annotations: {{
                        criticalLine: {{
                            type: 'line',
                            yMin: {high_draw},
                            yMax: {high_draw},
                            borderColor: '{danger_color_soft}',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {{ display: true, content: 'Critical ({high_draw})', position: 'end', backgroundColor: '{danger_color_bg}' }}
                        }},
                        warningLine: {{
                            type: 'line',
                            yMin: {low_draw},
                            yMax: {low_draw},
                            borderColor: '{ok_color_soft}',
                            borderWidth: 2,
                            borderDash: [6, 6],
                            label: {{ display: true, content: 'Good ({low_draw})', position: 'start', backgroundColor: '{ok_color_bg}' }}
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
        charts['tris_timeline'] = f"""
// Triangles Timeline with Performance Zones
(function() {{
    const ctx = document.getElementById('trisTimeline').getContext('2d');
    const data = {tris_data};
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, '{accent_strong_gradient_top}');
    gradient.addColorStop(1, '{accent_strong_gradient_bottom}');
    
    new Chart(ctx, {{
        type: 'line',
        data: {{
            datasets: [{{
                label: {json.dumps(tris_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                borderColor: '{theme.accent_strong}',
                backgroundColor: gradient,
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7,
                pointBackgroundColor: data.map(d => d.color),
                pointBorderColor: data.map(d => d.color),
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
                    title: {{ display: true, text: {json.dumps(frame_index_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(tris_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
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
                    borderColor: '{theme.accent_strong}',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {{
                        title: function(items) {{ return 'Frame ' + items[0].parsed.x; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [d.testcase, {json.dumps(tris_label)} + ': ' + d.y.toLocaleString()];
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
        scatter_label = f"{draws_label} vs {tris_label}"
        charts['scatter'] = f"""
// Scatter Plot with Performance Zone Colors
(function() {{
    const ctx = document.getElementById('scatterPlot').getContext('2d');
    const data = {scatter_data};
    
    new Chart(ctx, {{
        type: 'scatter',
        data: {{
            datasets: [{{
                label: {json.dumps(scatter_label)},
                data: data.map(d => ({{x: d.x, y: d.y}})),
                backgroundColor: data.map(d => d.color),
                borderColor: data.map(d => d.color.replace('0.8', '1')),
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
                    title: {{ display: true, text: {json.dumps(draws_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(tris_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
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
                        title: function(items) {{ return 'Frame ' + data[items[0].dataIndex].index; }},
                        label: function(ctx) {{ 
                            const d = data[ctx.dataIndex];
                            return [
                                d.testcase,
                                {json.dumps(draws_label)} + ': ' + d.x.toLocaleString(),
                                {json.dumps(tris_label)} + ': ' + d.y.toLocaleString()
                            ];
                        }}
                    }}
                }}
            }}
        }}
    }});
}})();
"""
        return charts
    
    def _generate_metrics_charts(
        self, data_points, theme, colors, labels,
        draws_label, tris_label, frequency_label,
        high_draw, low_draw, high_tris, low_tris
    ) -> Dict[str, str]:
        """Generate charts for metrics page."""
        charts = {}
        
        grid_color = colors['grid']
        grid_color_light = colors['grid_light']
        tooltip_bg = colors['tooltip_bg']
        
        # Histogram data with color-coded bars
        draws_values = [p['draws'] for p in data_points]
        tris_values = [p['tris'] for p in data_points]
        
        draws_hist = self._compute_histogram(draws_values, high_draw, low_draw)
        tris_hist = self._compute_histogram(tris_values, high_tris, low_tris)
        
        charts['draws_histogram'] = f"""
// Draw Calls Distribution
(function() {{
    const ctx = document.getElementById('drawsHistogram').getContext('2d');
    
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(draws_hist['labels'])},
            datasets: [{{
                label: {json.dumps(frequency_label)},
                data: {json.dumps(draws_hist['counts'])},
                backgroundColor: {json.dumps(draws_hist['colors'])},
                borderColor: {json.dumps([c.replace('0.7', '1') for c in draws_hist['colors']])},
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(draws_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color_light}' }},
                    ticks: {{ color: '{theme.text_soft}', maxRotation: 45 }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(frequency_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }},
                    beginAtZero: true
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
                    padding: 10
                }}
            }}
        }}
    }});
}})();
"""
        charts['tris_histogram'] = f"""
// Triangles Distribution
(function() {{
    const ctx = document.getElementById('trisHistogram').getContext('2d');
    
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(tris_hist['labels'])},
            datasets: [{{
                label: {json.dumps(frequency_label)},
                data: {json.dumps(tris_hist['counts'])},
                backgroundColor: {json.dumps(tris_hist['colors'])},
                borderColor: {json.dumps([c.replace('0.7', '1') for c in tris_hist['colors']])},
                borderWidth: 1,
                borderRadius: 4
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                x: {{ 
                    title: {{ display: true, text: {json.dumps(tris_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color_light}' }},
                    ticks: {{ color: '{theme.text_soft}', maxRotation: 45 }}
                }},
                y: {{ 
                    title: {{ display: true, text: {json.dumps(frequency_label)}, color: '{theme.text_soft}', font: {{ weight: 'bold' }} }},
                    grid: {{ color: '{grid_color}' }},
                    ticks: {{ color: '{theme.text_soft}' }},
                    beginAtZero: true
                }}
            }},
            plugins: {{
                legend: {{ labels: {{ color: '{theme.text_main}', font: {{ size: 12 }} }} }},
                tooltip: {{
                    backgroundColor: '{tooltip_bg}',
                    titleColor: '{theme.text_main}',
                    bodyColor: '{theme.text_soft}',
                    borderColor: '{theme.accent_strong}',
                    borderWidth: 1,
                    padding: 10
                }}
            }}
        }}
    }});
}})();
"""
        return charts
    
    def _compute_histogram(self, values: List[float], high_threshold: float = None, low_threshold: float = None, num_bins: int = 15) -> Dict[str, Any]:
        """Compute histogram bins with performance zone colors."""
        if not values:
            return {'labels': [], 'counts': [], 'colors': []}
        
        theme = get_theme()
        
        def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        
        danger_rgba = hex_to_rgba(theme.danger, 0.7)
        ok_rgba = hex_to_rgba(theme.ok, 0.7)
        warn_rgba = hex_to_rgba(theme.warn, 0.7)
        accent_rgba = hex_to_rgba(theme.accent, 0.7)
        
        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            return {'labels': [str(int(min_val))], 'counts': [len(values)], 'colors': [accent_rgba]}
        
        bin_width = (max_val - min_val) / num_bins
        counts = [0] * num_bins
        
        for v in values:
            idx = int((v - min_val) / bin_width)
            if idx >= num_bins:
                idx = num_bins - 1
            counts[idx] += 1
        
        labels = []
        colors = []
        for i in range(num_bins):
            bin_center = min_val + (i + 0.5) * bin_width
            labels.append(f"{int(min_val + i * bin_width)}-{int(min_val + (i+1) * bin_width)}")
            
            # Color based on performance zone using theme colors
            if high_threshold and bin_center >= high_threshold:
                colors.append(danger_rgba)
            elif low_threshold and bin_center < low_threshold:
                colors.append(ok_rgba)
            else:
                colors.append(warn_rgba)
        
        return {'labels': labels, 'counts': counts, 'colors': colors}

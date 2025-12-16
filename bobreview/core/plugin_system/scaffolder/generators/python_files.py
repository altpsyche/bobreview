"""
Python file generators for plugin scaffolding.

Generates source code for plugin components:
- plugin.py (main plugin class)
- csv_parser.py (data parser)
- context_builder.py (template context)
- chart_generator.py (Chart.js generation)
- analysis.py (statistical analysis)
"""


def generate_plugin_py(name: str, safe_name: str, class_name: str, template: str) -> str:
    """Generate the main plugin.py file."""
    
    if template == 'full':
        imports = f"""from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper
from .parsers.csv_parser import {class_name}CsvParser
from .theme import {safe_name.upper()}_THEME, {safe_name.upper()}_DEEP_THEME"""

        
        registration = f'''        # Load report system definition
        import json
        report_system_path = Path(__file__).parent / "report_systems" / "{safe_name}.json"
        with open(report_system_path) as f:
            system_def = json.load(f)
        
        # Register core components
        helper.setup_complete_report_system(
            system_id="{safe_name}",
            system_def=system_def,
            parser_class={class_name}CsvParser,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # ─────────────────────────────────────────────────────────────────────
        # Register Themes (required - no built-in themes in core)
        # ─────────────────────────────────────────────────────────────────────
        
        helper.add_theme({safe_name.upper()}_THEME)
        helper.add_theme({safe_name.upper()}_DEEP_THEME)
        
        # NOTE: Pages are user-defined in report_config.yaml, not here.'''

    else:
        imports = f"""from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper
from .parsers.csv_parser import {class_name}CsvParser
from .analysis import analyze_{safe_name}_data"""
        
        registration = f'''        # Load report system definition
        import json
        report_system_path = Path(__file__).parent / "report_systems" / "{safe_name}.json"
        with open(report_system_path) as f:
            system_def = json.load(f)
        
        # Register core components
        helper.setup_complete_report_system(
            system_id="{safe_name}",
            system_def=system_def,
            parser_class={class_name}CsvParser,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # NOTE: Pages are user-defined in report_config.yaml, not here.'''
    
    return f'''"""
{name} Plugin - Main plugin class.
"""

{imports}


class {class_name}Plugin(BasePlugin):
    """
    Plugin for analyzing {name} data.
    """
    
    name = "{name}"
    version = "1.0.0"
    author = "Your Name"
    description = "Plugin for {name} analysis"

    def on_load(self, registry) -> None:
        """Register all plugin components using PluginHelper."""
        helper = PluginHelper(registry, self.name)
        
{registration}
    
    def on_report_start(self, context: dict) -> None:
        """Called when report generation begins."""
        pass
    
    def on_report_complete(self, result: dict) -> None:
        """Called when report generation completes."""
        pass
'''


def generate_csv_parser(name: str, class_name: str) -> str:
    """Generate CSV parser file."""
    return f'''"""
CSV Parser for {name} Plugin.

Data Flow:
    CSV → Parser.parse_directory() → List[Dict] → DataFrame
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

from bobreview.core.api import DataParserInterface


class {class_name}CsvParser:
    """
    Parse CSV files with name, score, and category columns.
    
    Expected CSV format:
        name,score,category
        Item1,85,Backend
        Item2,72,Frontend
    """
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single CSV file (not used for multi-row CSVs)."""
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Find all CSV files in the directory."""
        return sorted(directory.glob("*.csv"))
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all CSV files and return combined records."""
        data_points = []
        
        for csv_file in self.discover_files(directory):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data_point = self._parse_row(row, csv_file.name)
                        if data_point:
                            data_points.append(data_point)
            except (OSError, csv.Error):
                continue
        
        return data_points
    
    def _parse_row(self, row: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row."""
        try:
            name = row.get('name', '').strip()
            score_str = row.get('score', '').strip()
            
            if not name or not score_str:
                return None
            
            return {{
                'name': name,
                'score': float(score_str),
                'category': row.get('category', 'General').strip(),
                'source': source_file,
            }}
        except (ValueError, TypeError):
            return None
'''


def generate_context_builder(name: str, class_name: str) -> str:
    """Generate context builder file."""
    return f'''"""
Context Builder for {name} Plugin.
"""

from typing import Dict, List, Any, Union


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """Convert DataFrame or other iterable to List[Dict]."""
    if hasattr(data, '__iter__') and hasattr(data, 'column_names'):
        return list(data)
    elif isinstance(data, list):
        return data
    else:
        return list(data) if hasattr(data, '__iter__') and not isinstance(data, str) else []


class {class_name}ContextBuilder:
    """Build template context for {name} reports."""
    
    def build_context(
        self,
        data: Union[List[Dict[str, Any]], Any],
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enriched context for template rendering."""
        context = dict(base_context)
        
        # Convert DataFrame to list if needed
        data_points = _normalize_data_to_list(data)
        
        # Sort by score (descending)
        ranked = sorted(data_points, key=lambda x: x.get('score', 0), reverse=True)
        context['ranked_data'] = ranked
        
        # Add rankings
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        
        # Categorize by score
        scores = [d.get('score', 0) for d in data_points]
        if scores:
            context['score_range'] = {{
                'min': min(scores),
                'max': max(scores),
                'spread': max(scores) - min(scores),
            }}
        
        return context
'''



def generate_chart_generator(name: str, class_name: str) -> str:
    """Generate chart generator file with theme support."""
    return '''"""
Chart Generator for ''' + name + ''' Plugin.

Generates Chart.js JavaScript code with theme-aware coloring.
"""

import json
from typing import Dict, List, Any, Union
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """Convert DataFrame or other iterable to List[Dict]."""
    if hasattr(data, '__iter__') and hasattr(data, 'column_names'):
        return list(data)
    elif isinstance(data, list):
        return data
    else:
        return list(data) if hasattr(data, '__iter__') and not isinstance(data, str) else []


class ''' + class_name + '''ChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js JavaScript code with theme support."""
    
    def generate_chart(
        self,
        data: Union[List[Dict[str, Any]], Any],  # DataFrame or List[Dict]
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate Chart.js JavaScript code.
        
        Returns JavaScript code that creates the chart, NOT JSON config.
        """
        # Convert DataFrame to list if needed
        data_points = _normalize_data_to_list(data)
        
        chart_id = chart_config.get('id', 'chart')
        chart_type = chart_config.get('type', 'bar')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'score')
        x_field = chart_config.get('x_field', 'name')
        
        # Get theme from config
        theme_id = chart_config.get('theme_id', 'terminal')
        theme = get_theme_by_id(theme_id) or DARK_THEME
        
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


def generate_analysis_module(name: str, safe_name: str) -> str:
    """Generate analysis module with statistical functions."""
    return f'''"""
Statistical Analysis for {name} Plugin.

Provides common statistical functions for data analysis.
Register with: helper.add_analyzer('{safe_name}', analyze_{safe_name}_data)
"""

from typing import List, Dict, Any
import statistics


def analyze_{safe_name}_data(
    data_points: List[Dict[str, Any]],
    config: Any = None,
    **kwargs  # Accept metrics, metric_config from AnalyticsService
) -> Dict[str, Any]:
    """
    Compute statistics from parsed data.
    
    Parameters:
        data_points: List of parsed data points with 'score' field
        config: Optional Config
        **kwargs: Additional args from AnalyticsService (metrics, metric_config)
    
    Returns:
        Dict with computed statistics
    """
    if not data_points:
        return {{'count': 0}}
    
    scores = [p.get('score', 0) for p in data_points]
    sorted_scores = sorted(scores)
    n = len(scores)
    
    def percentile(data: List[float], p: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        idx = int(len(data) * p / 100)
        return data[min(idx, len(data) - 1)]
    
    return {{
        'count': n,
        'score': {{
            'min': min(scores),
            'max': max(scores),
            'mean': statistics.mean(scores),
            'median': statistics.median(scores),
            'stdev': statistics.stdev(scores) if n > 1 else 0,
            'variance': statistics.variance(scores) if n > 1 else 0,
            'q1': percentile(sorted_scores, 25),
            'q3': percentile(sorted_scores, 75),
            'p90': percentile(sorted_scores, 90),
            'p95': percentile(sorted_scores, 95),
            'iqr': percentile(sorted_scores, 75) - percentile(sorted_scores, 25),
        }},
        # Categorized data for templates
        'high_performers': [p for p in data_points if p.get('score', 0) >= percentile(sorted_scores, 75)],
        'low_performers': [p for p in data_points if p.get('score', 0) <= percentile(sorted_scores, 25)],
        'median_performers': [p for p in data_points 
                              if percentile(sorted_scores, 25) < p.get('score', 0) < percentile(sorted_scores, 75)],
    }}
'''


def generate_theme_module(name: str, safe_name: str, class_name: str) -> str:
    """
    Generate theme.py with premium, production-ready themes.
    
    Includes 4 stunning themes:
    - MIDNIGHT: Deep blue with electric cyan accents
    - AURORA: Purple/magenta with northern lights feel
    - SUNSET: Warm amber/orange gradients
    - FROST: Clean icy light theme
    """
    return f'''"""
Premium Themes for {name} Plugin.

Four stunning themes with unique personalities:

1. MIDNIGHT - Deep blue with electric cyan accents (default)
2. AURORA - Purple/magenta with northern lights glow
3. SUNSET - Warm amber and orange gradients
4. FROST - Clean, icy light theme

Register in plugin.py:
    from .theme import (
        {safe_name.upper()}_MIDNIGHT,
        {safe_name.upper()}_AURORA,
        {safe_name.upper()}_SUNSET,
        {safe_name.upper()}_FROST,
    )
    helper.add_theme({safe_name.upper()}_MIDNIGHT)
    helper.add_theme({safe_name.upper()}_AURORA)
    helper.add_theme({safe_name.upper()}_SUNSET)
    helper.add_theme({safe_name.upper()}_FROST)
"""

from bobreview.core.themes import ReportTheme, hex_to_rgba


# =============================================================================
# 🌙 MIDNIGHT THEME - Deep blue with electric cyan
# =============================================================================
# Perfect for: Technical reports, developer dashboards, code analysis
# Font: JetBrains Mono + Inter - clean, technical, highly readable

{safe_name.upper()}_MIDNIGHT = ReportTheme(
    id='{safe_name}_midnight',
    name='{class_name} Midnight',
    
    # Deep blue-black backgrounds
    bg='#0a0f1a',
    bg_elevated='#111827',
    bg_soft='#1e293b',
    
    # Electric cyan accents
    accent='#22d3ee',
    accent_soft=hex_to_rgba('#22d3ee', 0.15),
    accent_strong='#67e8f9',
    
    # Cool gray text
    text_main='#f1f5f9',
    text_soft='#94a3b8',
    
    # Vibrant status colors
    ok='#4ade80',
    ok_soft=hex_to_rgba('#4ade80', 0.15),
    warn='#facc15',
    warn_soft=hex_to_rgba('#facc15', 0.15),
    danger='#f87171',
    danger_soft=hex_to_rgba('#f87171', 0.15),
    
    # Sharp edges for technical feel
    border_subtle='#334155',
    shadow_soft='0 8px 32px rgba(0, 0, 0, 0.5)',
    shadow_strong='0 20px 60px rgba(0, 0, 0, 0.7)',
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='16px',
    
    # JetBrains Mono + Inter - technical, clean
    font_family='"Inter", "SF Pro Display", system-ui, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", "SF Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# 🌌 AURORA THEME - Purple/magenta with northern lights glow
# =============================================================================
# Perfect for: Creative projects, marketing reports, analytics dashboards
# Font: Space Grotesk + IBM Plex Mono - modern, geometric, stylish

{safe_name.upper()}_AURORA = ReportTheme(
    id='{safe_name}_aurora',
    name='{class_name} Aurora',
    
    # Deep purple-black backgrounds
    bg='#0c0a1d',
    bg_elevated='#13102a',
    bg_soft='#1e1839',
    
    # Vibrant magenta/pink accents
    accent='#e879f9',
    accent_soft=hex_to_rgba('#e879f9', 0.18),
    accent_strong='#f0abfc',
    
    # Soft lavender text
    text_main='#f5f3ff',
    text_soft='#a5b4fc',
    
    # Colorful neon status colors
    ok='#34d399',
    ok_soft=hex_to_rgba('#34d399', 0.15),
    warn='#fcd34d',
    warn_soft=hex_to_rgba('#fcd34d', 0.15),
    danger='#fb7185',
    danger_soft=hex_to_rgba('#fb7185', 0.15),
    
    # Soft glow effects
    border_subtle='#312e54',
    shadow_soft='0 10px 40px rgba(139, 92, 246, 0.2)',
    shadow_strong='0 25px 80px rgba(139, 92, 246, 0.35)',
    radius_sm='6px',
    radius_md='12px',
    radius_lg='18px',
    radius_xl='24px',
    
    # Space Grotesk + IBM Plex Mono - modern, geometric
    font_family='"Space Grotesk", "Outfit", system-ui, sans-serif',
    font_mono='"IBM Plex Mono", "Source Code Pro", monospace',
    font_url='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap',
    
    chart_grid_opacity=0.3,
)


# =============================================================================
# 🌅 SUNSET THEME - Warm amber and orange gradients
# =============================================================================
# Perfect for: Business reports, executive dashboards, warm presentations
# Font: DM Sans + JetBrains Mono - friendly, professional, approachable

{safe_name.upper()}_SUNSET = ReportTheme(
    id='{safe_name}_sunset',
    name='{class_name} Sunset',
    
    # Warm dark backgrounds with red undertones
    bg='#120c0c',
    bg_elevated='#1a1212',
    bg_soft='#271a1a',
    
    # Warm amber/orange accents
    accent='#fb923c',
    accent_soft=hex_to_rgba('#fb923c', 0.18),
    accent_strong='#fdba74',
    
    # Warm cream text
    text_main='#fef3e2',
    text_soft='#d4a574',
    
    # Fire-inspired status colors
    ok='#86efac',
    ok_soft=hex_to_rgba('#86efac', 0.15),
    warn='#fde047',
    warn_soft=hex_to_rgba('#fde047', 0.15),
    danger='#fca5a5',
    danger_soft=hex_to_rgba('#fca5a5', 0.15),
    
    # Warm, cozy effects
    border_subtle='#3d2a2a',
    shadow_soft='0 12px 40px rgba(251, 146, 60, 0.15)',
    shadow_strong='0 24px 70px rgba(251, 146, 60, 0.25)',
    radius_sm='6px',
    radius_md='10px',
    radius_lg='16px',
    radius_xl='24px',
    
    # DM Sans + JetBrains Mono - friendly, readable
    font_family='"DM Sans", "Nunito", "Poppins", system-ui, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", monospace',
    font_url='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap',
    
    chart_grid_opacity=0.35,
)


# =============================================================================
# ❄️ FROST THEME - Clean, icy light theme
# =============================================================================
# Perfect for: Print-friendly reports, light mode preference, formal docs
# Font: Plus Jakarta Sans + Fira Code - elegant, modern, professional

{safe_name.upper()}_FROST = ReportTheme(
    id='{safe_name}_frost',
    name='{class_name} Frost',
    
    # Clean icy backgrounds
    bg='#f0f9ff',
    bg_elevated='#ffffff',
    bg_soft='#e0f2fe',
    
    # Cool blue accent
    accent='#0284c7',
    accent_soft=hex_to_rgba('#0284c7', 0.12),
    accent_strong='#0ea5e9',
    
    # Dark slate text
    text_main='#0f172a',
    text_soft='#475569',
    
    # Clear, vivid status
    ok='#16a34a',
    ok_soft=hex_to_rgba('#16a34a', 0.1),
    warn='#d97706',
    warn_soft=hex_to_rgba('#d97706', 0.1),
    danger='#dc2626',
    danger_soft=hex_to_rgba('#dc2626', 0.1),
    
    # Subtle, clean effects
    border_subtle='#bae6fd',
    shadow_soft='0 4px 20px rgba(14, 165, 233, 0.08)',
    shadow_strong='0 12px 40px rgba(14, 165, 233, 0.15)',
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='20px',
    
    # Plus Jakarta Sans + Fira Code - elegant, modern
    font_family='"Plus Jakarta Sans", "Outfit", "Inter", system-ui, sans-serif',
    font_mono='"Fira Code", "JetBrains Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap',
    
    chart_grid_opacity=0.25,
)


# =============================================================================
# DEFAULT THEME ALIAS
# =============================================================================
# Point to midnight as the default theme for this plugin

{safe_name.upper()}_THEME = {safe_name.upper()}_MIDNIGHT


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Register in plugin.py on_load():
#        helper.add_theme({safe_name.upper()}_MIDNIGHT)  # or any theme
#
# 2. Use in executor/templates:
#        theme_id='{safe_name}_midnight'  # or aurora, sunset, frost
#
# 3. Available themes:
#        {safe_name}_midnight  - Deep blue + cyan (default)
#        {safe_name}_aurora    - Purple + magenta
#        {safe_name}_sunset    - Warm amber + orange
#        {safe_name}_frost     - Clean light blue
'''



def generate_widgets_module(name: str, safe_name: str, class_name: str) -> str:
    """Generate widgets.py with custom widget examples."""
    return f'''"""
Custom Widgets for {name} Plugin.

Widgets are reusable UI components that can be used across templates.
Register widgets with: helper.add_widget('widget_id', WidgetClass)
"""

from typing import Dict, Any


class {class_name}StatCard:
    """
    A reusable stat card widget for displaying key metrics.
    
    Usage in templates:
        {{{{ widgets.{safe_name}_stat_card.render(title="Score", value=85, trend="up") }}}}
    """
    
    @staticmethod
    def render(
        title: str,
        value: Any,
        subtitle: str = "",
        trend: str = "",  # "up", "down", or ""
        status: str = "neutral"  # "ok", "warn", "danger", "neutral"
    ) -> str:
        """
        Render the stat card HTML.
        
        Parameters:
            title: Card title
            value: Main value to display
            subtitle: Optional subtitle text
            trend: Trend indicator ("up", "down", or "")
            status: Status color ("ok", "warn", "danger", "neutral")
        
        Returns:
            HTML string for the stat card
        """
        trend_icon = ""
        if trend == "up":
            trend_icon = '<span class="trend trend-up">↑</span>'
        elif trend == "down":
            trend_icon = '<span class="trend trend-down">↓</span>'
        
        status_class = f"stat-card--{{status}}" if status != "neutral" else ""
        
        return f"""
        <div class="stat-card {{status_class}}">
            <div class="stat-card__title">{{title}}</div>
            <div class="stat-card__value">{{value}} {{trend_icon}}</div>
            <div class="stat-card__subtitle">{{subtitle}}</div>
        </div>
        """
    
    @staticmethod
    def get_css() -> str:
        """Return CSS for the stat card widget."""
        return """
        .stat-card {{
            background: var(--bg-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            text-align: center;
        }}
        .stat-card__title {{
            font-size: 0.875rem;
            color: var(--text-soft);
            margin-bottom: 0.5rem;
        }}
        .stat-card__value {{
            font-size: 2rem;
            font-weight: 600;
            color: var(--text-main);
        }}
        .stat-card__subtitle {{
            font-size: 0.75rem;
            color: var(--text-soft);
            margin-top: 0.25rem;
        }}
        .stat-card--ok {{ border-color: var(--ok); }}
        .stat-card--warn {{ border-color: var(--warn); }}
        .stat-card--danger {{ border-color: var(--danger); }}
        .trend {{ margin-left: 0.25rem; }}
        .trend-up {{ color: var(--ok); }}
        .trend-down {{ color: var(--danger); }}
        """


# =============================================================================
# USAGE NOTES
# =============================================================================
#
# 1. Register in plugin.py on_load():
#        from .widgets import {class_name}StatCard
#        helper.add_widget("{safe_name}_stat_card", {class_name}StatCard)
#
# 2. Use in Jinja2 templates:
#        {{{{ widgets.{safe_name}_stat_card.render(title="Score", value=85) }}}}
#
# 3. Include widget CSS in your template:
#        <style>{{{{ widgets.{safe_name}_stat_card.get_css() }}}}</style>
'''


def generate_component_module(name: str, safe_name: str, class_name: str) -> str:
    """
    Generate components.py with Property Controls pattern.
    
    Creates example components demonstrating:
    - @register_component decorator
    - PropTypes schema definitions
    - Component templates
    """
    return f'''"""
Component Definitions for {name} plugin.

This module uses the Property Controls pattern where components
define their accepted props using PropTypes. Core validates YAML
against these schemas automatically.

Usage in YAML:
    components:
      - type: {safe_name}_chart
        id: my_chart
        chart: bar
        title: "Score Distribution"
        
      - type: {safe_name}_stat_card
        id: total
        label: "Total Items"
        value: "{{{{ stats.count }}}}"
"""

from bobreview.core.components import register_component, PropTypes


@register_component("{safe_name}_chart", plugin="{safe_name}")
class {class_name}ChartComponent:
    """
    Chart visualization component.
    
    Renders data as bar, line, pie, or other chart types.
    """
    
    props = {{
        "id": PropTypes.string(required=True, description="Unique chart ID"),
        "chart": PropTypes.choice(
            ["bar", "line", "pie", "scatter", "histogram", "doughnut"],
            default="bar",
            description="Chart type"
        ),
        "title": PropTypes.string(default="", description="Chart title"),
        "x": PropTypes.string(description="X-axis data field"),
        "y": PropTypes.string(description="Y-axis data field"),
        "animated": PropTypes.boolean(default=True, description="Enable animations"),
        "height": PropTypes.number(default=300, description="Chart height (px)"),
    }}
    
    template = "{safe_name}/components/chart.html.j2"


@register_component("{safe_name}_stat_card", plugin="{safe_name}")
class {class_name}StatCardComponent:
    """
    Stat card widget displaying a metric with label.
    
    Shows a prominent value with optional label, color, and status.
    """
    
    props = {{
        "id": PropTypes.string(description="Optional card ID"),
        "label": PropTypes.string(default="", description="Card label"),
        "value": PropTypes.template(required=True, description="Value (Jinja2)"),
        "color": PropTypes.color(description="Value color"),
        "icon": PropTypes.string(description="FontAwesome icon"),
        "variant": PropTypes.choice(
            ["default", "ok", "warn", "danger", "info"],
            default="default",
            description="Visual variant"
        ),
    }}
    
    template = "{safe_name}/components/stat_card.html.j2"


@register_component("{safe_name}_data_table", plugin="{safe_name}")
class {class_name}DataTableComponent:
    """
    Data table component for tabular data display.
    
    Renders data with sortable columns and optional pagination.
    """
    
    props = {{
        "id": PropTypes.string(description="Table ID"),
        "title": PropTypes.string(default="", description="Table title"),
        "columns": PropTypes.array(description="Column names"),
        "sortable": PropTypes.boolean(default=True, description="Sortable columns"),
        "paginated": PropTypes.boolean(default=False, description="Enable pagination"),
        "page_size": PropTypes.number(default=25, description="Rows per page"),
        "striped": PropTypes.boolean(default=True, description="Striped rows"),
    }}
    
    template = "{safe_name}/components/data_table.html.j2"


@register_component("{safe_name}_llm", plugin="{safe_name}")
class {class_name}LLMComponent:
    """
    LLM-generated content component.
    
    Generates content using an LLM with the provided prompt template.
    """
    
    props = {{
        "id": PropTypes.string(required=True, description="Unique ID"),
        "title": PropTypes.string(default="", description="Section title"),
        "prompt": PropTypes.template(description="Prompt template (Jinja2)"),
        "generator": PropTypes.string(description="Generator function"),
        "temperature": PropTypes.number(default=0.7, min=0, max=2),
    }}
    
    template = "{safe_name}/components/llm.html.j2"


@register_component("{safe_name}_text", plugin="{safe_name}")
class {class_name}TextComponent:
    """
    Static or templated text content.
    """
    
    props = {{
        "content": PropTypes.template(required=True, description="Content"),
        "markdown": PropTypes.boolean(default=False, description="Render as Markdown"),
        "class_name": PropTypes.string(default="", description="CSS class"),
    }}
    
    template = "{safe_name}/components/text.html.j2"


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Components are auto-registered when this module is imported
#    (via @register_component decorator)
#
# 2. Import in plugin.py __init__():
#        from . import components  # Triggers registration
#
# 3. Use in YAML config:
#        components:
#          - type: {safe_name}_chart
#            id: score_chart
#            chart: bar
#            title: "Scores"
#            x: name
#            y: score
'''


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
from .context_builder import {class_name}ContextBuilder
from .chart_generator import {class_name}ChartGenerator
from .analysis import analyze_{safe_name}_data
from .widgets import {class_name}StatCard
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
            analyzer_func=analyze_{safe_name}_data,
            context_builder_class={class_name}ContextBuilder,
            chart_generator_class={class_name}ChartGenerator,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # ─────────────────────────────────────────────────────────────────────
        # Register Components (users compose these in report_config.yaml)
        # ─────────────────────────────────────────────────────────────────────
        
        # Custom widget (reusable UI component)
        helper.add_widget("{safe_name}_stat_card", {class_name}StatCard)
        
        # Custom chart type (gauge visualization)
        helper.add_chart_type("{safe_name}_gauge", {{
            "type": "doughnut",
            "options": {{
                "cutout": "70%",
                "circumference": 180,
                "rotation": 270
            }},
            "description": "Semi-circular gauge chart for progress/scores"
        }})
        
        # Custom themes
        helper.add_theme({safe_name.upper()}_THEME)
        helper.add_theme({safe_name.upper()}_DEEP_THEME)
        
        # Register default services
        helper.register_default_services()
        
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
            analyzer_func=analyze_{safe_name}_data,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # Register default services
        helper.register_default_services()
        
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


class {class_name}CsvParser(DataParserInterface):
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
from bobreview.core.api import ContextBuilderInterface


class {class_name}ContextBuilder(ContextBuilderInterface):
    """Build template context for {name} reports."""
    
    def build_context(
        self,
        data: Union[List[Dict[str, Any]], Any],  # DataFrame or List[Dict]
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enriched context for template rendering."""
        context = dict(base_context)
        
        # Convert DataFrame to list if needed
        data_points = list(data) if hasattr(data, "__iter__") else data
        
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
        data_points = list(data) if hasattr(data, "__iter__") else data
        
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
        accent_soft = self._hex_to_rgba(theme.accent, 0.2)
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
    Generate theme.py with custom theme examples.
    
    Shows plugin developers how to create themes:
    - Full standalone theme with fonts and all properties
    - Theme extending ocean base with deeper colors
    """
    return f'''"""
Custom Themes for {name} Plugin.

This module demonstrates two approaches to theme creation:

1. FULL THEME - Complete standalone theme with all properties including fonts
2. OCEAN DEEP THEME - Extends ocean base with deeper, moodier colors

Register themes in plugin.py:
    from .theme import {safe_name.upper()}_THEME, {safe_name.upper()}_DEEP_THEME
    helper.add_theme({safe_name.upper()}_THEME)
    helper.add_theme({safe_name.upper()}_DEEP_THEME)
"""

from bobreview.core.themes import ReportTheme, create_theme, hex_to_rgba


# =============================================================================
# FULL THEME - Complete standalone theme with fonts and everything
# =============================================================================
#
# Use ReportTheme directly when you want full control over every property.
# This is ideal for a completely custom branded experience.

{safe_name.upper()}_THEME = ReportTheme(
    id='{safe_name}_full',
    name='{class_name} Theme',
    
    # Backgrounds - deep navy gradient feel
    bg='#0a0e14',
    bg_elevated='#12171f',
    bg_soft='#1a2028',
    
    # Accents - vibrant teal/cyan
    accent='#00d4aa',
    accent_soft=hex_to_rgba('#00d4aa', 0.15),
    accent_strong='#00ffcc',
    
    # Text - high contrast for readability
    text_main='#e8eaed',
    text_soft='#9aa0a6',
    
    # Status colors
    ok='#34d399',            # Emerald green
    ok_soft=hex_to_rgba('#34d399', 0.15),
    warn='#fbbf24',          # Amber
    warn_soft=hex_to_rgba('#fbbf24', 0.15),
    danger='#f87171',        # Coral red
    danger_soft=hex_to_rgba('#f87171', 0.15),
    
    # Borders and effects
    border_subtle='#282f3a',
    shadow_soft='0 8px 32px rgba(0, 0, 0, 0.4)',
    shadow_strong='0 16px 48px rgba(0, 0, 0, 0.6)',
    
    # Border radius
    radius_sm='4px',
    radius_md='8px',
    radius_lg='12px',
    radius_xl='20px',
    
    # Fonts - distinctive typography (different from built-in themes)
    # Space Grotesk: Modern geometric sans with character
    # IBM Plex Mono: Clean technical monospace
    font_family='"Space Grotesk", "Outfit", "Rubik", system-ui, sans-serif',
    font_mono='"IBM Plex Mono", "Source Code Pro", "Cascadia Code", monospace',
    
    # Google Fonts URL - templates use this to load the fonts dynamically
    font_url='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap',
    
    # Chart styling
    chart_grid_opacity=0.4,
)


# =============================================================================
# OCEAN DEEP THEME - Extends ocean base with deeper, moodier feel
# =============================================================================
#
# Use create_theme() when you want to extend a base theme and only override
# specific properties. This is the simplest approach for quick customization.

{safe_name.upper()}_DEEP_THEME = create_theme(
    id='{safe_name}_ocean_deep',
    name='{class_name} Ocean Deep',
    base='ocean',  # Inherit from ocean theme
    
    # Deeper backgrounds for a moodier atmosphere
    bg='#060d1a',            # Darker navy, almost black
    bg_elevated='#0c1628',   # Deep ocean blue
    bg_soft='#132035',       # Midnight blue
    
    # Accent: keeping ocean's teal but slightly more saturated
    accent='#5afaff',        # Brighter cyan
    accent_soft=hex_to_rgba('#5afaff', 0.12),
    
    # Softer text for less harsh contrast
    text_soft='#6b7a94',     # Muted ocean gray
    
    # Deeper border for that underwater feel
    border_subtle='#1a2744',
)


# =============================================================================
# USAGE NOTES
# =============================================================================
#
# 1. Register in plugin.py on_load():
#        helper.add_theme({safe_name.upper()}_THEME)
#        helper.add_theme({safe_name.upper()}_DEEP_THEME)
#
# 2. Use in report_systems/*.json:
#        "theme": {{ "preset": "{safe_name}_full" }}
#    or:
#        "theme": {{ "preset": "{safe_name}_ocean_deep" }}
#
# 3. Users can override via CLI:
#        bobreview --plugin {name} --theme {safe_name}_ocean_deep
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
    Generate components.py with ComponentInterface implementations.
    
    Creates example components demonstrating:
    - Sync component (StatCardComponent)
    - Async component with data fetching (DataTableComponent)
    - DataFrame integration for data-aware components
    """
    return f'''"""
UI Components for {name} plugin.

Components implement ComponentInterface for reusable UI elements
that templates can render via render_component().

Data Flow:
    Parser → List[Dict] → DataService → DataFrame → Components

Usage in templates:
    {{{{ render_component('stat_card', {{'title': 'Total', 'value': 42}}) }}}}
    {{{{ render_component('data_table', {{'columns': ['name', 'value']}}) }}}}
"""

from typing import Dict, Any, List, Union
from bobreview.core.api import ComponentInterface

# Optional: Import DataFrame for type hints
try:
    from bobreview.core.dataframe import DataFrame
except ImportError:
    DataFrame = None


class {class_name}StatCardComponent(ComponentInterface):
    """
    A stat card component displaying a metric with optional trend indicator.
    
    Props:
        title: Card title (required)
        value: Main numeric value (required)
        subtitle: Optional description text
        trend: 'up', 'down', or None
        status: 'ok', 'warn', 'danger' for border color
    """
    
    @property
    def component_type(self) -> str:
        return '{safe_name}_stat_card'
    
    def render(self, props: Dict[str, Any], context: Dict[str, Any]) -> str:
        title = props.get('title', '')
        value = props.get('value', 0)
        subtitle = props.get('subtitle', '')
        trend = props.get('trend')
        status = props.get('status', '')
        
        # Format value
        if isinstance(value, float):
            formatted = f"{{value:,.1f}}"
        elif isinstance(value, int):
            formatted = f"{{value:,}}"
        else:
            formatted = str(value)
        
        # Trend icon
        trend_html = ''
        if trend == 'up':
            trend_html = '<span class="trend trend-up">↑</span>'
        elif trend == 'down':
            trend_html = '<span class="trend trend-down">↓</span>'
        
        # Status class
        status_class = f' stat-card--{{status}}' if status else ''
        
        # Subtitle HTML (conditional)
        subtitle_html = f'<div class="stat-card__subtitle">{{subtitle}}</div>' if subtitle else ''
        
        return f"""
        <div class="stat-card{{status_class}}">
            <div class="stat-card__title">{{title}}</div>
            <div class="stat-card__value">{{formatted}}{{trend_html}}</div>
            {{subtitle_html}}
        </div>
        """
    
    @staticmethod
    def get_css() -> str:
        """Return component CSS styles."""
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


class {class_name}DataTableComponent(ComponentInterface):
    """
    A data table component that renders DataFrame or List[Dict] data.
    
    Props:
        data: DataFrame or List[Dict] (required)
        columns: List of column names to display (optional, defaults to all)
        max_rows: Maximum rows to show (default: 10)
        title: Optional table title
    
    This component demonstrates DataFrame integration.
    """
    
    @property
    def component_type(self) -> str:
        return '{safe_name}_data_table'
    
    @property
    def is_async(self) -> bool:
        # Set to True if fetching external data
        return False
    
    def render(self, props: Dict[str, Any], context: Dict[str, Any]) -> str:
        data = props.get('data', [])
        columns = props.get('columns')
        max_rows = props.get('max_rows', 10)
        title = props.get('title', '')
        
        # Convert DataFrame to list if needed
        if hasattr(data, '__iter__') and hasattr(data, 'column_names'):
            # It's a DataFrame
            rows = list(data)[:max_rows]
            columns = columns or data.column_names
        else:
            # It's a list
            rows = list(data)[:max_rows]
            if rows and not columns:
                columns = list(rows[0].keys())
        
        if not rows or not columns:
            return '<div class="data-table--empty">No data available</div>'
        
        # Build HTML
        header = ''.join(f'<th>{{col}}</th>' for col in columns)
        body = ''
        for row in rows:
            cells = ''.join(f'<td>{{row.get(col, "")}}</td>' for col in columns)
            body += f'<tr>{{cells}}</tr>'
        
        title_html = f'<caption>{{title}}</caption>' if title else ''
        
        return f"""
        <table class="data-table">
            {{title_html}}
            <thead><tr>{{header}}</tr></thead>
            <tbody>{{body}}</tbody>
        </table>
        """
    
    @staticmethod
    def get_css() -> str:
        """Return component CSS styles."""
        return """
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-elevated);
            border-radius: var(--radius-md);
            overflow: hidden;
        }}
        .data-table caption {{
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            color: var(--text-main);
        }}
        .data-table th {{
            background: var(--bg-soft);
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 500;
            color: var(--text-soft);
            font-size: 0.875rem;
        }}
        .data-table td {{
            padding: 0.75rem 1rem;
            border-top: 1px solid var(--border-subtle);
            color: var(--text-main);
        }}
        .data-table--empty {{
            padding: 2rem;
            text-align: center;
            color: var(--text-soft);
        }}
        """


# =============================================================================
# USAGE
# =============================================================================
#
# 1. Register in plugin.py on_load():
#        from .components import {class_name}StatCardComponent, {class_name}DataTableComponent
#        helper.add_component('{safe_name}_stat_card', {class_name}StatCardComponent)
#        helper.add_component('{safe_name}_data_table', {class_name}DataTableComponent)
#
# 2. Use in templates:
#        {{{{ render_component('{safe_name}_stat_card', {{'title': 'Score', 'value': 85}}) }}}}
#        {{{{ render_component('{safe_name}_data_table', {{'data': data, 'columns': ['name', 'value']}}) }}}}
'''

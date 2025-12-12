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
    imports = """from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper"""
    
    if template == 'full':
        imports += """
from .parsers.csv_parser import {class_name}CsvParser
from .context_builder import {class_name}ContextBuilder
from .chart_generator import {class_name}ChartGenerator
from .theme import {safe_name}_THEME, {safe_name}_DEEP_THEME""".format(class_name=class_name, safe_name=safe_name.upper())
    else:
        imports += f"""
from .parsers.csv_parser import {class_name}CsvParser"""
    
    registration = f'''        # Register data parser
        helper.add_data_parser("{safe_name}_csv", {class_name}CsvParser)'''
    
    if template == 'full':
        registration += f'''
        
        # Register context builder
        helper.add_context_builder("{safe_name}", {class_name}ContextBuilder)
        
        # Register chart generator
        helper.add_chart_generator("{safe_name}", {class_name}ChartGenerator)'''
    
    registration += '''
        
        # Register templates
        template_dir = Path(__file__).parent / "templates"
        helper.add_templates(template_dir)
        
        # Register report systems
        report_systems_dir = Path(__file__).parent / "report_systems"
        helper.add_report_systems_from_dir(report_systems_dir)
        
        # Register default services
        helper.register_default_services()'''
    
    if template == 'full':
        # Add theme registration for full template
        registration += f'''
        
        # Register custom themes (see theme.py for customization)
        helper.add_theme({safe_name.upper()}_THEME)       # Full standalone theme
        helper.add_theme({safe_name.upper()}_DEEP_THEME)  # Ocean-based deep theme'''
    
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

from typing import Dict, List, Any
from bobreview.core.api import ContextBuilderInterface


class {class_name}ContextBuilder(ContextBuilderInterface):
    """Build template context for {name} reports."""
    
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enriched context for template rendering."""
        context = dict(base_context)
        
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
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME


class ''' + class_name + '''ChartGenerator(ChartGeneratorInterface):
    """Generate Chart.js JavaScript code with theme support."""
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate Chart.js JavaScript code.
        
        Returns JavaScript code that creates the chart, NOT JSON config.
        """
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
        
        # Build JavaScript code
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
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
'''


def generate_analysis_module(name: str, safe_name: str) -> str:
    """Generate analysis module with statistical functions."""
    return f'''"""
Statistical Analysis for {name} Plugin.

Provides common statistical functions for data analysis.
Register with: get_analyzer_registry().register('{safe_name}', analyze_{safe_name}_data)
"""

from typing import List, Dict, Any
import statistics


def analyze_{safe_name}_data(
    data_points: List[Dict[str, Any]],
    config: Any = None
) -> Dict[str, Any]:
    """
    Compute statistics from parsed data.
    
    Parameters:
        data_points: List of parsed data points with 'score' field
        config: Optional ReportConfig
    
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
    
    # Fonts - modern, clean typography
    font_sans='"Plus Jakarta Sans", "Inter", system-ui, -apple-system, sans-serif',
    font_mono='"JetBrains Mono", "Fira Code", "SF Mono", Consolas, monospace',
    
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


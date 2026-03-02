"""
Generators for plugin component files.

Creates:
- analysis.py (statistical analysis)
- widgets.py (custom widget examples)
- components.py (Property Controls pattern)
"""


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
        
        import html
        status_class = f"stat-{{status}}" if status != "neutral" else ""
        
        return f"""
        <div class="stat-card {{status_class}}">
            <div class="stat-card__title">{{html.escape(str(title))}}</div>
            <div class="stat-card__value">{{html.escape(str(value))}} {{trend_icon}}</div>
            <div class="stat-card__subtitle">{{html.escape(str(subtitle))}}</div>
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
        .stat-card.stat-ok {{ border-color: var(--ok); }}
        .stat-card.stat-warn {{ border-color: var(--warn); }}
        .stat-card.stat-danger {{ border-color: var(--danger); }}
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
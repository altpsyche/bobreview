# BobReview Plugin Development Guide

This guide walks through creating a custom report plugin for BobReview, using the `mayhem-reports` plugin as a reference implementation.

## Table of Contents

1. [Overview](#overview)
2. [Plugin Structure](#plugin-structure)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Component Reference](#component-reference)
5. [Testing](#testing)

---

## Overview

A BobReview plugin generates HTML reports from data files. The plugin system supports:

- Custom data parsers (CSV, JSON, PNG filenames, etc.)
- Statistical analysis functions
- Chart.js chart generation
- Multi-page HTML reports with themes
- LLM-generated content integration

### Data Flow

```
Data Files → Parser → Data Points → Analyzer → Statistics
                                         ↓
                            Context Builder → Template Context
                                         ↓
                            Chart Generator → Chart JS Code
                                         ↓
                            Jinja2 Templates → HTML Pages
```

---

## Plugin Structure

```
bobreview/plugins/your_plugin/
├── __init__.py              # Package init, exports plugin class
├── manifest.json            # Plugin metadata and capabilities
├── plugin.py                # Main plugin class with registrations
├── parsers/
│   ├── __init__.py
│   └── your_parser.py       # Data file parser
├── analysis.py              # Statistical analysis function
├── context_builder.py       # Template context preparation
├── chart_generator.py       # Chart.js code generator
├── report_systems/
│   └── your_report.json     # Report configuration
├── templates/
│   ├── your_plugin/
│   │   ├── pages/
│   │   │   ├── base.html.j2
│   │   │   ├── home.html.j2
│   │   │   └── *.html.j2
│   │   └── static/
│   │       └── plugin.css
│   └── components/
│       └── macros.html.j2
└── sample_data/
```

---

## Step-by-Step Guide

### Step 1: Create Plugin Scaffold

```bash
bobreview plugins create my-plugin
```

### Step 2: Define manifest.json

```json
{
    "id": "my-plugin",
    "name": "My Custom Reports",
    "version": "1.0.0",
    "description": "Generate reports from custom data format",
    "author": "Your Name",
    "provides": [
        "report_systems",
        "templates", 
        "parsers",
        "chart_generators",
        "context_builders"
    ]
}
```

**Capability Options:**
- `report_systems` - JSON configuration files
- `templates` - Jinja2 HTML templates
- `parsers` - Data file parsers
- `chart_generators` - Chart.js code generators
- `context_builders` - Template context builders
- `themes` - Custom color themes
- `llm_generators` - AI content generators

### Step 3: Create the Parser

```python
# parsers/my_parser.py
from bobreview.core.api import ParserInterface
from typing import List, Dict, Any
from pathlib import Path

class MyParser(ParserInterface):
    """Parse data from custom file format."""
    
    def parse(self, directory: Path, pattern: str = None) -> List[Dict[str, Any]]:
        data_points = []
        
        for file_path in directory.glob("*.csv"):
            point = self._parse_file(file_path)
            if point:
                data_points.append(point)
        
        return data_points
    
    def _parse_file(self, file_path: Path) -> Dict[str, Any]:
        return {
            "name": file_path.stem,
            "value": 100,
            "category": "A",
            "timestamp": "2024-01-01"
        }
```

### Step 4: Create the Analyzer

```python
# analysis.py
from typing import List, Dict, Any
import statistics

def analyze_my_data(data_points: List[Dict[str, Any]], config=None) -> Dict[str, Any]:
    values = [p.get('value', 0) for p in data_points]
    
    if not values:
        return {'count': 0}
    
    sorted_values = sorted(values)
    n = len(values)
    
    return {
        'count': n,
        'value': {
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'stdev': statistics.stdev(values) if n > 1 else 0,
            'q1': sorted_values[n // 4],
            'q3': sorted_values[3 * n // 4],
            'p90': sorted_values[int(n * 0.9)],
            'p95': sorted_values[int(n * 0.95)],
        },
        'high_values': [(i, p) for i, p in enumerate(data_points) if p['value'] > 100],
        'low_values': [(i, p) for i, p in enumerate(data_points) if p['value'] < 50],
    }
```

### Step 5: Create Report System JSON

```json
{
    "schema_version": "1.0",
    "id": "my_report",
    "name": "My Custom Report",
    "version": "1.0.0",
    
    "data_source": {
        "type": "my_parser",
        "input_format": "csv",
        "fields": {
            "name": {"type": "string", "required": true},
            "value": {"type": "number", "required": true}
        }
    },
    
    "thresholds": {
        "high_threshold": 100,
        "low_threshold": 50
    },
    
    "labels": {
        "title": "My Report",
        "value": "Score"
    },
    
    "pages": [
        {
            "id": "home",
            "filename": "index.html",
            "nav_label": "Overview",
            "nav_order": 10,
            "template": {
                "type": "jinja2",
                "name": "my_plugin/pages/home.html.j2"
            },
            "data_requirements": {
                "data_points": false,
                "images": false
            },
            "enabled": true
        },
        {
            "id": "details",
            "filename": "details.html",
            "nav_label": "Details",
            "nav_order": 20,
            "card_icon": "fa-chart-bar",
            "card_description": "Detailed breakdown.",
            "template": {
                "type": "jinja2",
                "name": "my_plugin/pages/details.html.j2"
            },
            "charts": [
                {
                    "id": "value_histogram",
                    "type": "histogram",
                    "title": "Value Distribution",
                    "y_field": "value"
                }
            ],
            "data_requirements": {
                "data_points": true,
                "images": false
            },
            "enabled": true
        }
    ],
    
    "theme": {
        "preset": "terminal"
    }
}
```

### Step 6: Create Chart Generator

```python
# chart_generator.py
import json
from typing import Dict, List, Any
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME

class MyChartGenerator(ChartGeneratorInterface):
    
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        chart_id = chart_config.get('id', 'chart')
        title = chart_config.get('title', 'Chart')
        y_field = chart_config.get('y_field', 'value')
        
        theme = get_theme_by_id('terminal') or DARK_THEME
        
        labels = [p.get('name', f'#{i}') for i, p in enumerate(data_points)]
        values = [p.get(y_field, 0) for p in data_points]
        
        # Must return JavaScript code, not JSON
        return f"""
(function() {{
    const ctx = document.getElementById('{chart_id}').getContext('2d');
    new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(labels)},
            datasets: [{{
                label: {json.dumps(title)},
                data: {json.dumps(values)},
                backgroundColor: '{self._hex_to_rgba(theme.accent, 0.7)}',
                borderColor: '{theme.accent}',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false
        }}
    }});
}})();
"""
    
    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
```

### Step 7: Create Context Builder

```python
# context_builder.py
from typing import Dict, Any, List
from bobreview.core.api import ContextBuilderInterface

class MyContextBuilder(ContextBuilderInterface):
    
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        page_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        critical = None
        if data_points:
            critical_idx = max(range(len(data_points)), 
                              key=lambda i: data_points[i].get('value', 0))
            critical = {'index': critical_idx, **data_points[critical_idx]}
        
        return {
            'critical': critical,
            'total_count': len(data_points),
            'high_count': len(stats.get('high_values', [])),
            'low_count': len(stats.get('low_values', [])),
        }
```

### Step 8: Create Base Template

```jinja2
{# templates/my_plugin/pages/base.html.j2 #}
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{% block title %}{{ config.title }}{% endblock %}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  {% block head_scripts %}{% endblock %}
  
  <style>{{ theme_css|safe }}</style>
  <style>{{ base_css|safe }}</style>
  <style>{{ plugin_css|safe }}</style>
</head>
<body>
  <div class="page">
    <header>
      <h1>{{ config.title }}</h1>
      <p class="meta">Generated {{ generation_date }}</p>
    </header>
    
    <nav class="nav-links">
      {% for page in pages %}
      <a href="{{ page.filename }}" 
         class="{% if current_page == page.id %}active{% endif %}">
        {{ page.nav_label }}
      </a>
      {% endfor %}
    </nav>
    
    {% block content %}{% endblock %}
    
    <div class="footer">{{ labels.footer_text }}</div>
  </div>
  
  {% block scripts %}{% endblock %}
</body>
</html>
```

### Step 9: Create Page Template

```jinja2
{# templates/my_plugin/pages/home.html.j2 #}
{% extends "my_plugin/pages/base.html.j2" %}
{% from "components/macros.html.j2" import stat_card %}

{% block title %}{{ config.title }} - Overview{% endblock %}

{% block content %}
<section class="panel">
  <h2>Summary</h2>
  
  <div class="stats-grid">
    {{ stat_card('Total Items', stats.count) }}
    {{ stat_card('Average', stats.value.mean|format_number(1)) }}
    {{ stat_card('High Performers', high_count, variant='ok') }}
    {{ stat_card('Needs Work', low_count, variant='danger') }}
  </div>
</section>
{% endblock %}
```

### Step 10: Register Components

```python
# plugin.py
from pathlib import Path
from bobreview.core.plugin_system.base import BasePlugin
from bobreview.core.plugin_system.helper import PluginHelper

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def on_load(self, registry) -> None:
        helper = PluginHelper(registry, self.name)
        
        from .parsers.my_parser import MyParser
        helper.add_data_parser('my_parser', MyParser)
        
        from .analysis import analyze_my_data
        from bobreview.core.plugin_system.registries import get_analyzer_registry
        get_analyzer_registry().register('my_analyzer', analyze_my_data)
        
        from .chart_generator import MyChartGenerator
        helper.add_chart_generator('my_report', MyChartGenerator)
        
        from .context_builder import MyContextBuilder
        helper.add_context_builder('my_report', MyContextBuilder)
        
        template_dir = Path(__file__).parent / 'templates'
        helper.add_templates(template_dir)
        
        helper.add_builtin_themes()
        
        report_dir = Path(__file__).parent / 'report_systems'
        helper.add_report_systems(report_dir)
```

---

## Component Reference

### Theme CSS Variables

| Variable | Purpose |
|----------|---------|
| `--bg` | Main background |
| `--bg-elevated` | Card backgrounds |
| `--bg-soft` | Secondary backgrounds |
| `--accent` | Primary accent color |
| `--accent-strong` | Secondary accent |
| `--text-main` | Primary text |
| `--text-soft` | Secondary text |
| `--ok` | Success (green) |
| `--warn` | Warning (yellow) |
| `--danger` | Error (red) |
| `--border-subtle` | Border color |

### Template Context Variables

| Variable | Type | Description |
|----------|------|-------------|
| `config` | object | ReportConfig with thresholds, title |
| `stats` | dict | Computed statistics from analyzer |
| `data_points` | list | Raw parsed data points |
| `images` | dict | Embedded images (base64) |
| `labels` | dict | UI labels from JSON |
| `pages` | list | All page configs for navigation |
| `current_page` | str | Current page ID |
| `llm` | dict | LLM-generated content |
| `charts` | dict | Generated chart JS code |
| `theme_css` | str | Theme CSS variables |
| `has_images` | bool | Whether images are available |

### Chart Types

| Type | Description | Fields |
|------|-------------|--------|
| `bar` | Vertical bar chart | `y_field` |
| `histogram` | Distribution histogram | `y_field` |
| `timeline` | Line chart over time | `y_field` |
| `scatter` | X-Y scatter plot | `x_field`, `y_field` |

---

## Testing

### Run with Dry Run Mode

```bash
bobreview --plugin my-plugin --dir ./path/to/data --dry-run
```

### Verbose Output

```bash
bobreview --plugin my-plugin --dir ./data --dry-run --verbose
```

### Verify Plugin Import

```bash
python -c "from bobreview.plugins.my_plugin import MyPlugin; print('OK')"
```

---

## Reference Implementation

See `bobreview/plugins/mayhem_reports/` for a complete working example.

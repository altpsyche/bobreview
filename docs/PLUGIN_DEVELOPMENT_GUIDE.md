# BobReview Plugin Development Guide

This guide walks through creating a custom report plugin for BobReview using the CLI scaffolder and PluginHelper API.

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

### Architecture: Two Configuration Layers

BobReview uses **two separate configuration files** for different audiences:

| Configuration | Created By | Purpose | Format |
|--------------|------------|---------|--------|
| **Report System JSON** | Plugin Developer | Define plugin capabilities | `report_systems/*.json` |
| **Report Config YAML** | End User | Compose pages from components | `report_config.yaml` |

```
┌─────────────────────────────────────────────────────────────────┐
│  PLUGIN DEVELOPER LAYER                                         │
│  report_systems/my_plugin.json                                  │
│  ───────────────────────────────────────────────────────────    │
│  • data_source: what data types plugin supports (CSV, FBX...)  │
│  • llm_generators (summary, recommendations, custom)            │
│  • widgets, charts, analyzers available                         │
│  • default theme configuration                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  END USER LAYER                                                  │
│  report_config.yaml                                              │
│  ───────────────────────────────────────────────────────────    │
│  • plugin: "my-plugin" ← which plugin to use (REQUIRED)         │
│  • data_source: "./data/*.csv" ← user's data                    │
│  • pages: [...] ← which pages to include                        │
│  • components: [...] ← what to show on each page                │
└─────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Plugins are always required.** Users cannot create reports without a plugin.
> The plugin defines what data types are supported and what components are available.

---

## Plugin Structure

```
~/.bobreview/plugins/your_plugin/
├── __init__.py              # Package init, exports plugin class
├── manifest.json            # Plugin metadata and capabilities
├── report_config.yaml       # User-editable report config (pages, charts, LLM)
├── plugin.py                # Main plugin class with registrations
├── parsers/
│   ├── __init__.py
│   └── your_parser.py       # Data file parser
├── analysis.py              # Statistical analysis function
├── context_builder.py       # Template context preparation
├── chart_generator.py       # Chart.js code generator
├── report_systems/
│   └── your_report.json     # Report system definition (plugin capabilities)
├── templates/
│   ├── your_plugin/
│   │   ├── pages/
│   │   │   ├── base.html.j2
│   │   │   ├── overview.html.j2
│   │   │   └── details.html.j2
│   │   └── static/
│   │       └── plugin.css
│   └── components/
│       └── macros.html.j2
└── sample_data/
    └── sample.csv           # Sample data to test with
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
from bobreview.core.api import DataParserInterface
from typing import List, Dict, Any
from pathlib import Path

class MyCsvParser(DataParserInterface):
    """Parse data from CSV files."""
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single CSV file."""
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if rows:
            return rows[0]  # Return first row as example
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Find all CSV files in directory."""
        return sorted(directory.glob("*.csv"))
```

### Step 4: Create the Analyzer

```python
# analysis.py
from typing import List, Dict, Any
import statistics

def analyze_my_data(
    data_points: List[Dict[str, Any]],
    config=None,
    **kwargs  # Accept metrics, metric_config from AnalyticsService
) -> Dict[str, Any]:
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
            "id": "overview",
            "filename": "overview.html",
            "nav_label": "Overview",
            "nav_order": 10,
            "template": {
                "type": "jinja2",
                "name": "my_plugin/pages/overview.html.j2"
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

### Step 5a: Create Custom Themes (Optional)

Plugins can define custom themes. The scaffolder generates two examples when using `bobreview plugins create --template full`:

**Approach 1: Full Standalone Theme** (complete control with fonts, radii, shadows)

```python
# theme.py
from bobreview.core.themes import ReportTheme, hex_to_rgba

MY_PLUGIN_THEME = ReportTheme(
    id='my_plugin_full',
    name='My Plugin Theme',
    
    # Backgrounds
    bg='#0a0e14',
    bg_elevated='#12171f',
    bg_soft='#1a2028',
    
    # Accents
    accent='#00d4aa',
    accent_soft=hex_to_rgba('#00d4aa', 0.15),
    accent_strong='#00ffcc',
    
    # Text
    text_main='#e8eaed',
    text_soft='#9aa0a6',
    
    # Status colors
    ok='#34d399',
    ok_soft=hex_to_rgba('#34d399', 0.15),
    warn='#fbbf24',
    warn_soft=hex_to_rgba('#fbbf24', 0.15),
    danger='#f87171',
    danger_soft=hex_to_rgba('#f87171', 0.15),
    
    # Fonts (Google Fonts URL enables dynamic loading)
    font_family='"Space Grotesk", system-ui, sans-serif',
    font_mono='"IBM Plex Mono", monospace',
    font_url='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap',
)
```

**Approach 2: Extend a Base Theme** (quick customization)

```python
from bobreview.core.themes import create_theme, hex_to_rgba

MY_PLUGIN_DEEP_THEME = create_theme(
    id='my_plugin_ocean_deep',
    name='My Plugin Ocean Deep',
    base='ocean',  # Inherit from ocean theme
    
    # Only override what you need
    bg='#060d1a',
    bg_elevated='#0c1628',
    accent='#5afaff',
    accent_soft=hex_to_rgba('#5afaff', 0.12),
)
```

**Register in plugin.py:**

```python
from .theme import MY_PLUGIN_THEME, MY_PLUGIN_DEEP_THEME

def on_load(self, registry):
    helper = PluginHelper(registry, self.name)
    helper.add_theme(MY_PLUGIN_THEME)
    helper.add_theme(MY_PLUGIN_DEEP_THEME)
```

**Available base themes:** `dark`, `light`, `ocean`, `purple`, `terminal`, `sunset`

| Property | Description |
|----------|-------------|
| `accent` | Primary accent (buttons, links) |
| `accent_soft` | Translucent accent for backgrounds |
| `bg`, `bg_elevated`, `bg_soft` | Background colors |
| `text_main`, `text_soft` | Text colors |
| `ok`, `warn`, `danger` + `_soft` | Status colors |
| `font_family`, `font_mono` | Font families |
| `font_url` | Google Fonts URL (enables dynamic font loading) |
| `radius_sm/md/lg/xl` | Border radii |
| `shadow_soft`, `shadow_strong` | Box shadows |


### Step 6: Create Chart Generator


```python
# chart_generator.py
import json
from typing import Dict, List, Any, Union
from bobreview.core.api import ChartGeneratorInterface
from bobreview.core.themes import get_theme_by_id, DARK_THEME

class MyChartGenerator(ChartGeneratorInterface):
    
    def generate_chart(
        self,
        data: Union[List[Dict[str, Any]], Any],  # DataFrame or List[Dict]
        stats: Dict[str, Any],
        config: Any,
        chart_config: Dict[str, Any]
    ) -> str:
        # Convert to list for internal use
        data_points = list(data) if hasattr(data, '__iter__') else data
        
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
        """Convert hex color to rgba string."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
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
        data: Union[List[Dict[str, Any]], Any],  # DataFrame or List[Dict]
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Convert to list for internal use
        data_points = list(data) if hasattr(data, '__iter__') else data
        
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
{# templates/my_plugin/pages/overview.html.j2 #}
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
import json
from bobreview.core.plugin_system import BasePlugin, PluginHelper

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def on_load(self, registry) -> None:
        helper = PluginHelper(registry, self.name)
        
        # Import components
        from .parsers.my_parser import MyParser
        from .analysis import analyze_my_data
        from .context_builder import MyContextBuilder
        from .chart_generator import MyChartGenerator
        
        # Load report system definition
        report_system_path = Path(__file__).parent / "report_systems" / "my_plugin.json"
        with open(report_system_path) as f:
            system_def = json.load(f)
        
        # Register everything in one call
        helper.setup_complete_report_system(
            system_id="my_plugin",
            system_def=system_def,
            parser_class=MyParser,
            analyzer_func=analyze_my_data,
            context_builder_class=MyContextBuilder,
            chart_generator_class=MyChartGenerator,
            template_dir=Path(__file__).parent / "templates"
        )
        
        # Register themes
        helper.add_builtin_themes()
        
        # Register default services
        helper.register_default_services()
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
| `config` | object | Config with thresholds, title |
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
python -c "from my_plugin.plugin import MyPlugin; print('OK')"
```

---

## Reference Implementation

Use `bobreview plugins create my-plugin --template full` to generate a complete working example.

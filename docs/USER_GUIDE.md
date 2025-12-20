# BobReview User Configuration Guide

This guide explains how to customize your reports using `report_config.yaml` after creating a plugin.

---

## Overview

When you create a plugin with `bobreview plugins create my-plugin`, a `report_config.yaml` file is generated. This file controls:

- **Pages** - What pages appear in your report
- **Components** - Charts, tables, LLM content, and widgets on each page
- **Theme** - Visual appearance
- **Data source** - Where to find data files

---

## Basic Structure

```yaml
name: "My Report"
plugin: my_plugin
data_source: "./sample_data/*.csv"
output_dir: "./output"
theme: dark

pages:
  - id: overview
    title: "Overview"
    layout: grid
    nav_order: 1
    components:
      - type: chart
        id: score_chart
        chart: bar
        title: "Scores"
        x: name
        y: score
```

---

## Pages

Add pages to the `pages` array:

```yaml
pages:
  - id: my_page          # Unique ID (used in filename)
    title: "My Page"     # Display title
    layout: grid         # grid | flex | single-column
    nav_order: 3         # Navigation order (lower = first)
    enabled: true        # Set false to disable
    components: []       # List of components
```

### Page Layouts

| Layout | Description |
|--------|-------------|
| `grid` | Responsive cards that wrap |
| `flex` | Horizontal layout |
| `single-column` | Stacked vertically |

---

## Components

### Charts

```yaml
- type: chart
  id: my_chart           # Required: must match template
  chart: bar             # Chart type
  title: "My Chart"
  x: name                # X-axis field from data
  y: score               # Y-axis field from data
```

**Chart Types:**

| Type | Description |
|------|-------------|
| `bar` | Vertical bars |
| `line` | Line with gradient fill |
| `histogram` | Distribution (auto-binned) |
| `doughnut` | Pie chart grouped by category |
| `scatter` | X-Y scatter plot |

> **Important:** Chart IDs must match what the template expects. Default templates use:
> - Overview: `score_chart`, `trend_chart`
> - Details: `distribution_chart`, `category_chart`

### LLM Content

```yaml
- type: llm
  id: summary
  title: "Executive Summary"
  prompt: "Analyze {{name}} and {{score}} data. Provide insights."
```

**Field References:** Use `{{field}}` syntax to include data columns in prompts.

### Data Tables

```yaml
- type: data_table
  columns:
    - name
    - score
    - category
  sortable: true
  paginated: true
  page_size: 10
```

### Stat Widgets

```yaml
- type: widget
  widget: stat_card
  config:
    title: "Total Items"
    value: "{{ data_points | length }}"
    subtitle: "in dataset"
    status: ok           # ok | warn | danger | neutral
    trend: up            # up | down | (empty)
```

---

## Themes

Set the theme in your config:

```yaml
theme: dark
```

**Built-in Themes:** `dark`, `light`, `ocean`, `purple`, `terminal`, `sunset`, `high_contrast`

---

## Adding Custom Charts

If you add a chart with a new ID, you must update the template to render it.

1. Add the chart in YAML:
   ```yaml
   - type: chart
     id: custom_chart
     chart: bar
     title: "Custom Chart"
     x: name
     y: score
   ```

2. Edit the template (`templates/{plugin}/pages/overview.html.j2`):
   ```jinja2
   <div class="chart-container">
       <canvas id="custom_chart"></canvas>
   </div>
   
   {% block scripts %}
   <script>
   {% if charts.custom_chart %}{{ charts.custom_chart | safe }}{% endif %}
   </script>
   {% endblock %}
   ```

---

## Template Variables

Use these in widget values with `{{ }}` syntax:

| Variable | Description |
|----------|-------------|
| `data_points` | List of all data items |
| `data_points \| length` | Number of items |
| `stats.score.mean` | Average score |
| `stats.score.min` | Minimum score |
| `stats.score.max` | Maximum score |
| `stats.score.median` | Median score |
| `stats.count` | Total count |
| `llm.summary` | LLM-generated summary |
| `llm.recommendations` | LLM recommendations |

---

## Complete Example

```yaml
name: "Performance Report"
plugin: my_plugin
data_source: "./data/*.csv"
output_dir: "./reports"
theme: ocean
version: "1.0"
author: "Your Name"

pages:
  - id: overview
    title: "Overview"
    layout: grid
    nav_order: 1
    components:
      - type: widget
        widget: stat_card
        config:
          title: "Total Items"
          value: "{{ data_points | length }}"
      
      - type: chart
        id: score_chart
        chart: bar
        title: "Scores by Item"
        x: name
        y: score
      
      - type: llm
        id: summary
        title: "Summary"
        prompt: "Summarize the {{name}} and {{score}} data."

  - id: details
    title: "Details"
    layout: single-column
    nav_order: 2
    components:
      - type: chart
        id: distribution_chart
        chart: histogram
        title: "Score Distribution"
        y: score
      
      - type: data_table
        columns: [name, score, category]
        sortable: true
```

---

## Running Your Report

```bash
bobreview --plugin my_plugin --dir ./data
```

Or from the plugin directory:

```bash
cd ~/.bobreview/plugins/my_plugin/sample_data
bobreview --plugin my_plugin
```

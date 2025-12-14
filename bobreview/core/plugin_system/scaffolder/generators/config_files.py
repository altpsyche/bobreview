"""
Configuration file generators for plugin scaffolding.

Generates JSON/configuration structures:
- manifest.json
- report_system.json
"""

from typing import Dict, Any, Literal


def generate_manifest(
    name: str,
    safe_name: str,
    class_name: str,
    template: Literal['minimal', 'full']
) -> Dict[str, Any]:
    """Generate manifest.json content as a dictionary."""
    manifest = {
        "name": name,
        "version": "1.0.0",
        "author": "Your Name",
        "description": f"Plugin for {name}",
        "entry_point": f"plugin:{class_name}Plugin",
        "dependencies": [],
        "provides": {
            "report_systems": [safe_name],
            "data_parsers": [f"{safe_name}_csv"],
        }
    }
    
    if template == 'full':
        manifest["provides"]["context_builders"] = [safe_name]
        manifest["provides"]["chart_generators"] = [safe_name]
    
    return manifest


def generate_report_system(name: str, safe_name: str, color_theme: str = 'dark') -> Dict[str, Any]:
    """Generate report system JSON with theme preset support."""
    return {
        "schema_version": "1.0",
        "id": safe_name,
        "name": f"{name} Report",
        "version": "1.0.0",
        "description": f"Report system for {name}",
        "author": "Your Name",
        
        "data_source": {
            "type": f"{safe_name}_csv",
            "input_format": "csv",
            "fields": {
                "name": {"type": "string", "required": True},
                "score": {"type": "float", "required": True},
                "category": {"type": "string", "required": False}
            }
        },
        
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2000,
            "chunk_size": 10
        },
        
        "llm_generators": [
            {
                "id": "summary",
                "name": "Summary",
                "description": "Executive summary of the data analysis",
                "prompt_template": f"Analyze this {name} data and provide a brief executive summary. Highlight key trends, outliers, and notable patterns.",
                "data_table": {
                    "columns": ["name", "score"],
                    "sample_strategy": "all",
                    "max_rows": 50
                },
                "returns": "string",
                "enabled": True
            },
            {
                "id": "recommendations",
                "name": "Recommendations",
                "description": "Actionable recommendations based on the data",
                "prompt_template": f"Based on this {name} data, provide 3-5 actionable recommendations for improvement.",
                "data_table": {
                    "columns": ["name", "score"],
                    "sample_strategy": "all",
                    "max_rows": 50
                },
                "returns": "string",
                "enabled": True
            }
        ],
        
        "theme": {
            "preset": color_theme  # dark, ocean, purple, terminal, sunset
        },
        
        # Pages define report structure
        "pages": [
            {
                "id": "home",
                "filename": "index.html",
                "nav_label": "Overview",
                "nav_order": 1,
                "template": {
                    "type": "jinja2",
                    "name": f"{safe_name}/pages/home.html.j2"
                },
                "llm_content": ["summary", "recommendations"],
                "charts": [
                    {
                        "id": "score_chart",
                        "type": "bar",
                        "title": "Scores Overview",
                        "x_field": "name",
                        "y_field": "score"
                    },
                    {
                        "id": "trend_chart",
                        "type": "line",
                        "title": "Score Trend",
                        "x_field": "name",
                        "y_field": "score"
                    }
                ]
            },
            {
                "id": "details",
                "filename": "details.html",
                "nav_label": "Details",
                "nav_order": 2,
                "template": {
                    "type": "jinja2",
                    "name": f"{safe_name}/pages/details.html.j2"
                },
                "charts": [
                    {
                        "id": "distribution_chart",
                        "type": "histogram",
                        "title": "Score Distribution",
                        "y_field": "score"
                    },
                    {
                        "id": "category_chart",
                        "type": "doughnut",
                        "title": "By Category",
                        "x_field": "category",
                        "y_field": "score"
                    }
                ]
            }
        ],
        
        "output": {
            "default_filename": f"{safe_name}_report.html"
        }
    }


def generate_user_report_config(name: str, safe_name: str, color_theme: str = 'dark') -> str:
    """
    Generate a user-facing report_config.yaml for end users.
    
    This is the CMS-style config that end users edit to compose reports
    from plugin-provided components.
    """
    return f'''# ═══════════════════════════════════════════════════════════════════════════════
# {name.upper()} REPORT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
#
# This YAML file lets you customize your report without coding.
# Edit pages, add charts, configure LLM content — all by editing this file.
#
# QUICK START:
#   1. Edit the sections below to customize your report
#   2. Run: bobreview --plugin {safe_name} --dir ./sample_data
#   3. Open the generated HTML report
#
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────────
# REPORT SETTINGS
# ─────────────────────────────────────────────────────────────────────────────────

name: "{name} Report"
plugin: "{safe_name}"
data_source: "./sample_data/*.csv"    # Path to your data files (supports glob patterns)
output_dir: "./output"                 # Where to save generated HTML

# THEME OPTIONS: dark, light, ocean, purple, terminal, sunset
theme: "{color_theme}"

# Optional metadata (shown in report footer)
version: "1.0"
author: ""
description: "Generated report for {name} data analysis"

# ─────────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────────
#
# Each page becomes an HTML file with navigation links.
#
# PAGE PROPERTIES:
#   id:         Unique identifier (used in URLs)
#   title:      Page title shown in nav and header
#   layout:     grid | flex | single-column
#   nav_order:  Sort order in navigation (lower = first)
#   components: List of widgets, charts, tables, or LLM content
#
# ─────────────────────────────────────────────────────────────────────────────────

pages:
  # ┌─────────────────────────────────────────────────────────────────────────────┐
  # │ OVERVIEW PAGE                                                                │
  # └─────────────────────────────────────────────────────────────────────────────┘
  - id: overview
    title: "Overview"
    layout: grid           # grid = responsive cards, flex = horizontal, single-column = stacked
    nav_order: 1
    components:
      # ── STAT CARDS ──────────────────────────────────────────────────────────────
      # Display key metrics in highlighted cards
      #
      # OPTIONS:
      #   title:    Card header
      #   value:    Number or template expression like {{{{ stats.score.mean }}}}
      #   subtitle: Small text below value
      #   status:   ok (green) | warn (yellow) | danger (red) | neutral
      #   trend:    up | down | (empty for no arrow)
      
      - type: widget
        widget: stat_card
        config:
          title: "Total Items"
          value: "{{{{ data_points | length }}}}"
          subtitle: "in dataset"
      
      - type: widget
        widget: stat_card
        config:
          title: "Average Score"
          value: "{{{{ stats.score.mean | round(1) }}}}"
          subtitle: "across all items"
          status: ok

      - type: widget
        widget: stat_card
        config:
          title: "Highest Score"
          value: "{{{{ stats.score.max }}}}"
          status: ok
          trend: up

      - type: widget
        widget: stat_card
        config:
          title: "Lowest Score"
          value: "{{{{ stats.score.min }}}}"
          status: warn
          trend: down

      # ── CHARTS ──────────────────────────────────────────────────────────────────
      # Visualize your data with Chart.js
      #
      # CHART TYPES:
      #   bar       - Vertical bars comparing values
      #   line      - Trend line with gradient fill
      #   histogram - Distribution of values (auto-binned)
      #   doughnut  - Pie chart grouped by category
      #   scatter   - X-Y scatter plot
      #
      # OPTIONS:
      #   title: Chart title
      #   x:     Field for X-axis (e.g., name, category)
      #   y:     Field for Y-axis (e.g., score, value)

      - type: chart
        chart: bar
        title: "Scores by Item"
        x: name
        y: score

      - type: chart
        chart: line
        title: "Score Trend"
        x: name
        y: score

      # ── LLM CONTENT ─────────────────────────────────────────────────────────────
      # AI-generated insights using your configured LLM provider
      #
      # AVAILABLE GENERATORS (defined in report_systems/{safe_name}.json):
      #   summary         - Executive summary of the data
      #   recommendations - Actionable recommendations
      #
      # To add more generators, edit report_systems/{safe_name}.json

      - type: llm
        generator: summary

  # ┌─────────────────────────────────────────────────────────────────────────────┐
  # │ DETAILS PAGE                                                                 │
  # └─────────────────────────────────────────────────────────────────────────────┘
  - id: details
    title: "Details"
    layout: single-column
    nav_order: 2
    components:
      # ── HISTOGRAM ───────────────────────────────────────────────────────────────
      - type: chart
        chart: histogram
        title: "Score Distribution"
        y: score

      # ── CATEGORY BREAKDOWN ──────────────────────────────────────────────────────
      - type: chart
        chart: doughnut
        title: "By Category"
        x: category
        y: score

      # ── DATA TABLE ──────────────────────────────────────────────────────────────
      # Display raw data in a sortable table
      #
      # OPTIONS:
      #   columns:   List of field names to show
      #   sortable:  Enable column sorting (true/false)
      #   paginated: Enable pagination (true/false)
      #   page_size: Rows per page (default: 25)

      - type: data_table
        columns:
          - name
          - score
          - category
        sortable: true
        paginated: true
        page_size: 10

      # ── LLM RECOMMENDATIONS ─────────────────────────────────────────────────────
      - type: llm
        generator: recommendations

# ═══════════════════════════════════════════════════════════════════════════════
# HOW TO ADD MORE PAGES
# ═══════════════════════════════════════════════════════════════════════════════
#
# Copy this template and add to the pages list above:
#
#   - id: my_new_page
#     title: "My New Page"
#     layout: grid
#     nav_order: 3
#     components:
#       - type: chart
#         chart: bar
#         title: "My Chart"
#         x: name
#         y: score
#
# ═══════════════════════════════════════════════════════════════════════════════
# AVAILABLE TEMPLATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════
#
# Use these in widget values with {{{{ }}}} syntax:
#
#   data_points             - List of all data items
#   data_points | length    - Number of items
#   stats.score.mean        - Average score
#   stats.score.min         - Minimum score
#   stats.score.max         - Maximum score
#   stats.score.median      - Median score
#   stats.count             - Total count
#
# ═══════════════════════════════════════════════════════════════════════════════
'''


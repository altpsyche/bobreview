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
    """
    Generate report system JSON for plugin developers.
    
    This JSON defines CAPABILITIES that the plugin provides:
    - Data source configuration (parser type, fields)
    - LLM generators (prompts for AI-generated content)
    - Theme preset
    
    Pages and components are defined by USERS in report_config.yaml.
    """
    return {
        "schema_version": "1.0",
        "id": safe_name,
        "name": f"{name} Report",
        "version": "1.0.0",
        "description": f"Report system for {name}",
        "author": "Your Name",
        
        # ─────────────────────────────────────────────────────────────────────
        # DATA SOURCE
        # Defines how data files are parsed
        # ─────────────────────────────────────────────────────────────────────
        "data_source": {
            "type": f"{safe_name}_csv",
            "input_format": "csv",
            "fields": {
                "name": {"type": "string", "required": True},
                "score": {"type": "float", "required": True},
                "category": {"type": "string", "required": False}
            }
        },
        
        # ─────────────────────────────────────────────────────────────────────
        # LLM CONFIGURATION (flat format)
        # Settings for AI content generation (provider, model, temperature)
        # Users define their own prompts in report_config.yaml
        # ─────────────────────────────────────────────────────────────────────
        "llm_provider": "openai",
        "llm_model": "gpt-4o",
        "llm_temperature": 0.7,
        "llm_max_tokens": 2000,
        "llm_chunk_size": 10,
        
        # ─────────────────────────────────────────────────────────────────────
        # THEME AND OUTPUT (flat format)
        # Default theme preset (users can override in YAML or via --theme)
        # ─────────────────────────────────────────────────────────────────────
        "theme": color_theme,  # dark, light, ocean, purple, terminal, sunset
        "output_filename": f"{safe_name}_report.html"
        
        # NOTE: Pages are defined by USERS in report_config.yaml, not here.
        # This file defines what's POSSIBLE; YAML defines what to USE.
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
# PLUGIN CONFIG
# ─────────────────────────────────────────────────────────────────────────────────
#
# Plugin-specific settings. These override the plugin's JSON defaults.
# Access in templates via: {{{{ config.your_setting }}}}
#
# ─────────────────────────────────────────────────────────────────────────────────

config:
  # Example plugin-specific settings (customize for your plugin):
  # thresholds:
  #   warning: 50
  #   danger: 30
  # labels:
  #   header: "My Custom Report"
  #   footer: "Generated by BobReview"

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
        id: score_chart
        chart: bar
        title: "Scores by Item"
        x: name
        y: score

      - type: chart
        id: trend_chart
        chart: line
        title: "Score Trend"
        x: name
        y: score

      # ── LLM CONTENT ─────────────────────────────────────────────────────────────
      # AI-generated insights using your configured LLM provider
      #
      # Add as many LLM sections as you want - each with its own prompt!
      #
      # OPTIONS:
      #   id:       Unique identifier (optional, auto-generated if omitted)
      #   title:    Display title for the section
      #   prompt:   Your prompt - be creative! The AI will analyze your data.
      #   max_rows: Max data rows to include (default: 50)
      #
      # DATA FIELD REFERENCES:
      #   Use {{{{field}}}} syntax to reference data fields in your prompt.
      #   This auto-configures which columns are sent to the LLM.
      #   Example: "Compare {{{{name}}}} scores: {{{{score}}}}"

      - type: llm
        id: summary
        title: "Executive Summary"
        prompt: "Analyze the {{{{name}}}} and {{{{score}}}} data. Provide a brief executive summary highlighting key trends and outliers."

      - type: llm
        id: recommendations
        title: "Recommendations"
        prompt: "Based on this {name} data, provide 3-5 actionable recommendations for improvement."

      # ── INLINE WIDGETS ────────────────────────────────────────────────────────────
      # Create custom widgets with inline HTML templates
      #
      # OPTIONS:
      #   id:       Widget identifier
      #   title:    Widget title
      #   template: HTML template with Jinja2 variables
      #   config:   Template variables
      #
      # EXAMPLE:
      #   - type: widget
      #     id: custom_card
      #     template: "<div class='custom-card'><h3>{{{{ title }}}}</h3><p>{{{{ value }}}}</p></div>"
      #     config:
      #       title: "Average"
      #       value: "{{{{ stats.score.mean | round(2) }}}}"

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
        id: distribution_chart
        chart: histogram
        title: "Score Distribution"
        y: score

      # ── CATEGORY BREAKDOWN ──────────────────────────────────────────────────────
      - type: chart
        id: category_chart
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


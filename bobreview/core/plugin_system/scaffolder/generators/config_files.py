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
    
    Uses Property Controls pattern - components have typed props.
    """
    return f'''# ═══════════════════════════════════════════════════════════════════════════════
# {name.upper()} REPORT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
#
# Components use Property Controls - each has typed props validated automatically.
#
# QUICK START:
#   1. Edit sections below to customize your report
#   2. Run: bobreview --plugin {safe_name} --dir ./sample_data
#   3. Open the generated HTML report
#
# ═══════════════════════════════════════════════════════════════════════════════

name: "{name} Report"
plugin: "{safe_name}"
data_source: "./sample_data/*.csv"
output_dir: "./output"
theme: "{color_theme}"

# ─────────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────────

pages:
  # ┌─────────────────────────────────────────────────────────────────────────────┐
  # │ DASHBOARD                                                                    │
  # └─────────────────────────────────────────────────────────────────────────────┘
  - id: dashboard
    title: "Dashboard"
    layout: grid
    nav_order: 1
    components:
      # ── STAT CARDS ────────────────────────────────────────────────────────────
      - type: {safe_name}_stat_card
        label: "Total Items"
        value: "{{{{ data_points | length }}}}"
        variant: info

      - type: {safe_name}_stat_card
        label: "Average Score"
        value: "{{{{ stats.score.mean | round(1) }}}}"
        variant: ok

      - type: {safe_name}_stat_card
        label: "Highest"
        value: "{{{{ stats.score.max }}}}"
        variant: ok

      - type: {safe_name}_stat_card
        label: "Lowest"
        value: "{{{{ stats.score.min }}}}"
        variant: warn

      # ── CHARTS ────────────────────────────────────────────────────────────────
      - type: {safe_name}_chart
        id: scores_bar
        chart: bar
        title: "Scores by Item"
        x: name
        y: score
        animated: true

      - type: {safe_name}_chart
        id: scores_line
        chart: line
        title: "Score Trend"
        x: name
        y: score

      # ── AI SUMMARY ────────────────────────────────────────────────────────────
      - type: {safe_name}_llm
        id: summary
        title: "AI Summary"
        prompt: "Analyze the {{{{name}}}} and {{{{score}}}} data. Provide a brief executive summary."

  # ┌─────────────────────────────────────────────────────────────────────────────┐
  # │ DETAILS                                                                      │
  # └─────────────────────────────────────────────────────────────────────────────┘
  - id: details
    title: "Details"
    layout: single-column
    nav_order: 2
    components:
      - type: {safe_name}_chart
        id: distribution
        chart: histogram
        title: "Score Distribution"
        y: score

      - type: {safe_name}_chart
        id: categories
        chart: doughnut
        title: "By Category"
        x: category
        y: score

      # ── DATA TABLE ────────────────────────────────────────────────────────────
      - type: {safe_name}_data_table
        id: all_data
        title: "All Data"
        columns:
          - name
          - score
          - category
        sortable: true
        paginated: true
        page_size: 10

      # ── RECOMMENDATIONS ───────────────────────────────────────────────────────
      - type: {safe_name}_llm
        id: recommendations
        title: "Recommendations"
        prompt: "Based on this {name} data, provide 3-5 actionable recommendations."

# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT REFERENCE (Property Controls)
# ═══════════════════════════════════════════════════════════════════════════════
#
# {safe_name}_stat_card:
#   label:   Card header text
#   value:   Jinja2 template {{{{ stats.score.mean }}}}
#   variant: default | ok | warn | danger | info
#
# {safe_name}_chart:
#   id:       Unique chart ID (required)
#   chart:    bar | line | pie | doughnut | histogram | scatter
#   title:    Chart title
#   x:        X-axis field
#   y:        Y-axis field
#   animated: true | false
#
# {safe_name}_data_table:
#   id:        Table ID
#   title:     Table title
#   columns:   List of column names
#   sortable:  true | false
#   paginated: true | false
#   page_size: Rows per page
#
# {safe_name}_llm:
#   id:     Unique ID (required)
#   title:  Section title
#   prompt: Your prompt with {{{{field}}}} references
#
# {safe_name}_text:
#   content:  Text or Jinja2 template
#   markdown: true | false
#
# ═══════════════════════════════════════════════════════════════════════════════
'''


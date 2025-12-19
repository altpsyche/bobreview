"""
Configuration file generators for plugin scaffolding.

Generates JSON/configuration structures:
- manifest.json
- report_system.json
- report_config.yaml (user-facing)
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
    """Generate report system JSON for plugin developers."""
    return {
        "schema_version": "1.0",
        "system_id": safe_name,
        "name": f"{name} Adventurer's Guild",
        "data_source": {
            "parser": f"{safe_name}_csv",
            "fields": ["name", "class", "level", "hp", "str", "dex", "con", "int", "wis", "cha", "background", "equipment", "alignment", "story", "featured"]
        },
        "generators": {
            "party_analysis": {"type": "llm", "description": "Party composition analysis"},
            "quest_generator": {"type": "llm", "description": "Generate adventure hooks"},
        },
        "theme": color_theme,
        "output_filename": f"{safe_name}_report.html"
    }


def generate_user_report_config(name: str, safe_name: str, color_theme: str = 'dark') -> str:
    """
    Generate a D&D character sheet style report.
    Features: ability scores, featured characters, story section.
    """
    return f'''# -----------------------------------------------------------------------------
#  {name.upper()} - ADVENTURER'S GUILD
# -----------------------------------------------------------------------------

name: "{name} Adventurer's Guild"
plugin: "{safe_name}"
data_source: "./sample_data/*.csv"
output_dir: "./output"
theme: "{color_theme}"

pages:
  # ---------------------------------------------------------------------------
  # THE TAVERN - Where heroes gather
  # ---------------------------------------------------------------------------
  - id: tavern
    title: "The Tavern"
    icon: "fa-beer-mug-empty"
    layout: single-column
    nav_order: 1
    components:
      # Hero banner - Party status
      - type: {safe_name}_hero_banner
        title: "Welcome to the Guild"
        subtitle: "{{{{ data_points | length }}}} adventurers ready for glory"
        icon: "fa-shield"
        variant: ok

      # Section divider
      - type: {safe_name}_divider
        label: "Featured Heroes"

      # Featured section - showcase 1-4 highlighted characters
      - type: {safe_name}_featured_section
        title: "Heroes of Renown"
        max_featured: 4
        show_stats: true

      # Section divider
      - type: {safe_name}_divider
        label: "Party Statistics"

      # Stats row - 4 cards side by side
      - type: {safe_name}_stat_row
        items:
          - label: "Heroes"
            value: "{{{{ data_points | length }}}}"
            variant: info
            icon: "fa-users"
          - label: "Champion"
            value: "Lvl {{{{ stats.level.max }}}}"
            variant: ok
            icon: "fa-crown"
          - label: "Total HP"
            value: "{{{{ stats.hp.sum }}}}"
            variant: default
            icon: "fa-heart"
          - label: "Avg Level"
            value: "{{{{ stats.level.mean | round(1) }}}}"
            variant: warn
            icon: "fa-chart-line"

      # Guild Master speaks!
      - type: {safe_name}_llm
        id: guild_master
        title: "The Guild Master's Wisdom"
        icon: "fa-scroll"
        prompt: |
          You are Greybeard, a legendary retired adventurer who now runs the guild.
          
          PARTY: {{{{data_points | length}}}} adventurers | Avg Level {{{{stats.level.mean | round(1)}}}}
          
          Give a SHORT assessment in character:
          1. Rate the party (Legendary/Seasoned/Promising/Green)
          2. One strength you notice
          3. One piece of gruff advice
          
          Be gruff but wise. Keep it to 3-4 sentences total!

  # ---------------------------------------------------------------------------
  # THE ARMOURY - Combat stats & ability scores
  # ---------------------------------------------------------------------------
  - id: armoury
    title: "The Armoury"
    icon: "fa-shield-halved"
    layout: single-column
    nav_order: 2
    components:
      # Hero banner - Combat readiness
      - type: {safe_name}_hero_banner
        title: "Combat Readiness"
        subtitle: "Analyzing party strength and ability scores"
        icon: "fa-swords"
        variant: warn

      # Section divider
      - type: {safe_name}_divider
        label: "Party Ability Scores"

      # Ability scores - The Big Six displayed as stat cards
      - type: {safe_name}_ability_scores
        title: "Average Party Stats"
        show_average: true

      # Section divider
      - type: {safe_name}_divider
        label: "Hit Point Analysis"

      # Stats row - 3 HP stats
      - type: {safe_name}_stat_row
        items:
          - label: "Tank HP"
            value: "{{{{ stats.hp.max }}}}"
            variant: ok
            icon: "fa-shield"
          - label: "Lowest HP"
            value: "{{{{ stats.hp.min }}}}"
            variant: danger
            icon: "fa-skull"
          - label: "Average HP"
            value: "{{{{ stats.hp.mean | round(0) }}}}"
            variant: info
            icon: "fa-heart-pulse"

      # HP progress bar
      - type: {safe_name}_progress_bar
        label: "Party HP Range"
        min: "{{{{ stats.hp.min }}}}"
        max: "{{{{ stats.hp.max }}}}"
        current: "{{{{ stats.hp.mean | round(0) }}}}"
        variant: ok

      # Section divider
      - type: {safe_name}_divider
        label: "Combat Analysis"

      # HP chart
      - type: {safe_name}_chart
        id: hp_chart
        chart: bar
        title: "Hit Points Ranking"
        x: name
        y: hp
        animated: true

      # Class distribution chart
      - type: {safe_name}_chart
        id: class_chart
        chart: doughnut
        title: "Class Distribution"
        x: class
        y: level

      # Tactical assessment
      - type: {safe_name}_llm
        id: tactician
        title: "Tactical Assessment"
        icon: "fa-chess"
        prompt: |
          Quick tactical party assessment:
          - {{{{data_points | length}}}} members, HP {{{{stats.hp.min}}}}-{{{{stats.hp.max}}}}
          - Avg STR: {{{{stats.str.mean | round(0)}}}}, DEX: {{{{stats.dex.mean | round(0)}}}}, CON: {{{{stats.con.mean | round(0)}}}}
          
          Rate combat readiness and suggest a challenge rating (CR).
          2-3 sentences max!

  # ---------------------------------------------------------------------------
  # QUEST BOARD
  # ---------------------------------------------------------------------------
  - id: quests
    title: "Quest Board"
    icon: "fa-map"
    layout: single-column
    nav_order: 3
    components:
      # Hero banner
      - type: {safe_name}_hero_banner
        title: "Quest Board"
        subtitle: "Available contracts and bounties for adventurers"
        icon: "fa-scroll"

      # Section divider
      - type: {safe_name}_divider
        label: "Party Composition"

      # Stats row
      - type: {safe_name}_stat_row
        items:
          - label: "Backgrounds"
            value: "{{{{ data_points | map(attribute='background') | unique | list | length }}}}"
            variant: info
            icon: "fa-masks-theater"
          - label: "Classes"
            value: "{{{{ data_points | map(attribute='class') | unique | list | length }}}}"
            variant: ok
            icon: "fa-hat-wizard"

      # Charts in a row
      - type: {safe_name}_chart
        id: background_chart
        chart: pie
        title: "Backgrounds in Party"
        x: background
        y: level

      - type: {safe_name}_chart
        id: align_chart
        chart: doughnut
        title: "Moral Alignment"
        x: alignment
        y: level

      # Section divider
      - type: {safe_name}_divider
        label: "Available Quests"

      # Quest hooks
      - type: {safe_name}_llm
        id: quest_hooks
        title: "Available Quests"
        icon: "fa-scroll"
        prompt: |
          Generate 3 quest hooks for a level {{{{stats.level.mean | round(0)}}}} party:
          
          Format:
          **Quest 1: [NAME]** (Easy)
          [1-2 sentence hook]
          
          **Quest 2: [NAME]** (Medium)
          [1-2 sentence hook]
          
          **Quest 3: [NAME]** (Hard/Funny)
          [1-2 sentence hook]

  # ---------------------------------------------------------------------------
  # STORY FORGE - LLM-enhanced session generator
  # ---------------------------------------------------------------------------
  - id: stories
    title: "Story Forge"
    icon: "fa-book-sparkles"
    layout: single-column
    nav_order: 4
    components:
      # Hero banner
      - type: {safe_name}_hero_banner
        title: "The Story Forge"
        subtitle: "Transform character backstories into epic sessions"
        icon: "fa-wand-magic-sparkles"
        variant: info

      # Section divider
      - type: {safe_name}_divider
        label: "Character Stories"

      # Story section - shows character stories and LLM enhancement
      - type: {safe_name}_story_section
        title: "Tales of the Party"
        show_all: false
        featured_only: true

      # Section divider
      - type: {safe_name}_divider
        label: "Session Generator"

      # LLM story enhancement
      - type: {safe_name}_llm
        id: session_generator
        title: "Tonight's Adventure"
        icon: "fa-dragon"
        prompt: |
          You are a master Dungeon Master. Using the party's backstories, create a ONE-SHOT adventure outline.
          
          FEATURED HEROES:
          {{% for hero in data_points if hero.featured %}}
          - {{{{hero.name}}}} ({{{{hero.class}}}}): {{{{hero.story}}}}
          {{% endfor %}}
          
          Create a compelling 2-3 paragraph adventure hook that:
          1. Ties into at least 2 character backstories
          2. Provides a clear objective
          3. Hints at complications
          4. Includes one moment where a specific character can shine
          
          Make it dramatic and engaging for a tabletop session!

  # ---------------------------------------------------------------------------
  # GUILD REGISTRY - Full roster with all stats
  # ---------------------------------------------------------------------------
  - id: registry
    title: "Guild Registry"
    icon: "fa-book"
    layout: single-column
    nav_order: 5
    components:
      # Hero banner
      - type: {safe_name}_hero_banner
        title: "Guild Registry"
        subtitle: "Official record of registered adventurers"
        icon: "fa-book-open"

      # Section divider
      - type: {safe_name}_divider
        label: "Registry Overview"

      # Stats row
      - type: {safe_name}_stat_row
        items:
          - label: "Registered"
            value: "{{{{ data_points | length }}}}"
            variant: info
            icon: "fa-users"
          - label: "Highest Level"
            value: "Lvl {{{{ stats.level.max }}}}"
            variant: ok
            icon: "fa-crown"
          - label: "Total HP Pool"
            value: "{{{{ stats.hp.sum }}}}"
            variant: default
            icon: "fa-heart"

      # Member spotlight - Champion
      - type: {safe_name}_member_spotlight
        title: "Guild Champion"
        field: level
        mode: max
        icon: "fa-crown"

      # Section divider
      - type: {safe_name}_divider
        label: "Complete Roster"

      # Full roster table with all stats
      - type: {safe_name}_data_table
        id: roster
        title: "Complete Adventurer Roster"
        columns:
          - name
          - class
          - level
          - hp
          - str
          - dex
          - con
          - int
          - wis
          - cha
          - background
          - equipment
        sortable: true
        paginated: false

# -----------------------------------------------------------------------------
# COMPONENT REFERENCE
# -----------------------------------------------------------------------------
#
# {safe_name}_featured_section:
#   title:        Section header
#   max_featured: Max characters to show (1-4)
#   show_stats:   Display ability scores on cards
#
# {safe_name}_ability_scores:
#   title:        Section header
#   show_average: Show party average for each stat
#
# {safe_name}_story_section:
#   title:         Section header
#   show_all:      Show all character stories
#   featured_only: Only show featured character stories
#
# {safe_name}_stat_card:
#   label:   Card header text
#   value:   Jinja2 template {{{{ stats.level.mean }}}}
#   variant: default | ok | warn | danger | info
#
# {safe_name}_chart:
#   chart: bar | line | pie | doughnut | histogram
#   x: X-axis field (name, class, background)
#   y: Y-axis field (level, hp, str, dex, etc.)
#
# {safe_name}_llm:
#   prompt: Multi-line D&D themed prompt
#
# {safe_name}_data_table:
#   columns: List of columns to show
#
# -----------------------------------------------------------------------------
'''

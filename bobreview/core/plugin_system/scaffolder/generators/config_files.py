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

# Adventure Theme - describe what kind of session you want!
# The LLM will weave this theme into quests and story elements.
adventure_theme: "A mysterious curse is spreading through the land, and ancient evils stir in forgotten dungeons."


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

      # Guild Master speaks! - references adventure theme
      - type: {safe_name}_llm
        id: guild_master
        title: "The Guild Master's Wisdom"
        icon: "fa-scroll"
        prompt: |
          You are Greybeard, a legendary retired adventurer who now runs the guild.
          
          PARTY: {{{{data_points | length}}}} adventurers | Avg Level {{{{stats.level.mean | round(1)}}}}
          
          TONIGHT'S ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          
          Give a SHORT assessment in character:
          1. Rate the party for THIS adventure (Ready/Promising/Needs Preparation)
          2. One strength that will help with this theme
          3. One piece of gruff advice specific to the challenge ahead
          
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
        subtitle: "Analyzing party strength for the adventure ahead"
        icon: "fa-swords"
        variant: warn

      # Tactical assessment FIRST - the story-relevant content
      - type: {safe_name}_llm
        id: tactician
        title: "Tactical Assessment"
        icon: "fa-chess"
        prompt: |
          Quick tactical party assessment for the adventure ahead:
          
          ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          
          PARTY STATS:
          - {{{{data_points | length}}}} members, HP {{{{stats.hp.min}}}}-{{{{stats.hp.max}}}}
          - Avg STR: {{{{stats.str.mean | round(0)}}}}, DEX: {{{{stats.dex.mean | round(0)}}}}, CON: {{{{stats.con.mean | round(0)}}}}
          
          Rate combat readiness FOR THIS THEME and suggest appropriate challenge rating (CR).
          2-3 sentences max!

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

      # Section divider - charts are reference, not primary
      - type: {safe_name}_divider
        label: "Reference Charts"

      # Single chart - class distribution (useful for party balance)
      - type: {safe_name}_chart
        id: class_chart
        chart: doughnut
        title: "Class Distribution"
        x: class
        y: level

  # ---------------------------------------------------------------------------
  # QUEST BOARD - The heart of tonight's adventure
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
        subtitle: "Choose your adventure wisely, heroes"
        icon: "fa-scroll"
        variant: info

      # Quest hooks FIRST - this is the main content!
      - type: {safe_name}_llm
        id: quest_hooks
        title: "Available Quests"
        icon: "fa-scroll"
        prompt: |
          Generate 3 quest hooks for a level {{{{stats.level.mean | round(0)}}}} party.
          
          ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          
          PARTY MEMBERS:
          {{% for hero in data_points[:5] %}}
          - {{{{hero.name}}}} ({{{{hero.class}}}}){{{{': ' + hero.story[:80] + '...' if hero.story else ''}}}}
          {{% endfor %}}
          
          Create quests that FIT THE THEME and tie into character backstories!
          
          Format:
          **Quest 1: [NAME]** (Easy)
          [1-2 sentence hook connected to the theme]
          
          **Quest 2: [NAME]** (Medium)
          [1-2 sentence hook with personal stakes related to the theme]
          
          **Quest 3: [NAME]** (Hard/Epic)
          [1-2 sentence hook - the climactic adventure matching the theme]

      # Section divider - supporting info below
      - type: {safe_name}_divider
        label: "Party Composition"

      # Stats row - quick reference
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
          - label: "Alignments"
            value: "{{{{ data_points | map(attribute='alignment') | unique | list | length }}}}"
            variant: warn
            icon: "fa-balance-scale"

      # Single small chart - alignment is relevant for moral dilemmas
      - type: {safe_name}_chart
        id: align_chart
        chart: doughnut
        title: "Moral Alignment"
        x: alignment
        y: level

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

      # LLM story enhancement - references quest_hooks output and theme
      - type: {safe_name}_llm
        id: session_generator
        title: "Tonight's Adventure"
        icon: "fa-dragon"
        depends_on: [quest_hooks]  # Ensures quests are generated first
        prompt: |
          You are a master Dungeon Master. Create a ONE-SHOT adventure outline.
          
          ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          
          FEATURED HEROES:
          {{% for hero in data_points if hero.featured %}}
          - {{{{hero.name}}}} ({{{{hero.class}}}}): {{{{hero.story}}}}
          {{% endfor %}}
          
          AVAILABLE QUESTS FROM THE GUILD BOARD:
          {{{{ llm_outputs.quest_hooks }}}}
          
          Create a compelling 2-3 paragraph adventure that:
          1. Directly connects to the ADVENTURE THEME above
          2. Uses one of the quest hooks as a starting point
          3. Weaves in at least 2 character backstories
          4. Includes a dramatic complication
          5. Features a moment where a specific character can shine
          
          Make it feel like a cohesive story that fits the theme!

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

  # ---------------------------------------------------------------------------
  # NPCs - Generated characters for the adventure
  # ---------------------------------------------------------------------------
  - id: npcs
    title: "NPCs"
    icon: "fa-users-between-lines"
    layout: single-column
    nav_order: 6
    components:
      # Hero banner
      - type: {safe_name}_hero_banner
        title: "Cast of Characters"
        subtitle: "NPCs generated for tonight's adventure"
        icon: "fa-masks-theater"
        variant: info

      # NPC Generator LLM
      - type: {safe_name}_llm
        id: npc_generator
        title: "Key NPCs"
        icon: "fa-user-secret"
        prompt: |
          Generate 4 NPCs for tonight's adventure.
          
          ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          
          PARTY LEVEL: {{{{stats.level.mean | round(0)}}}}
          
          Create NPCs that fit the theme. For each NPC:
          **[NAME]** - [ROLE] ([Friendly/Neutral/Hostile])
          *Appearance:* [1 sentence]
          *Personality:* [1-2 traits]
          *Secret:* [What they're hiding]
          *Hook:* [How they connect to the adventure]
          
          Include: 1 quest giver, 1 potential ally, 1 suspicious character, 1 villain or obstacle.

      # Section divider
      - type: {safe_name}_divider
        label: "Tavern Rumors"

      # Tavern Rumors LLM
      - type: {safe_name}_llm
        id: tavern_rumors
        title: "Whispers in the Tavern"
        icon: "fa-comments"
        prompt: |
          Generate 5 tavern rumors that players might hear.
          
          ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          
          Create rumors that build atmosphere and provide hooks:
          - 2 rumors that are TRUE and directly relate to the adventure
          - 2 rumors that are FALSE or misleading red herrings
          - 1 rumor that's PARTIALLY TRUE with a twist
          
          Format each as:
          **"[Rumor text]"** - [TRUE/FALSE/PARTIAL]
          *Source:* [Who's spreading this]

  # ---------------------------------------------------------------------------
  # ENCOUNTERS - Combat and challenges
  # ---------------------------------------------------------------------------
  - id: encounters
    title: "Encounters"
    icon: "fa-skull-crossbones"
    layout: single-column
    nav_order: 7
    components:
      # Hero banner
      - type: {safe_name}_hero_banner
        title: "Encounters"
        subtitle: "Combat and challenges for the session"
        icon: "fa-dragon"
        variant: danger

      # Encounter Builder LLM
      - type: {safe_name}_llm
        id: encounter_builder
        title: "Prepared Encounters"
        icon: "fa-swords"
        depends_on: [tactician, quest_hooks]
        prompt: |
          Generate 3 combat encounters for tonight's session.
          
          ADVENTURE THEME: {{{{ config.adventure_theme }}}}
          PARTY: {{{{data_points | length}}}} characters, Avg Level {{{{stats.level.mean | round(0)}}}}
          
          TACTICAL ASSESSMENT:
          {{{{ llm_outputs.tactician }}}}
          
          AVAILABLE QUESTS:
          {{{{ llm_outputs.quest_hooks }}}}
          
          Create encounters that fit the quests:
          
          **Encounter 1: [Name]** (Easy, CR {{{{stats.level.mean | round(0) - 2}}}})
          - Enemies: [What they face]
          - Terrain: [Environment]
          - Objective: [Beyond just combat]
          
          **Encounter 2: [Name]** (Medium, CR {{{{stats.level.mean | round(0)}}}})
          - Enemies: [What they face]
          - Terrain: [Environmental hazards]
          - Twist: [Complication mid-fight]
          
          **Encounter 3: [Name]** (Hard/Boss, CR {{{{stats.level.mean | round(0) + 2}}}})
          - Enemies: [Boss + minions]
          - Lair Actions: [Special effects]
          - Victory Condition: [How to win]

      # Section divider
      - type: {safe_name}_divider
        label: "Treasure & Rewards"

      # Loot Generator LLM
      - type: {safe_name}_llm
        id: loot_generator
        title: "Treasure Hoard"
        icon: "fa-gem"
        depends_on: [encounter_builder]
        prompt: |
          Generate loot appropriate for the encounters.
          
          PARTY LEVEL: {{{{stats.level.mean | round(0)}}}}
          
          ENCOUNTERS TO REWARD:
          {{{{ llm_outputs.encounter_builder }}}}
          
          Create treasure that feels earned:
          
          **Easy Encounter Loot:**
          - Gold: [Amount]gp
          - Items: [1-2 useful items]
          
          **Medium Encounter Loot:**
          - Gold: [Amount]gp
          - Magic Item: [Uncommon item fitting the theme]
          
          **Boss Encounter Loot:**
          - Gold: [Amount]gp
          - Magic Item: [Rare item, named with backstory]
          - Story Item: [Plot-relevant object]

  # ---------------------------------------------------------------------------
  # SESSION PREP - DM Reference Materials
  # ---------------------------------------------------------------------------
  - id: session_prep
    title: "Session Prep"
    icon: "fa-list-check"
    layout: single-column
    nav_order: 8
    components:
      # Hero banner
      - type: {safe_name}_hero_banner
        title: "Session Prep"
        subtitle: "Quick reference materials for the DM"
        icon: "fa-clipboard-list"

      # Section divider
      - type: {safe_name}_divider
        label: "Initiative Tracker"

      # Initiative tracker
      - type: {safe_name}_initiative_tracker
        title: "Combat Initiative"

      # Section divider
      - type: {safe_name}_divider
        label: "Character Quick Reference"

      # Quick reference cards
      - type: {safe_name}_quick_cards
        title: "Party Reference Cards"
        featured_only: false

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
#   id:         Unique ID - used to reference output in other prompts
#   prompt:     Multi-line prompt template with Jinja2 support
#   depends_on: [id1, id2] - ensures these LLM components run first
#   
#   Use {{ llm_outputs.other_id }} in prompts to reference other LLM outputs.
#   Example:
#     - type: {safe_name}_llm
#       id: quests
#       prompt: "Generate quests..."
#     
#     - type: {safe_name}_llm
#       id: adventure
#       depends_on: [quests]
#       prompt: |
#         Based on these quests:
#         {{ llm_outputs.quests }}
#         Create an adventure...
#
# {safe_name}_data_table:
#   columns: List of columns to show
#
# {safe_name}_initiative_tracker:
#   title: Section header for initiative display
#   (Automatically sorts party by DEX for turn order)
#
# {safe_name}_quick_cards:
#   title:         Section header
#   featured_only: Only show featured characters (default: false)
#   (Shows character reference cards with stats, spells, equipment)
#
# {safe_name}_quote_box:
#   quote:   The quote text
#   speaker: Who said it
#   title:   Optional title above quote
#   icon:    FontAwesome icon (default: fa-comment-dots)
#   variant: default | villain (red styling)
#
# {safe_name}_encounter_card:
#   name:        Enemy name
#   cr:          Challenge Rating
#   ac:          Armor Class
#   hp:          Hit Points
#   description: Enemy description
#   abilities:   Special abilities
#   tactics:     Combat tactics
#   icon:        FontAwesome icon (default: fa-skull)
#
# -----------------------------------------------------------------------------
'''


"""
Plugin scaffolder core - main orchestration for creating plugin skeletons.

Generates a complete plugin directory structure with:
- manifest.json
- plugin.py (main plugin class)
- parsers/ (data parser examples)
- context_builder.py
- chart_generator.py
- report_systems/ (JSON report definition)
- templates/ (Jinja2 templates)
- sample_data/ (example data files)
"""

import json
from pathlib import Path
from typing import Literal

# Themes are now plugin-owned - no core imports needed

# Import generators
from .generators import (
    generate_plugin_py,
    generate_csv_parser,
    generate_context_builder,
    generate_executor,
    generate_chart_generator,
    generate_analysis_module,
    generate_theme_module,
    generate_widgets_module,
    generate_component_module,
    generate_manifest,
    generate_report_system,
    generate_user_report_config,
)


# Path to scaffolder templates
TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_plugin(
    name: str,
    output_dir: Path,
    template: Literal['minimal', 'full'] = 'full',
    color_theme: str = 'dark'
) -> Path:
    """
    Create a new plugin directory with all necessary files.
    
    Parameters:
        name: Plugin name (e.g., "my-plugin")
        output_dir: Directory to create the plugin in
        template: 'minimal' for basic plugin, 'full' for all features
        color_theme: Color scheme: 'dark', 'ocean', 'purple', 'terminal', 'sunset'
    
    Returns:
        Path to the created plugin directory
    """
    # color_theme is just a hint for generated theme styling
    # No validation needed - plugins create their own themes

    # Ensure output_dir is a Path
    output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
    
    # Normalize name for directory and Python usage
    safe_name = name.replace('-', '_').replace(' ', '_')
    plugin_dir = output_dir / safe_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    class_name = ''.join(word.capitalize() for word in name.replace('_', '-').split('-'))
    
    # Create manifest.json
    manifest = generate_manifest(name, safe_name, class_name, template)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=4), encoding='utf-8'
    )
    
    # Create __init__.py
    init_content = f'''"""
{name} Plugin for BobReview.

Provides a report system for analyzing {name} data.
"""

from .plugin import {class_name}Plugin
from .executor import generate_report

__all__ = ['{class_name}Plugin', 'generate_report']
'''
    (plugin_dir / "__init__.py").write_text(init_content, encoding='utf-8')
    
    # Create plugin.py
    plugin_content = generate_plugin_py(name, safe_name, class_name, template)
    (plugin_dir / "plugin.py").write_text(plugin_content, encoding='utf-8')
    
    # Create parsers directory
    parsers_dir = plugin_dir / "parsers"
    parsers_dir.mkdir(exist_ok=True)
    
    parser_init = f'''"""Data parsers for {name} plugin."""

from .csv_parser import {class_name}CsvParser

__all__ = ['{class_name}CsvParser']
'''
    (parsers_dir / "__init__.py").write_text(parser_init, encoding='utf-8')
    
    parser_content = generate_csv_parser(name, class_name)
    (parsers_dir / "csv_parser.py").write_text(parser_content, encoding='utf-8')
    
    # Create data_schema.yaml for user-defined data structure
    data_schema = _read_template("data_schema.yaml", name=name, safe_name=safe_name)
    (plugin_dir / "data_schema.yaml").write_text(data_schema, encoding='utf-8')
    
    # Create component_templates.yaml for YAML-based component templates
    comp_templates = _read_template("component_templates.yaml", name=name, safe_name=safe_name)
    (plugin_dir / "component_templates.yaml").write_text(comp_templates, encoding='utf-8')
    
    if template == 'full':
        # Create context_builder.py
        context_content = generate_context_builder(name, class_name)
        (plugin_dir / "context_builder.py").write_text(context_content, encoding='utf-8')
        
        # Create chart_generator.py
        chart_content = generate_chart_generator(name, class_name)
        (plugin_dir / "chart_generator.py").write_text(chart_content, encoding='utf-8')
        
        # Create executor.py (for CLI integration)
        executor_content = generate_executor(name, safe_name, class_name)
        (plugin_dir / "executor.py").write_text(executor_content, encoding='utf-8')
        
        # Create widgets.py (custom UI components)
        widgets_content = generate_widgets_module(name, safe_name, class_name)
        (plugin_dir / "widgets.py").write_text(widgets_content, encoding='utf-8')
        
        # Create components.py (Property Controls pattern)
        components_content = generate_component_module(name, safe_name, class_name)
        (plugin_dir / "components.py").write_text(components_content, encoding='utf-8')
    
    # Create report_systems directory
    rs_dir = plugin_dir / "report_systems"
    rs_dir.mkdir(exist_ok=True)
    
    report_system = generate_report_system(name, safe_name, color_theme)
    (rs_dir / f"{safe_name}.json").write_text(
        json.dumps(report_system, indent=4), encoding='utf-8'
    )
    
    # Create static CSS directory for plugin styles
    static_dir = plugin_dir / "templates" / safe_name / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # NOTE: Reports are built entirely from YAML config (report_config.yaml
    # + component_templates.yaml). Theme CSS is generated dynamically at runtime.
    
    
    # Generate plugin CSS (layout and components)
    plugin_css = _read_template("static/plugin.css", name=name, safe_name=safe_name)
    (static_dir / "plugin.css").write_text(plugin_css, encoding='utf-8')
    
    # Create analysis module (for full template)
    if template == 'full':
        analysis_content = generate_analysis_module(name, safe_name)
        (plugin_dir / "analysis.py").write_text(analysis_content, encoding='utf-8')
        
        # Create custom theme module
        theme_content = generate_theme_module(name, safe_name, class_name)
        (plugin_dir / "theme.py").write_text(theme_content, encoding='utf-8')
    
    # Create sample_data directory with epic D&D character data!
    sample_dir = plugin_dir / "sample_data"
    sample_dir.mkdir(exist_ok=True)
    
    # ⚔️ D&D Character Roster - Adventurer's Guild Records ⚔️
    # Extended stats: name, class, level, hp, str, dex, con, int, wis, cha, background, equipment, alignment, story, featured
    sample_csv = """name,class,level,hp,str,dex,con,int,wis,cha,background,equipment,alignment,story,featured
Thorin Ironforge,Fighter,12,98,18,12,16,10,13,14,Soldier,Warhammer +2 & Shield of Faith,Lawful Good,A veteran of the Goblin Wars seeking to reclaim his clan's lost fortress.,true
Lyralei Moonwhisper,Ranger,10,72,14,18,14,12,16,10,Outlander,Longbow of Seeking & Cloak of Elvenkind,Neutral Good,Last survivor of a village destroyed by undead. Hunts the necromancer responsible.,true
Grimtooth the Wise,Barbarian,14,145,20,14,18,8,12,10,Tribal Nomad,Greataxe of Fury & Belt of Giant Strength,Chaotic Neutral,Despite his name he solves most problems by hitting them. Hard.,false
Elara Brightshield,Paladin,11,95,16,10,14,12,14,16,Noble,Holy Avenger & Plate of the Dawn,Lawful Good,Sworn to protect the innocent after witnessing a demon incursion as a child.,true
Zephyr Shadowstep,Rogue,9,52,10,20,12,16,14,14,Criminal,Daggers of Venom & Boots of Elvenkind,Chaotic Good,Reformed thief who now steals only from the corrupt and evil.,false
Morrigan Darkhollow,Warlock,8,61,10,14,14,16,12,18,Sage,Staff of the Pact & Tome of Shadows,Neutral Evil,Made a pact with an elder entity. The price is yet to be revealed.,false
Aldric Stormcaller,Wizard,13,48,8,14,12,20,16,10,Scholar,Staff of Power & Robes of the Archmagi,True Neutral,Obsessed with understanding the nature of wild magic surges.,false
Kira Flameheart,Sorcerer,10,68,12,14,14,12,10,18,Folk Hero,Ring of Fire Resistance & Wand of Fireballs,Chaotic Good,Her draconic bloodline awakened during a village fire she miraculously survived.,false
Brother Marcus,Cleric,11,78,14,10,16,12,18,14,Acolyte,Mace of Disruption & Shield of Faith,Lawful Good,Healer and counselor who joined adventuring to spread his deity's light.,false
Fennwick Tinkertop,Artificer,7,45,10,16,12,18,14,12,Guild Artisan,Mechanical Companion & Bag of Holding,Neutral Good,Builds wonderful contraptions. They explode only 40% of the time now.,false
Ravenna Nightshade,Bard,9,55,10,16,12,14,12,18,Entertainer,Lute of Charming & Rapier of Dancing,Chaotic Neutral,Collects stories of legendary heroes. Plans to become one herself.,false
Grok Skullcrusher,Barbarian,15,162,20,12,20,6,10,8,Outlander,Vorpal Greataxe & Cloak of Protection,Chaotic Neutral,The party's problem solver. Every problem looks like a skull to crush.,false
Seraphina Dawnweaver,Cleric,12,82,12,10,14,14,18,16,Acolyte,Staff of Healing & Armor of Light,Lawful Good,Chosen by her goddess at birth. Marked with radiant sigils.,false
Vex the Silent,Monk,10,64,12,18,14,12,16,10,Hermit,Bracers of Defense & Staff of Striking,True Neutral,Took a vow of silence. Communicates through gestures and written notes.,false
Bramblewood,Druid,11,88,14,12,16,13,18,10,Outlander,Staff of the Woodlands & Ring of Animal Friendship,Neutral Good,A firbolg who tends to a sacred grove threatened by expanding civilization.,false
Captain Flint,Fighter,8,76,16,14,16,12,10,14,Sailor,Cutlass +1 & Pistol of Warning,Neutral Evil,Former pirate captain seeking a legendary treasure map.,false
Whisper,Rogue,6,38,10,18,10,14,14,12,Urchin,Cloak of Shadows & Dagger of Returning,Chaotic Good,A young kenku raised by thieves learning the difference between survival and greed.,false
Azura Frostborn,Sorcerer,9,54,10,14,12,14,12,18,Noble,Staff of Frost & Ring of Warmth,Chaotic Neutral,Her ice magic manifested on her wedding day. The groom is still frozen.,false
"""
    (sample_dir / "sample.csv").write_text(sample_csv, encoding='utf-8')
    
    # Create user-facing report_config.yaml
    # This is the CMS-style config that end users edit to compose reports
    user_config = generate_user_report_config(name, safe_name, color_theme)
    (plugin_dir / "report_config.yaml").write_text(user_config, encoding='utf-8')
    
    return plugin_dir


def _read_template(relative_path: str, **kwargs) -> str:
    """
    Read a template file and interpolate placeholders.
    
    Placeholders use {{key}} format (double braces to avoid
    conflicts with Jinja2 which uses single braces).
    
    Parameters:
        relative_path: Path relative to scaffolder/templates/
        **kwargs: Key-value pairs for placeholder substitution
    
    Returns:
        Template content with placeholders replaced
    """
    template_path = TEMPLATES_DIR / relative_path
    content = template_path.read_text(encoding='utf-8')
    
    # Replace {{key}} placeholders
    for key, value in kwargs.items():
        content = content.replace("{{" + key + "}}", value)
    
    return content

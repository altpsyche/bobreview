"""
Generator for executor.py file.

Creates the YAML-driven report generation executor with:
- Page rendering from report_config.yaml
- Chart generation with theme support
- LLM content generation
- Tab-based navigation
"""


def generate_executor(name: str, safe_name: str, class_name: str) -> str:
    """Generate executor.py with YAML-driven report generation."""
    return '''"""
Report Executor for ''' + name + ''' Plugin.

YAML-Driven Report Generation:
- Reads pages from report_config.yaml
- Generates charts, stats, tables, and LLM content dynamically
- Single HTML file with tabbed pages

Usage:
    bobreview --plugin ''' + name + ''' --dir ./data --output ./output
    bobreview --plugin ''' + name + ''' --dir ./data --dry-run  # Skip LLM calls
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .theme import ''' + safe_name.upper() + '''_DUNGEON, ''' + safe_name.upper() + '''_MIDNIGHT, ''' + safe_name.upper() + '''_AURORA, ''' + safe_name.upper() + '''_SUNSET, ''' + safe_name.upper() + '''_FROST, get_theme_css_variables, ReportTheme
from .parsers.csv_parser import ''' + class_name + '''CsvParser
from .chart_generator import ''' + class_name + '''ChartGenerator


# Theme mapping
THEMES = {
    "''' + safe_name + '''_dungeon": ''' + safe_name.upper() + '''_DUNGEON,
    "''' + safe_name + '''_midnight": ''' + safe_name.upper() + '''_MIDNIGHT,
    "''' + safe_name + '''_aurora": ''' + safe_name.upper() + '''_AURORA,
    "''' + safe_name + '''_sunset": ''' + safe_name.upper() + '''_SUNSET,
    "''' + safe_name + '''_frost": ''' + safe_name.upper() + '''_FROST,
    "dungeon": ''' + safe_name.upper() + '''_DUNGEON,
    "midnight": ''' + safe_name.upper() + '''_MIDNIGHT,
    "aurora": ''' + safe_name.upper() + '''_AURORA,
    "sunset": ''' + safe_name.upper() + '''_SUNSET,
    "frost": ''' + safe_name.upper() + '''_FROST,
}


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load report_config.yaml."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def calculate_stats(data_points: List[Dict]) -> Dict[str, Any]:
    """Calculate stats for all numeric fields."""
    if not data_points:
        return {}
    
    stats = {}
    # Find all numeric fields
    for key in data_points[0].keys():
        values = [d.get(key) for d in data_points if isinstance(d.get(key), (int, float))]
        if values:
            stats[key] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values),
                'sum': sum(values),
            }
    return stats


def _topological_sort_llm(components: list) -> list:
    """
    Sort LLM components by depends_on for correct execution order.
    
    Components with no dependencies run first, then components that
    depend on them, etc. This ensures llm_outputs[dep_id] is available
    when a component references it.
    
    Raises ValueError if circular dependencies are detected.
    """
    by_id = {c.get('id', f'anon_{i}'): c for i, c in enumerate(components)}
    visited = set()      # Fully processed nodes
    in_progress = set()  # Currently being visited (for cycle detection)
    result = []
    
    def visit(comp_id, path=None):
        if path is None:
            path = []
        if comp_id in visited:
            return
        if comp_id in in_progress:
            cycle = ' -> '.join(path + [comp_id])
            raise ValueError(f"Circular dependency detected: {cycle}")
        
        in_progress.add(comp_id)
        comp = by_id.get(comp_id)
        if comp:
            # Visit dependencies first
            for dep in comp.get('depends_on', []):
                if dep in by_id:
                    visit(dep, path + [comp_id])
            result.append(comp)
        in_progress.remove(comp_id)
        visited.add(comp_id)
    
    for comp_id in by_id:
        visit(comp_id)
    
    return result


def generate_llm_content(
    config: Dict[str, Any],
    data_points: List[Dict],
    stats: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, str]:
    """
    Generate LLM content for all prompts in YAML config.
    
    Supports LLM chaining via:
    - depends_on: [id1, id2] - ensures specified components run first
    - llm_outputs.id - reference previous LLM output in prompt templates
    
    Example YAML:
        - type: plugin_llm
          id: quest_hooks
          prompt: "Generate quests..."
        
        - type: plugin_llm
          id: session_generator
          depends_on: [quest_hooks]
          prompt: |
            Create adventure based on:
            {{ llm_outputs.quest_hooks }}
    """
    from jinja2 import Environment
    from markupsafe import Markup
    import html as html_module
    
    # Create Jinja2 environment for rendering prompts with autoescape
    env = Environment(autoescape=True)
    env.globals['len'] = len
    env.globals['min'] = min
    env.globals['max'] = max
    env.globals['sum'] = sum
    env.globals['round'] = round
    
    # Collect all LLM components from all pages
    llm_components = []
    for page in config.get('pages', []):
        for comp in page.get('components', []):
            comp_type = comp.get('type', '')
            if '_llm' in comp_type:
                llm_components.append(comp)
    
    # Sort by dependencies (topological order)
    ordered = _topological_sort_llm(llm_components)
    
    llm_content = {}      # HTML-sanitized for display
    llm_outputs = {}      # Raw text for chaining to other prompts
    
    for comp in ordered:
        comp_id = comp.get('id', 'unknown')
        prompt_template = comp.get('prompt', '')
        
        # Render prompt with Jinja2 - includes llm_outputs for chaining
        try:
            tpl = env.from_string(prompt_template)
            rendered_prompt = tpl.render(
                data_points=data_points,
                stats=stats,
                llm_outputs=llm_outputs,  # Previous LLM outputs available here
                config=config,  # Full config including adventure_theme
            )
        except Exception as e:
            rendered_prompt = f"[Template Error: {e}]\\n{prompt_template}"
        
        if dry_run:
            # Show rendered prompt preview in dry-run mode (escaped for safety)
            preview = html_module.escape(rendered_prompt[:300].replace('\\n', ' '))
            deps = comp.get('depends_on', [])
            deps_info = f' (depends on: {", ".join(deps)})' if deps else ''
            title_escaped = html_module.escape(comp.get("title", comp_id))
            # Mark as safe since we constructed this HTML ourselves
            llm_content[comp_id] = Markup(f'<div class="llm-dry-run"><em>[LLM Placeholder: {title_escaped}]{deps_info}</em><br><small>Prompt: {preview}...</small></div>')
            llm_outputs[comp_id] = f'[Placeholder output for {comp_id}]'
        else:
            try:
                from bobreview.services.llm.client import call_llm
                from bobreview.core.config import Config
                from bobreview.core.cache import init_cache
                from bobreview.core.html_utils import sanitize_llm_html
                llm_config = Config()
                init_cache(llm_config)
                response = call_llm(rendered_prompt, config=llm_config)
                # Store raw response for chaining
                if response:
                    llm_outputs[comp_id] = response
                    # Mark sanitized HTML as safe to prevent double-escaping
                    llm_content[comp_id] = Markup(sanitize_llm_html(response))
                else:
                    llm_outputs[comp_id] = ''
                    llm_content[comp_id] = Markup(f'<em>No response for {comp_id}</em>')
            except Exception as e:
                llm_outputs[comp_id] = f'[Error: {e}]'
                error_escaped = html_module.escape(str(e))
                llm_content[comp_id] = Markup(f'<div class="llm-error">LLM Error: {error_escaped}</div>')
    
    return llm_content




class TemplateLoader:
    """Load component templates from YAML file."""
    
    def __init__(self, plugin_dir: Path):
        self.templates_path = plugin_dir / 'component_templates.yaml'
        self._cache: Dict[str, Any] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from YAML file."""
        if not self.templates_path.exists():
            return
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                for comp_type, comp_def in data.items():
                    if isinstance(comp_def, dict) and 'template' in comp_def:
                        self._cache[comp_type] = comp_def
        except Exception as e:
            print(f"Warning: Failed to load component templates: {e}")
    
    def get(self, comp_type: str) -> Dict:
        """Get template definition for a component type."""
        return self._cache.get(comp_type, {})
    
    def has(self, comp_type: str) -> bool:
        """Check if template exists."""
        return comp_type in self._cache


class ComponentRenderer:
    """Render components using YAML templates."""
    
    def __init__(self, data_points: List[Dict], stats: Dict, llm_content: Dict,
                 charts_js: List[str], chart_gen: "''' + class_name + '''ChartGenerator",
                 theme: ReportTheme, safe_name: str, template_loader: TemplateLoader,
                 custom_components: Dict[str, Any] = None):
        self.data_points = data_points
        self.stats = stats
        self.llm_content = llm_content
        self.charts_js = charts_js
        self.chart_gen = chart_gen
        self.theme = theme
        self.safe_name = safe_name
        self.templates = template_loader
        self.custom_components = custom_components or {}
        self.count = len(data_points)
        
        # Jinja2 environment with autoescape for HTML safety
        from jinja2 import Environment
        self.env = Environment(autoescape=True)
        self.env.globals['len'] = len
        self.env.globals['min'] = min
        self.env.globals['max'] = max
        self.env.globals['sum'] = sum
        self.env.globals['round'] = round
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Base context for all templates."""
        return {
            'data_points': self.data_points,
            'stats': self.stats,
            'theme': self.theme,
            'count': self.count,
        }
    
    def _render_template(self, template_str: str, context: Dict) -> str:
        """Render a Jinja2 template."""
        try:
            tpl = self.env.from_string(template_str)
            return tpl.render(**context)
        except Exception as e:
            return f'<div class="error">Template error: {e}</div>'
    
    def render(self, comp: Dict) -> str:
        """Render a component to HTML."""
        comp_type = comp.get('type', '')
        
        # Check inline custom components first
        if comp_type in self.custom_components:
            return self._render_custom(comp_type, comp)
        
        # Check charts first (needs JS generation) - BEFORE YAML templates
        if '_chart' in comp_type:
            return self._render_chart(comp)
        
        # Handle new layout/creative components
        if '_stat_row' in comp_type:
            return self._render_stat_row(comp)
        if '_hero_banner' in comp_type:
            return self._render_hero_banner(comp)
        if '_divider' in comp_type:
            return self._render_divider(comp)
        if '_progress_bar' in comp_type:
            return self._render_progress_bar(comp)
        if '_member_spotlight' in comp_type:
            return self._render_member_spotlight(comp)
        if '_featured_section' in comp_type:
            return self._render_featured_section(comp)
        if '_ability_scores' in comp_type:
            return self._render_ability_scores(comp)
        if '_story_section' in comp_type:
            return self._render_story_section(comp)
        if '_initiative_tracker' in comp_type:
            return self._render_initiative_tracker(comp)
        if '_quick_cards' in comp_type:
            return self._render_quick_cards(comp)
        if '_quote_box' in comp_type:
            return self._render_quote_box(comp)
        if '_encounter_card' in comp_type:
            return self._render_encounter_card(comp)
        
        # Check YAML templates
        if self.templates.has(comp_type):
            return self._render_yaml(comp_type, comp)
        
        return f'<!-- Unknown: {comp_type} -->'

    
    def _render_stat_row(self, comp: Dict) -> str:
        """Render a row of stat cards side-by-side."""
        import html as html_module
        items = comp.get('items', [])
        cards_html = ''
        for item in items:
            value = eval_template(item.get('value', '0'), self.data_points, self.stats)
            label = html_module.escape(str(item.get('label', '')))
            variant = item.get('variant', 'default')
            icon = html_module.escape(str(item.get('icon', '')))
            icon_html = f'<i class="fa-solid {icon}"></i> ' if icon else ''
            cards_html += (
                f'<div class="stat-card stat-{variant}">'
                f'<div class="stat-value">{icon_html}{value}</div>'
                f'<div class="stat-label">{label}</div>'
                f'</div>'
            )
        return f'<div class="stats-row">{cards_html}</div>'
    
    def _render_hero_banner(self, comp: Dict) -> str:
        """Render a hero banner with title and subtitle."""
        import html as html_module
        title = comp.get('title', '')
        subtitle = comp.get('subtitle', '')
        if '{{' in title:
            title = eval_template(title, self.data_points, self.stats)
        else:
            title = html_module.escape(str(title))
        if '{{' in subtitle:
            subtitle = eval_template(subtitle, self.data_points, self.stats)
        else:
            subtitle = html_module.escape(str(subtitle))
        icon = html_module.escape(str(comp.get('icon', 'fa-flag')))
        variant = comp.get('variant', 'default')
        return (
            f'<div class="hero-banner hero-{variant}">'
            f'<i class="fa-solid {icon} hero-icon"></i>'
            f'<div class="hero-content">'
            f'<h2 class="hero-title">{title}</h2>'
            f'<p class="hero-subtitle">{subtitle}</p>'
            f'</div></div>'
        )
    
    def _render_divider(self, comp: Dict) -> str:
        """Render a section divider with optional label."""
        import html as html_module
        label = html_module.escape(str(comp.get('label', '')))
        if label:
            return f'<div class="section-divider"><span>{label}</span></div>'
        return '<div class="section-divider"></div>'
    
    def _render_progress_bar(self, comp: Dict) -> str:
        """Render a progress bar visualization."""
        import html as html_module
        label = html_module.escape(str(comp.get('label', 'Progress')))
        min_val = eval_template(comp.get('min', '0'), self.data_points, self.stats)
        max_val = eval_template(comp.get('max', '100'), self.data_points, self.stats)
        current = eval_template(comp.get('current', '50'), self.data_points, self.stats)
        
        try:
            min_n, max_n, curr_n = float(min_val), float(max_val), float(current)
            pct = ((curr_n - min_n) / (max_n - min_n)) * 100 if max_n > min_n else 50
        except:
            pct = 50
        
        variant = comp.get('variant', 'default')
        return (
            f'<div class="progress-card">'
            f'<div class="progress-header">'
            f'<span class="progress-label">{label}</span>'
            f'<span class="progress-values">{min_val} - {max_val}</span>'
            f'</div>'
            f'<div class="progress-bar-container">'
            f'<div class="progress-bar progress-{variant}" style="width: {pct}%"></div>'
            f'<div class="progress-marker" style="left: {pct}%">'
            f'<span class="progress-current">{current}</span>'
            f'</div></div></div>'
        )
    
    def _render_member_spotlight(self, comp: Dict) -> str:
        """Render a featured member spotlight card."""
        import html as html_module
        title = comp.get('title', 'Champion')
        field = comp.get('field', 'level')
        mode = comp.get('mode', 'max')  # max or min
        
        if not self.data_points:
            return '<div class="spotlight-card">No members</div>'
        
        # Find member by max/min
        if mode == 'max':
            member = max(self.data_points, key=lambda x: x.get(field, 0))
        else:
            member = min(self.data_points, key=lambda x: x.get(field, 0))
        
        # Escape all user-sourced content
        name = html_module.escape(str(member.get('name', 'Unknown')))
        background = html_module.escape(str(member.get('background', '')))
        char_class = html_module.escape(str(member.get('class', '')))
        level = member.get('level', 1)
        hp = member.get('hp', 0)
        icon = comp.get('icon', 'fa-crown')
        
        # Build ability score mini-display
        abilities = []
        for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
            val = member.get(stat, 10)
            abilities.append(f'{stat.upper()}: {val}')
        ability_str = ' | '.join(abilities)
        
        return (
            f'<div class="spotlight-card">'
            f'<div class="spotlight-icon"><i class="fa-solid {icon}"></i></div>'
            f'<div class="spotlight-title">{html_module.escape(title)}</div>'
            f'<div class="spotlight-name">{name}</div>'
            f'<div class="spotlight-meta">{char_class} • {background}</div>'
            f'<div class="spotlight-stats">'
            f'<span class="spotlight-stat"><i class="fa-solid fa-star"></i> Lvl {level}</span>'
            f'<span class="spotlight-stat"><i class="fa-solid fa-heart"></i> {hp} HP</span>'
            f'</div>'
            f'<div class="spotlight-abilities">{ability_str}</div>'
            f'</div>'
        )
    
    def _render_featured_section(self, comp: Dict) -> str:
        """Render a featured characters section with 1-4 highlighted heroes."""
        import html as html_module
        title = comp.get('title', 'Featured Heroes')
        max_featured = comp.get('max_featured', 4)
        show_stats = comp.get('show_stats', True)
        
        # Filter featured characters
        featured = [d for d in self.data_points if d.get('featured') in (True, 'true', 'True', 1, '1', 'yes', 'Yes')]
        
        if not featured:
            return '<div class="featured-section"><p class="no-featured">No featured heroes yet. Mark characters with featured=true in your CSV.</p></div>'
        
        # Limit to max_featured
        featured = featured[:max_featured]
        
        cards_html = ''
        for hero in featured:
            # Escape all user-sourced content
            name = html_module.escape(str(hero.get('name', 'Unknown')))
            char_class = html_module.escape(str(hero.get('class', 'Adventurer')))
            level = hero.get('level', 1)
            hp = hero.get('hp', 0)
            background = html_module.escape(str(hero.get('background', '')))
            equipment = html_module.escape(str(hero.get('equipment', '')))
            story = html_module.escape(str(hero.get('story', '')))
            
            # Ability scores display
            stats_html = ''
            if show_stats:
                stats_html = '<div class="featured-abilities">'
                for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                    val = hero.get(stat, 10)
                    stats_html += f'<span class="ability-badge"><span class="ability-name">{stat.upper()}</span><span class="ability-value">{val}</span></span>'
                stats_html += '</div>'
            
            story_html = f'<p class="featured-story">{story}</p>' if story else ''
            equipment_html = f'<div class="featured-equipment"><i class="fa-solid fa-swords"></i> {equipment}</div>' if equipment else ''
            
            cards_html += (
                f'<div class="featured-card">'
                f'<div class="featured-header">'
                f'<h3 class="featured-name">{name}</h3>'
                f'<span class="featured-class">{char_class} Lvl {level}</span>'
                f'</div>'
                f'<div class="featured-meta">'
                f'<span><i class="fa-solid fa-heart"></i> {hp} HP</span>'
                f'<span><i class="fa-solid fa-scroll"></i> {background}</span>'
                f'</div>'
                f'{stats_html}'
                f'{equipment_html}'
                f'{story_html}'
                f'</div>'
            )
        
        return f'<div class="featured-section"><h3 class="featured-title">{html_module.escape(title)}</h3><div class="featured-grid">{cards_html}</div></div>'
    
    def _render_ability_scores(self, comp: Dict) -> str:
        """Render party ability score averages as stat cards."""
        title = comp.get('title', 'Party Ability Scores')
        show_average = comp.get('show_average', True)
        
        ability_names = {
            'str': ('Strength', 'fa-fist-raised'),
            'dex': ('Dexterity', 'fa-feather'),
            'con': ('Constitution', 'fa-heart-pulse'),
            'int': ('Intelligence', 'fa-brain'),
            'wis': ('Wisdom', 'fa-eye'),
            'cha': ('Charisma', 'fa-comments'),
        }
        
        cards_html = ''
        for stat, (name, icon) in ability_names.items():
            if stat in self.stats:
                avg = round(self.stats[stat].get('mean', 10), 1)
                max_val = self.stats[stat].get('max', 10)
                min_val = self.stats[stat].get('min', 10)
            else:
                avg, max_val, min_val = 10, 10, 10
            
            # Color variant based on average score
            if avg >= 16:
                variant = 'ok'
            elif avg >= 12:
                variant = 'info'
            elif avg >= 10:
                variant = 'default'
            else:
                variant = 'warn'
            
            cards_html += (
                f'<div class="stat-card stat-{variant} ability-card">'
                f'<div class="stat-value"><i class="fa-solid {icon}"></i> {avg}</div>'
                f'<div class="stat-label">{name}</div>'
                f'<div class="stat-range">{min_val} - {max_val}</div>'
                f'</div>'
            )
        
        return f'<div class="ability-scores-section"><h3 class="ability-title">{title}</h3><div class="stats-row ability-row">{cards_html}</div></div>'
    
    def _render_story_section(self, comp: Dict) -> str:
        """Render character stories section."""
        import html as html_module
        title = comp.get('title', 'Character Stories')
        show_all = comp.get('show_all', False)
        featured_only = comp.get('featured_only', True)
        
        # Filter characters with stories
        if featured_only:
            characters = [d for d in self.data_points if d.get('featured') in (True, 'true', 'True', 1, '1', 'yes', 'Yes') and d.get('story')]
        elif show_all:
            characters = [d for d in self.data_points if d.get('story')]
        else:
            # Default: show first 5 with stories
            characters = [d for d in self.data_points if d.get('story')][:5]
        
        if not characters:
            return '<div class="story-section"><p class="no-stories">No character stories found. Add backstories to your characters!</p></div>'
        
        stories_html = ''
        for char in characters:
            # Escape all user-sourced content
            name = html_module.escape(str(char.get('name', 'Unknown')))
            char_class = html_module.escape(str(char.get('class', 'Adventurer')))
            story = html_module.escape(str(char.get('story', '')))
            
            stories_html += (
                f'<div class="story-card">'
                f'<div class="story-header">'
                f'<span class="story-name">{name}</span>'
                f'<span class="story-class">{char_class}</span>'
                f'</div>'
                f'<p class="story-text">{story}</p>'
                f'</div>'
            )
        
        return f'<div class="story-section"><h3 class="story-title">{html_module.escape(title)}</h3>{stories_html}</div>'
    
    def _render_initiative_tracker(self, comp: Dict) -> str:
        """Render an initiative tracker for combat encounters."""
        import html as html_module
        title = comp.get('title', 'Initiative Order')
        
        # Sort characters by DEX for default initiative order
        sorted_chars = sorted(self.data_points, key=lambda x: x.get('dex', 10), reverse=True)
        
        rows_html = ''
        for i, char in enumerate(sorted_chars[:10], 1):
            # Escape all user-sourced content
            name = html_module.escape(str(char.get('name', 'Unknown')))
            char_class = html_module.escape(str(char.get('class', '')))
            hp = char.get('hp', 0)
            dex = char.get('dex', 10)
            rows_html += (
                f'<tr class="initiative-row">'
                f'<td class="init-order">{i}</td>'
                f'<td class="init-name">{name}</td>'
                f'<td class="init-class">{char_class}</td>'
                f'<td class="init-hp"><i class="fa-solid fa-heart"></i> {hp}</td>'
                f'<td class="init-dex">DEX {dex}</td>'
                f'<td class="init-notes"><input type="text" placeholder="Notes..." class="init-input"></td>'
                f'</tr>'
            )
        
        return (
            f'<div class="initiative-tracker">'
            f'<h3 class="initiative-title"><i class="fa-solid fa-dice-d20"></i> {html_module.escape(title)}</h3>'
            f'<table class="initiative-table">'
            f'<thead><tr><th>#</th><th>Name</th><th>Class</th><th>HP</th><th>Init</th><th>Notes</th></tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table>'
            f'</div>'
        )
    
    def _render_quick_cards(self, comp: Dict) -> str:
        """Render quick reference cards for each character."""
        import html as html_module
        title = html_module.escape(str(comp.get('title', 'Quick Reference Cards')))
        featured_only = comp.get('featured_only', False)
        
        if featured_only:
            characters = [d for d in self.data_points if d.get('featured') in (True, 'true', 'True', 1, '1', 'yes', 'Yes')]
        else:
            characters = self.data_points[:8]  # Limit to 8 for display
        
        cards_html = ''
        for char in characters:
            # Escape all user-sourced content
            name = html_module.escape(str(char.get('name', 'Unknown')))
            race = html_module.escape(str(char.get('race', 'Unknown')))
            char_class = html_module.escape(str(char.get('class', 'Adventurer')))
            level = char.get('level', 1)
            hp = char.get('hp', 0)
            equipment = html_module.escape(str(char.get('equipment', '')))
            proficiencies = html_module.escape(str(char.get('proficiencies', '')))
            spells = html_module.escape(str(char.get('spells', '')))
            languages = html_module.escape(str(char.get('languages', 'Common')))
            
            # Build ability scores mini-display
            abilities_html = ''
            for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                val = char.get(stat, 10)
                mod = (val - 10) // 2
                mod_str = f'+{mod}' if mod >= 0 else str(mod)
                abilities_html += f'<span class="qc-stat"><b>{stat.upper()}</b> {val} ({mod_str})</span>'
            
            spells_html = f'<div class="qc-spells"><i class="fa-solid fa-wand-sparkles"></i> {spells}</div>' if spells and spells != 'None' else ''
            
            cards_html += (
                f'<div class="quick-card">'
                f'<div class="qc-header">'
                f'<span class="qc-name">{name}</span>'
                f'<span class="qc-race-class">{race} {char_class} {level}</span>'
                f'</div>'
                f'<div class="qc-hp"><i class="fa-solid fa-heart"></i> {hp} HP</div>'
                f'<div class="qc-abilities">{abilities_html}</div>'
                f'<div class="qc-proficiencies"><i class="fa-solid fa-star"></i> {proficiencies}</div>'
                f'{spells_html}'
                f'<div class="qc-languages"><i class="fa-solid fa-language"></i> {languages}</div>'
                f'<div class="qc-equipment"><i class="fa-solid fa-swords"></i> {equipment}</div>'
                f'</div>'
            )
        
        return f'<div class="quick-cards-section"><h3 class="qc-title">{title}</h3><div class="quick-cards-grid">{cards_html}</div></div>'
    
    def _render_quote_box(self, comp: Dict) -> str:
        """Render a dramatic quote box for NPC dialogue."""
        import html as html_module
        # Escape config-sourced values
        quote = html_module.escape(str(comp.get('quote', 'Your fate is sealed, adventurers...')))
        speaker = html_module.escape(str(comp.get('speaker', 'Mysterious Figure')))
        title = html_module.escape(str(comp.get('title', '')))
        icon = comp.get('icon', 'fa-comment-dots')
        variant = comp.get('variant', 'default')
        
        title_html = f'<div class="quote-title">{title}</div>' if title else ''
        
        return (
            f'<div class="quote-box quote-{variant}">'
            f'{title_html}'
            f'<div class="quote-icon"><i class="fa-solid {icon}"></i></div>'
            f'<blockquote class="quote-text">"{quote}"</blockquote>'
            f'<cite class="quote-speaker">— {speaker}</cite>'
            f'</div>'
        )
    
    def _render_encounter_card(self, comp: Dict) -> str:
        """Render an encounter card with enemy stat block style."""
        import html as html_module
        # Escape config-sourced values
        title = html_module.escape(str(comp.get('title', 'Encounter')))
        name = html_module.escape(str(comp.get('name', 'Mysterious Enemy')))
        cr = html_module.escape(str(comp.get('cr', '???')))
        hp = html_module.escape(str(comp.get('hp', '???')))
        ac = html_module.escape(str(comp.get('ac', '???')))
        description = html_module.escape(str(comp.get('description', 'A dangerous foe awaits...')))
        abilities = html_module.escape(str(comp.get('abilities', '')))
        tactics = html_module.escape(str(comp.get('tactics', '')))
        icon = comp.get('icon', 'fa-skull')
        
        abilities_html = f'<div class="enc-abilities"><b>Abilities:</b> {abilities}</div>' if abilities else ''
        tactics_html = f'<div class="enc-tactics"><b>Tactics:</b> {tactics}</div>' if tactics else ''
        
        return (
            f'<div class="encounter-card">'
            f'<div class="enc-header">'
            f'<i class="fa-solid {icon} enc-icon"></i>'
            f'<span class="enc-name">{name}</span>'
            f'<span class="enc-cr">CR {cr}</span>'
            f'</div>'
            f'<div class="enc-stats">'
            f'<span class="enc-stat"><i class="fa-solid fa-shield"></i> AC {ac}</span>'
            f'<span class="enc-stat"><i class="fa-solid fa-heart"></i> HP {hp}</span>'
            f'</div>'
            f'<div class="enc-description">{description}</div>'
            f'{abilities_html}'
            f'{tactics_html}'
            f'</div>'
        )
    

    def _render_yaml(self, comp_type: str, comp: Dict) -> str:
        """Render using YAML template."""
        template_def = self.templates.get(comp_type)
        template_str = template_def.get('template', '')
        
        # Build context - order matters! Prepared context should override raw props
        context = self._get_base_context()
        
        # Add raw component props first
        for key, value in comp.items():
            if key != 'type':
                # Eval Jinja expressions in values
                if isinstance(value, str) and '{{' in value:
                    context[key] = eval_template(value, self.data_points, self.stats)
                else:
                    context[key] = value
        
        # Add prepared context (overwrites raw props where needed)
        context.update(self._prepare_context(comp_type, comp))
        
        return self._render_template(template_str, context)
    
    def _prepare_context(self, comp_type: str, comp: Dict) -> Dict[str, Any]:
        """Prepare component-specific context."""
        ctx = {}
        
        if '_stat_card' in comp_type:
            value_template = comp.get('value', '0')
            ctx['value'] = eval_template(value_template, self.data_points, self.stats)
            ctx['variant'] = comp.get('variant', 'default')
        
        elif '_llm' in comp_type:
            comp_id = comp.get('id', 'unknown')
            ctx['llm_content'] = self.llm_content.get(comp_id, '<em>No content</em>')
        
        elif '_data_table' in comp_type:
            columns = comp.get('columns', ['name', 'score'])
            # Show all rows by default, or use page_size if explicitly set
            page_size = comp.get('page_size')
            if page_size is None or page_size <= 0:
                ctx['table_rows'] = self.data_points  # Show ALL rows
            else:
                ctx['table_rows'] = self.data_points[:page_size]
            ctx['columns'] = columns
        
        return ctx
    
    def _render_chart(self, comp: Dict) -> str:
        """Render chart component (needs JS)."""
        chart_id = comp.get('id', f'chart_{len(self.charts_js)}')
        chart_type = comp.get('chart', 'bar')
        title = comp.get('title', 'Chart')
        
        chart_config = {
            'id': chart_id,
            'type': chart_type,
            'title': title,
            'x_field': comp.get('x', 'name'),
            'y_field': comp.get('y', 'score'),
        }
        js = self.chart_gen.generate_chart(self.data_points, self.stats, None, chart_config, self.theme)
        self.charts_js.append(js)
        
        # Use template if available
        comp_type = f'{self.safe_name}_chart'
        if self.templates.has(comp_type):
            template_def = self.templates.get(comp_type)
            context = self._get_base_context()
            context['chart_id'] = chart_id
            context['title'] = title
            return self._render_template(template_def.get('template', ''), context)
        
        return f'<div class="chart-card"><h3>{title}</h3><div class="chart-container"><canvas id="{chart_id}"></canvas></div></div>'
    
    def _render_custom(self, comp_type: str, comp: Dict) -> str:
        """Render inline custom component."""
        custom_def = self.custom_components[comp_type]
        template_str = custom_def.get('template', '')
        if not template_str:
            return f'<!-- {comp_type} has no template -->'
        
        context = self._get_base_context()
        for key, value in comp.items():
            if key != 'type':
                if isinstance(value, str) and '{{' in value:
                    context[key] = eval_template(value, self.data_points, self.stats)
                else:
                    context[key] = value
        
        html = self._render_template(template_str, context)
        css = custom_def.get('css', '')
        if css:
            html = f'<style>{css}</style>\\n{html}'
        return html


def eval_template(template: str, data_points: List[Dict], stats: Dict[str, Any]) -> str:
    """
    Render template using Jinja2 for full expression support.
    
    Supports all Jinja2 features:
    - Filters: {{ value | round(2) }}, {{ items | sum(attribute='score') }}
    - Conditionals: {{ 'Good' if score > 80 else 'Needs work' }}
    - Math: {{ stats.score.mean * 100 }}%
    - List operations: {{ data_points | length }}, {{ data_points | first }}
    
    Context variables available:
    - data_points: List of all data records
    - stats: Dictionary of statistics per field
    - len: Python's len() function
    """
    from jinja2 import Template, Environment
    
    try:
        # Create Jinja2 environment with autoescape and useful globals
        env = Environment(autoescape=True)
        env.globals['len'] = len
        env.globals['min'] = min
        env.globals['max'] = max
        env.globals['sum'] = sum
        env.globals['abs'] = abs
        env.globals['round'] = round
        
        # Prepare context
        context = {
            'data_points': data_points,
            'stats': stats,
        }
        
        # Handle template string - may or may not have {{ }}
        tmpl_str = template.strip()
        if not tmpl_str.startswith('{{'):
            # Wrap in {{ }} if not already a Jinja expression
            if '{{' not in tmpl_str:
                return tmpl_str  # Plain text, return as-is
        
        tpl = env.from_string(tmpl_str)
        result = tpl.render(**context)
        return result
        
    except Exception as e:
        # Fallback: return template as-is if rendering fails
        return template.replace('{{', '').replace('}}', '').strip()


def generate_report(
    data_dir: str,
    output_dir: str,
    config_path: Optional[str] = None,
    theme_id: Optional[str] = None,
    dry_run: bool = False
) -> Path:
    """
    Generate an HTML report from data files using YAML configuration.
    
    Parameters:
        data_dir: Directory containing data files
        output_dir: Directory to write HTML output
        config_path: Path to report_config.yaml (defaults to plugin dir)
        theme_id: Theme ID to use (defaults to config's theme setting)
        dry_run: If True, skip LLM calls
    
    Returns:
        Path to the generated index.html
    """
    import html
    plugin_dir = Path(__file__).parent
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load config
    if config_path:
        config = load_config(Path(config_path))
    else:
        config = load_config(plugin_dir / 'report_config.yaml')
    
    # Get theme
    theme = THEMES.get(theme_id) or THEMES.get(config.get('theme', 'dungeon')) or ''' + safe_name.upper() + '''_DUNGEON
    theme_css = get_theme_css_variables(theme)
    font_link = f'<link href="{theme.font_url}" rel="stylesheet">' if theme.font_url else ''
    
    # Load plugin CSS from templates
    css_path = plugin_dir / 'templates' / ''' + "'" + safe_name + "'" + ''' / 'static' / 'plugin.css'
    if css_path.exists():
        plugin_css = css_path.read_text(encoding='utf-8')
    else:
        plugin_css = '/* plugin.css not found */'

    
    # Parse data
    parser = ''' + class_name + '''CsvParser()
    data_points = parser.parse_directory(data_path)
    
    if not data_points:
        raise ValueError(f"No data found in {data_dir}")
    
    # Calculate stats
    stats = calculate_stats(data_points)
    
    # Generate LLM content
    llm_content = generate_llm_content(config, data_points, stats, dry_run)
    
    # Initialize chart generator and template loader
    chart_gen = ''' + class_name + '''ChartGenerator()
    charts_js = []
    template_loader = TemplateLoader(plugin_dir)
    
    # Get custom components from config (if any)
    custom_components = config.get('custom_components', {})
    
    # Create component renderer
    renderer = ComponentRenderer(
        data_points, stats, llm_content, charts_js, chart_gen,
        theme, "''' + safe_name + '''", template_loader, custom_components
    )
    
    # Render pages
    pages = config.get('pages', [])
    nav_html = ''
    pages_html = ''
    
    for i, page in enumerate(pages):
        page_id = page.get('id', f'page_{i}')
        page_id_escaped = html.escape(page_id, quote=True)  # Escape quotes for JS context
        page_title = page.get('title', f'Page {i+1}')
        page_title_escaped = html.escape(page_title, quote=True)
        active_class = 'active' if i == 0 else ''
        
        # Navigation tab - use escaped values in onclick and content
        nav_html += f'<button class="tab-btn {active_class}" onclick="showPage(\\'{page_id_escaped}\\', event)">{page_title_escaped}</button>'
        
        # Page content
        components_html = ''
        layout = page.get('layout', 'grid')
        
        for comp in page.get('components', []):
            comp_html = renderer.render(comp)
            components_html += comp_html
        
        layout_class = {'grid': 'layout-grid', 'single-column': 'layout-single', 'flex': 'layout-flex'}.get(layout, 'layout-grid')
        pages_html += f'<div id="{page_id_escaped}" class="page-content {active_class} {layout_class}">{components_html}</div>'
    
    # Build final HTML
    report_name = config.get('name', "''' + name + ''' Report")
    report_name_escaped = html.escape(report_name)
    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name_escaped}</title>
    {font_link}
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
{theme_css}
""" + plugin_css + f"""
    </style>

</head>
<body>
    <div class="container">
        <header>
            <h1>{report_name_escaped}</h1>
            <p>Theme: {theme.name} | {len(data_points)} items</p>
        </header>
        <nav class="tabs">{nav_html}</nav>
        {pages_html}
    </div>
    <script>
function showPage(pageId, event) {{
    document.querySelectorAll('.page-content').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    if (event && event.target) {{
        event.target.classList.add('active');
    }}
}}
{''.join(charts_js)}
    </script>
</body>
</html>"""
    
    # Write output
    output_file = output_path / 'index.html'
    output_file.write_text(html_output, encoding='utf-8')
    
    mode_str = " (dry-run)" if dry_run else ""
    print(f"✓ Report generated{mode_str}: {output_file}")
    print(f"  Pages: {len(pages)}")
    print(f"  Data points: {len(data_points)}")
    print(f"  LLM sections: {len(llm_content)}")
    
    return output_file
'''

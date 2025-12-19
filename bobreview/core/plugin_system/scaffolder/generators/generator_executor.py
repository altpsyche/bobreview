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


def generate_llm_content(
    config: Dict[str, Any],
    data_points: List[Dict],
    stats: Dict[str, Any],
    dry_run: bool = False
) -> Dict[str, str]:
    """Generate LLM content for all prompts in YAML config."""
    from jinja2 import Environment
    
    # Create Jinja2 environment for rendering prompts
    env = Environment()
    env.globals['len'] = len
    env.globals['min'] = min
    env.globals['max'] = max
    env.globals['sum'] = sum
    env.globals['round'] = round
    
    llm_content = {}
    
    for page in config.get('pages', []):
        for comp in page.get('components', []):
            comp_type = comp.get('type', '')
            if '_llm' in comp_type:
                comp_id = comp.get('id', 'unknown')
                prompt_template = comp.get('prompt', '')
                
                # Render prompt with Jinja2 to process variables and for-loops
                try:
                    tpl = env.from_string(prompt_template)
                    rendered_prompt = tpl.render(
                        data_points=data_points,
                        stats=stats,
                    )
                except Exception as e:
                    rendered_prompt = f"[Template Error: {e}]\\n{prompt_template}"
                
                if dry_run:
                    # Show more of the rendered prompt in dry-run mode
                    preview = rendered_prompt[:200].replace('\\n', ' ')
                    llm_content[comp_id] = f'<div class="llm-dry-run"><em>[LLM Placeholder: {comp.get("title", comp_id)}]</em><br><small>Prompt: {preview}...</small></div>'
                else:
                    try:
                        from bobreview.services.llm.client import call_llm
                        from bobreview.core.config import Config
                        from bobreview.core.cache import init_cache
                        from bobreview.core.html_utils import sanitize_llm_html
                        llm_config = Config()
                        init_cache(llm_config)
                        response = call_llm(rendered_prompt, config=llm_config)
                        # Convert markdown to HTML and sanitize
                        if response:
                            llm_content[comp_id] = sanitize_llm_html(response)
                        else:
                            llm_content[comp_id] = f'<em>No response for {comp_id}</em>'
                    except Exception as e:
                        llm_content[comp_id] = f'<div class="llm-error">LLM Error: {e}</div>'
    
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
        
        # Jinja2 environment
        from jinja2 import Environment
        self.env = Environment()
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
        
        # Check YAML templates
        if self.templates.has(comp_type):
            return self._render_yaml(comp_type, comp)
        
        return f'<!-- Unknown: {comp_type} -->'
    
    def _render_stat_row(self, comp: Dict) -> str:
        """Render a row of stat cards side-by-side."""
        items = comp.get('items', [])
        cards_html = ''
        for item in items:
            value = eval_template(item.get('value', '0'), self.data_points, self.stats)
            label = item.get('label', '')
            variant = item.get('variant', 'default')
            icon = item.get('icon', '')
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
        title = comp.get('title', '')
        subtitle = comp.get('subtitle', '')
        if '{{' in title:
            title = eval_template(title, self.data_points, self.stats)
        if '{{' in subtitle:
            subtitle = eval_template(subtitle, self.data_points, self.stats)
        icon = comp.get('icon', 'fa-flag')
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
        label = comp.get('label', '')
        if label:
            return f'<div class="section-divider"><span>{label}</span></div>'
        return '<div class="section-divider"></div>'
    
    def _render_progress_bar(self, comp: Dict) -> str:
        """Render a progress bar visualization."""
        label = comp.get('label', 'Progress')
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
        title = comp.get('title', 'Champion')
        field = comp.get('field', 'level')
        mode = comp.get('mode', 'max')  # max or min
        
        if not self.data_points:
            return '<div class="member-spotlight">No members</div>'
        
        # Find member by max/min
        if mode == 'max':
            member = max(self.data_points, key=lambda x: x.get(field, 0))
        else:
            member = min(self.data_points, key=lambda x: x.get(field, 0))
        
        name = member.get('name', 'Unknown')
        background = member.get('background', '')
        char_class = member.get('class', '')
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
            f'<div class="member-spotlight">'
            f'<div class="spotlight-badge"><i class="fa-solid {icon}"></i></div>'
            f'<div class="spotlight-content">'
            f'<h3 class="spotlight-title">{title}</h3>'
            f'<div class="spotlight-name">{name}</div>'
            f'<div class="spotlight-details">{char_class} • {background}</div>'
            f'<div class="spotlight-stats">'
            f'<span class="spotlight-stat"><i class="fa-solid fa-star"></i> Lvl {level}</span>'
            f'<span class="spotlight-stat"><i class="fa-solid fa-heart"></i> {hp} HP</span>'
            f'</div>'
            f'<div class="spotlight-abilities">{ability_str}</div>'
            f'</div></div>'
        )
    
    def _render_featured_section(self, comp: Dict) -> str:
        """Render a featured characters section with 1-4 highlighted heroes."""
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
            name = hero.get('name', 'Unknown')
            char_class = hero.get('class', 'Adventurer')
            level = hero.get('level', 1)
            hp = hero.get('hp', 0)
            background = hero.get('background', '')
            equipment = hero.get('equipment', '')
            story = hero.get('story', '')
            
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
        
        return f'<div class="featured-section"><h3 class="featured-title">{title}</h3><div class="featured-grid">{cards_html}</div></div>'
    
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
            name = char.get('name', 'Unknown')
            char_class = char.get('class', 'Adventurer')
            story = char.get('story', '')
            
            stories_html += (
                f'<div class="story-card">'
                f'<div class="story-header">'
                f'<span class="story-name">{name}</span>'
                f'<span class="story-class">{char_class}</span>'
                f'</div>'
                f'<p class="story-text">{story}</p>'
                f'</div>'
            )
        
        return f'<div class="story-section"><h3 class="story-title">{title}</h3>{stories_html}</div>'
    
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
            page_size = comp.get('page_size', 10)
            ctx['columns'] = columns
            ctx['table_rows'] = self.data_points[:page_size]
        
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
        # Create Jinja2 environment with useful globals
        env = Environment()
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
        page_title = page.get('title', f'Page {i+1}')
        page_title_escaped = html.escape(page_title)
        active_class = 'active' if i == 0 else ''
        
        # Navigation tab
        nav_html += f'<button class="tab-btn {active_class}" onclick="showPage(\\'{page_id}\\', event)">{page_title_escaped}</button>'
        
        # Page content
        components_html = ''
        layout = page.get('layout', 'grid')
        
        for comp in page.get('components', []):
            comp_html = renderer.render(comp)
            components_html += comp_html
        
        layout_class = {'grid': 'layout-grid', 'single-column': 'layout-single', 'flex': 'layout-flex'}.get(layout, 'layout-grid')
        pages_html += f'<div id="{page_id}" class="page-content {active_class} {layout_class}">{components_html}</div>'
    
    # Build final HTML
    report_name = config.get('name', "''' + name + ''' Report")
    report_name_escaped = html.escape(report_name)
    html = f"""<!DOCTYPE html>
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
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* ---------------------------------------------------------------------------
   D&D FANTASY PARCHMENT THEME - Medieval Tavern Aesthetic
   --------------------------------------------------------------------------- */

body {{ 
    font-family: var(--font-family); 
    background: 
        radial-gradient(ellipse at top, var(--bg-soft) 0%, transparent 50%),
        radial-gradient(ellipse at bottom, var(--bg) 0%, transparent 50%),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-elevated) 50%, var(--bg) 100%);
    background-attachment: fixed;
    color: var(--text-main); 
    min-height: 100vh;
    line-height: 1.7;
}}

/* Parchment texture overlay */
body::before {{
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.03;
    pointer-events: none;
    z-index: -1;
}}

.container {{ 
    max-width: 1200px; 
    margin: 0 auto; 
    padding: 2rem;
    position: relative;
}}

/* ---------------------------------------------------------------------------
   ORNATE HEADER - Guild Banner Style
   --------------------------------------------------------------------------- */
header {{ 
    text-align: center; 
    margin-bottom: 2rem; 
    padding: 2.5rem 2rem;
    background: linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 3px solid var(--accent);
    border-radius: 4px;
    position: relative;
    box-shadow: 
        inset 0 0 60px rgba(0, 0, 0, 0.5),
        0 10px 40px rgba(0, 0, 0, 0.6);
}}

/* Corner decorations */
header::before, header::after {{
    content: '\\f6d1';
    font-family: 'Font Awesome 6 Free';
    font-weight: 900;
    position: absolute;
    color: var(--accent);
    font-size: 1rem;
    text-shadow: 0 0 10px var(--accent);
}}
header::before {{ top: -0.6rem; left: 50%; transform: translateX(-50%); }}
header::after {{ bottom: -0.6rem; left: 50%; transform: translateX(-50%) rotate(180deg); }}

header h1 {{ 
    color: var(--accent-strong);
    font-size: 2.5rem; 
    font-weight: 700;
    margin-bottom: 0.5rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    text-shadow: 
        0 0 20px var(--accent-soft),
        0 4px 8px rgba(0, 0, 0, 0.8);
}}
header p {{ 
    color: var(--text-soft); 
    font-size: 0.95rem; 
    font-style: italic;
    letter-spacing: 0.05em;
}}

/* ---------------------------------------------------------------------------
   NAVIGATION TABS - Tavern Menu Boards
   --------------------------------------------------------------------------- */
.tabs {{ 
    display: flex; 
    justify-content: center;
    gap: 0.75rem; 
    margin-bottom: 2rem; 
    flex-wrap: wrap;
    padding: 1rem;
    background: linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg) 100%);
    border: 2px solid var(--border-subtle);
    border-radius: 4px;
}}
.tabs::before {{
    content: '---  GUILD HALL  ---';
    display: block;
    width: 100%;
    text-align: center;
    color: var(--accent);
    font-size: 0.7rem;
    letter-spacing: 0.3em;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
}}
.tab-btn {{ 
    background: linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    color: var(--text-main); 
    border: 2px solid var(--border-subtle); 
    padding: 0.85rem 1.75rem; 
    cursor: pointer; 
    font-size: 1rem; 
    font-weight: 600;
    font-family: var(--font-family);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    transition: all 0.2s ease;
    position: relative;
}}
.tab-btn:hover {{ 
    background: var(--bg-soft);
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px var(--accent-soft);
}}
.tab-btn.active {{ 
    background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
    color: var(--bg); 
    border-color: var(--accent-strong);
    box-shadow: 
        0 0 20px var(--accent-soft),
        inset 0 1px 0 rgba(255, 255, 255, 0.2);
}}

/* ---------------------------------------------------------------------------
   PAGE LAYOUTS
   --------------------------------------------------------------------------- */
.layout-grid {{ 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); 
    gap: 1.5rem;
    padding: 1rem 0;
}}
.layout-single {{ 
    display: flex; 
    flex-direction: column; 
    gap: 1.5rem;
    padding: 1rem 0;
}}
.layout-flex {{ 
    display: flex; 
    flex-wrap: wrap; 
    gap: 1.5rem;
    padding: 1rem 0;
}}

.page-content {{ 
    display: none !important; 
    animation: unfurl 0.5s ease;
}}
.page-content.active {{ display: block !important; }}
.page-content.active.layout-grid {{ display: grid !important; }}
.page-content.active.layout-single {{ display: flex !important; }}
.page-content.active.layout-flex {{ display: flex !important; }}

@keyframes unfurl {{
    from {{ opacity: 0; transform: scale(0.98) translateY(10px); }}
    to {{ opacity: 1; transform: scale(1) translateY(0); }}
}}

/* ---------------------------------------------------------------------------
   STAT CARDS - D&D Character Ability Score Blocks
   --------------------------------------------------------------------------- */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
}}

.stat-card {{ 
    background: linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 3px solid var(--border-subtle);
    border-top: 4px solid var(--accent);
    padding: 1.5rem 1rem;
    text-align: center;
    position: relative;
    transition: all 0.2s ease;
}}
.stat-card::before {{
    content: '\\f3c5';
    font-family: 'Font Awesome 6 Free';
    font-weight: 900;
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    color: var(--accent);
    font-size: 0.75rem;
    background: var(--bg-elevated);
    padding: 0 0.5rem;
}}
.stat-card:hover {{ 
    transform: translateY(-3px); 
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
    border-color: var(--accent);
}}
.stat-value {{ 
    color: var(--accent-strong);
    font-size: 2.5rem; 
    font-weight: 700;
    line-height: 1;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}}
.stat-label {{ 
    color: var(--text-soft); 
    font-size: 0.75rem; 
    text-transform: uppercase; 
    letter-spacing: 0.15em;
    margin-top: 0.75rem;
    font-weight: 600;
}}

/* Variant colors for different stat types */
.stat-ok {{ border-top-color: var(--ok); }}
.stat-ok .stat-value {{ color: var(--ok); }}
.stat-ok::before {{ color: var(--ok); }}

.stat-warn {{ border-top-color: var(--warn); }}
.stat-warn .stat-value {{ color: var(--warn); }}
.stat-warn::before {{ color: var(--warn); }}

.stat-danger {{ border-top-color: var(--danger); }}
.stat-danger .stat-value {{ color: var(--danger); }}
.stat-danger::before {{ color: var(--danger); }}

.stat-info {{ border-top-color: var(--accent); }}

/* ---------------------------------------------------------------------------
   STATS ROW - Horizontal stat card layout
   --------------------------------------------------------------------------- */
.stats-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
}}
.stats-row .stat-card {{
    flex: 1 1 150px;
    min-width: 140px;
    max-width: 250px;
}}

/* ---------------------------------------------------------------------------
   HERO BANNER - Featured highlight section
   --------------------------------------------------------------------------- */
.hero-banner {{
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem 2rem;
    background: linear-gradient(135deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--accent);
    border-left: 6px solid var(--accent);
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}}
.hero-banner::after {{
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 100%;
    background: linear-gradient(90deg, transparent, var(--accent-soft));
}}
.hero-icon {{
    font-size: 2.5rem;
    color: var(--accent);
    text-shadow: 0 0 20px var(--accent-soft);
}}
.hero-content {{ flex: 1; }}
.hero-title {{
    color: var(--accent-strong);
    font-size: 1.5rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}}
.hero-subtitle {{
    color: var(--text-soft);
    font-size: 0.95rem;
    font-style: italic;
}}
.hero-ok {{ border-left-color: var(--ok); }}
.hero-ok .hero-icon {{ color: var(--ok); }}
.hero-warn {{ border-left-color: var(--warn); }}
.hero-warn .hero-icon {{ color: var(--warn); }}
.hero-danger {{ border-left-color: var(--danger); }}
.hero-danger .hero-icon {{ color: var(--danger); }}

/* ---------------------------------------------------------------------------
   SECTION DIVIDER - Visual separator with label
   --------------------------------------------------------------------------- */
.section-divider {{
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 1.5rem 0;
    color: var(--text-soft);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
}}
.section-divider::before,
.section-divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-subtle), transparent);
}}
.section-divider span {{
    color: var(--accent);
    padding: 0 0.5rem;
}}

/* ---------------------------------------------------------------------------
   PROGRESS BAR - Visual progress indicator
   --------------------------------------------------------------------------- */
.progress-card {{
    background: linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--border-subtle);
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}}
.progress-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}}
.progress-label {{
    color: var(--accent);
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.progress-values {{
    color: var(--text-soft);
    font-size: 0.8rem;
}}
.progress-bar-container {{
    position: relative;
    height: 24px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 2px;
    overflow: visible;
}}
.progress-bar {{
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-strong));
    border-radius: 2px;
    transition: width 0.5s ease;
}}
.progress-ok {{ background: linear-gradient(90deg, var(--ok), #22c55e); }}
.progress-warn {{ background: linear-gradient(90deg, var(--warn), #fbbf24); }}
.progress-danger {{ background: linear-gradient(90deg, var(--danger), #ef4444); }}
.progress-marker {{
    position: absolute;
    top: -8px;
    transform: translateX(-50%);
}}
.progress-current {{
    background: var(--accent);
    color: var(--bg);
    padding: 0.2rem 0.5rem;
    border-radius: 2px;
    font-size: 0.75rem;
    font-weight: 700;
}}

/* ---------------------------------------------------------------------------
   MEMBER SPOTLIGHT - Featured adventurer card
   --------------------------------------------------------------------------- */
.member-spotlight {{
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 1.5rem;
    background: linear-gradient(135deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--accent);
    position: relative;
    overflow: hidden;
}}
.member-spotlight::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent-strong), var(--accent));
}}
.spotlight-badge {{
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: var(--bg);
    box-shadow: 0 4px 15px var(--accent-soft);
}}
.spotlight-content {{ flex: 1; }}
.spotlight-title {{
    color: var(--accent);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.25rem;
}}
.spotlight-name {{
    color: var(--accent-strong);
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}}
.spotlight-details {{
    color: var(--text-soft);
    font-size: 0.9rem;
    font-style: italic;
    margin-bottom: 0.5rem;
}}
.spotlight-stats {{
    display: flex;
    gap: 1rem;
}}
.spotlight-stat {{
    color: var(--text-main);
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}
.spotlight-stat i {{
    color: var(--accent);
}}

/* ---------------------------------------------------------------------------
   CHARTS - Parchment Scroll Style
   --------------------------------------------------------------------------- */
.chart-card {{ 
    background: linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--border-subtle);
    padding: 1.5rem;
    position: relative;
    box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.3);
}}
.chart-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}}
.chart-card h3 {{ 
    color: var(--accent); 
    font-size: 1.1rem; 
    font-weight: 600;
    margin-bottom: 1rem;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-subtle);
}}
.chart-container {{ position: relative; height: 280px; }}

/* ---------------------------------------------------------------------------
   LLM CONTENT - Ancient Scroll/Tome Style
   --------------------------------------------------------------------------- */
.llm-section {{ 
    background: 
        linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--accent);
    border-left: 6px solid var(--accent);
    padding: 2rem;
    grid-column: 1 / -1;
    position: relative;
    box-shadow: 
        inset 0 0 40px rgba(0, 0, 0, 0.4),
        0 8px 30px rgba(0, 0, 0, 0.4);
}}
.llm-section::before {{
    content: '\\f70e';
    font-family: 'Font Awesome 6 Free';
    font-weight: 900;
    position: absolute;
    top: -15px;
    left: 20px;
    font-size: 1.25rem;
    color: var(--accent);
    background: var(--bg-elevated);
    padding: 0 0.5rem;
}}
.llm-section h3 {{ 
    color: var(--accent-strong); 
    font-size: 1.25rem; 
    font-weight: 600;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px dashed var(--border-subtle);
    padding-bottom: 0.75rem;
}}
.llm-content {{ 
    color: var(--text-main); 
    line-height: 1.9;
    font-style: italic;
}}
.llm-content p {{ margin-bottom: 1rem; }}
.llm-content ul, .llm-content ol {{ margin: 1rem 0; padding-left: 1.5rem; }}
.llm-content strong {{ color: var(--accent-strong); font-style: normal; }}
.llm-dry-run {{ 
    color: var(--text-soft); 
    font-style: italic; 
    padding: 1.25rem; 
    background: rgba(0, 0, 0, 0.3);
    border-left: 3px dashed var(--accent);
}}
.llm-error {{ color: var(--danger); padding: 1rem; background: var(--danger-soft); }}

/* ---------------------------------------------------------------------------
   DATA TABLES - Guild Registry Ledger
   --------------------------------------------------------------------------- */
.table-section {{ 
    background: linear-gradient(180deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--border-subtle);
    padding: 1.5rem; 
    grid-column: 1 / -1; 
    overflow-x: auto;
    box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.3);
}}
.table-section h3 {{ 
    color: var(--accent); 
    font-size: 1.15rem; 
    font-weight: 600;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    text-align: center;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--border-subtle);
}}
.data-table {{ width: 100%; border-collapse: collapse; }}
.data-table th {{ 
    background: linear-gradient(180deg, var(--accent) 0%, var(--accent-strong) 100%);
    color: var(--bg); 
    text-align: left; 
    padding: 1rem; 
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border: 1px solid var(--accent);
}}
.data-table td {{ 
    padding: 0.85rem 1rem; 
    border-bottom: 1px solid var(--border-subtle);
    border-left: 1px solid var(--border-subtle);
    border-right: 1px solid var(--border-subtle);
}}
.data-table tr:nth-child(even) {{ background: rgba(0, 0, 0, 0.15); }}
.data-table tr:hover {{ 
    background: var(--accent-soft);
    box-shadow: inset 0 0 0 1px var(--accent);
}}
.table-info {{ color: var(--text-soft); font-size: 0.85rem; margin-top: 1rem; text-align: center; }}

/* ---------------------------------------------------------------------------
   FEATURED SECTION - Premium Hero Spotlight Cards
   --------------------------------------------------------------------------- */
.featured-section {{
    margin: 1.5rem 0;
    padding: 1.5rem;
    background: linear-gradient(135deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.1) 100%);
    border-radius: 12px;
    border: 1px solid var(--border-subtle);
}}
.featured-title {{
    color: var(--accent-strong);
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    text-shadow: 0 2px 8px var(--accent-soft);
}}
.featured-title::before,
.featured-title::after {{
    content: '★';
    font-size: 1rem;
    color: var(--accent);
    text-shadow: 0 0 10px var(--accent);
}}
.featured-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.5rem;
}}
.featured-card {{
    background: 
        linear-gradient(180deg, rgba(255,255,255,0.03) 0%, transparent 50%),
        linear-gradient(135deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 2px solid var(--border-subtle);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    box-shadow: 
        0 4px 20px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
}}
.featured-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--accent), var(--accent-strong), var(--accent));
    box-shadow: 0 0 20px var(--accent-soft);
}}
.featured-card::after {{
    content: '★';
    position: absolute;
    top: 12px;
    right: 12px;
    font-size: 1.25rem;
    color: var(--accent);
    text-shadow: 0 0 15px var(--accent);
    opacity: 0.6;
    transition: all 0.3s ease;
}}
.featured-card:hover {{
    transform: translateY(-6px) scale(1.02);
    border-color: var(--accent);
    box-shadow: 
        0 12px 40px rgba(0, 0, 0, 0.4),
        0 0 30px var(--accent-soft),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
}}
.featured-card:hover::after {{
    opacity: 1;
    transform: rotate(15deg) scale(1.2);
}}
.featured-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-subtle);
}}
.featured-name {{
    color: var(--accent-strong);
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
    letter-spacing: 0.02em;
}}
.featured-class {{
    color: var(--bg);
    font-size: 0.75rem;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
    padding: 0.35rem 0.75rem;
    border-radius: 20px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 2px 8px var(--accent-soft);
}}
.featured-meta {{
    display: flex;
    gap: 1.25rem;
    color: var(--text-main);
    font-size: 0.9rem;
    margin-bottom: 1.25rem;
    padding: 0.75rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
}}
.featured-meta span {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}
.featured-meta i {{
    color: var(--accent);
    font-size: 1rem;
}}
.featured-abilities {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.5rem;
    margin-bottom: 1.25rem;
    padding: 0.75rem;
    background: rgba(0, 0, 0, 0.15);
    border-radius: 8px;
    border: 1px solid var(--border-subtle);
}}
.ability-badge {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem 0.25rem;
    border-radius: 6px;
    transition: all 0.2s ease;
}}
.ability-badge:hover {{
    background: var(--accent-soft);
    transform: translateY(-2px);
}}
.ability-name {{
    font-size: 0.6rem;
    color: var(--text-soft);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
}}
.ability-value {{
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--accent-strong);
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}}
.featured-equipment {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-main);
    font-size: 0.85rem;
    margin-bottom: 1rem;
    padding: 0.75rem 1rem;
    background: linear-gradient(90deg, rgba(0,0,0,0.2) 0%, transparent 100%);
    border-left: 3px solid var(--accent);
    border-radius: 0 6px 6px 0;
}}
.featured-equipment i {{
    color: var(--accent);
    font-size: 1rem;
}}
.featured-story {{
    color: var(--text-main);
    font-size: 0.9rem;
    font-style: italic;
    line-height: 1.7;
    padding: 1rem 1.25rem;
    margin: 0;
    background: linear-gradient(135deg, rgba(0,0,0,0.15) 0%, transparent 100%);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    position: relative;
}}
.featured-story::before {{
    content: '"';
    position: absolute;
    top: 0.25rem;
    left: 0.5rem;
    font-size: 2rem;
    color: var(--accent);
    opacity: 0.3;
    font-style: normal;
}}
.no-featured {{
    color: var(--text-soft);
    font-style: italic;
    padding: 1rem;
    background: var(--bg-soft);
    border-radius: 8px;
    text-align: center;
}}

/* ---------------------------------------------------------------------------
   ABILITY SCORES SECTION - D&D Big Six Display
   --------------------------------------------------------------------------- */
.ability-scores-section {{
    margin: 1.5rem 0;
    padding: 1rem;
    background: linear-gradient(135deg, rgba(0,0,0,0.1) 0%, transparent 100%);
    border-radius: 12px;
}}
.ability-title {{
    color: var(--accent);
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.ability-row {{
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 0.75rem;
}}
@media (max-width: 768px) {{
    .ability-row {{
        grid-template-columns: repeat(3, 1fr);
    }}
}}
.ability-card {{
    position: relative;
    padding: 1rem 0.5rem;
}}
.ability-card .stat-value {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}}
.ability-card .stat-value i {{
    font-size: 1rem;
    opacity: 0.8;
}}
.stat-range {{
    color: var(--text-soft);
    font-size: 0.7rem;
    margin-top: 0.25rem;
}}

/* ---------------------------------------------------------------------------
   STORY SECTION - Character Backstories
   --------------------------------------------------------------------------- */
.story-section {{
    margin: 1.5rem 0;
    padding: 1rem;
    background: linear-gradient(135deg, rgba(0,0,0,0.1) 0%, transparent 100%);
    border-radius: 12px;
}}
.story-title {{
    color: var(--accent-strong);
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}}
.story-title::before {{
    content: '📖';
    font-size: 1rem;
}}
.story-card {{
    background: linear-gradient(135deg, var(--bg-soft) 0%, var(--bg-elevated) 100%);
    border: 1px solid var(--border-subtle);
    border-left: 4px solid var(--accent);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease;
}}
.story-card:hover {{
    border-color: var(--accent);
    transform: translateX(4px);
}}
.story-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}}
.story-name {{
    color: var(--accent-strong);
    font-size: 1.1rem;
    font-weight: 700;
}}
.story-class {{
    color: var(--text-soft);
    font-size: 0.85rem;
    background: var(--bg);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
}}
.story-text {{
    color: var(--text-main);
    font-style: italic;
    line-height: 1.7;
    margin: 0;
}}
.no-stories {{
    color: var(--text-soft);
    font-style: italic;
    padding: 1rem;
    background: var(--bg-soft);
    border-radius: 8px;
    text-align: center;
}}

/* ---------------------------------------------------------------------------
   SPOTLIGHT ABILITIES (mini display)
   --------------------------------------------------------------------------- */
.spotlight-abilities {{
    color: var(--text-soft);
    font-size: 0.75rem;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-subtle);
    font-family: var(--font-mono, monospace);
    letter-spacing: 0.02em;
}}

/* ---------------------------------------------------------------------------
   RESPONSIVE - Tavern on Small Devices
   --------------------------------------------------------------------------- */
@media (max-width: 768px) {{
    .layout-grid {{ grid-template-columns: 1fr; }}
    .tabs {{ flex-direction: column; }}
    .tabs::before {{ display: none; }}
    .container {{ padding: 1rem; }}
    header h1 {{ font-size: 1.75rem; letter-spacing: 0.1em; }}
    .stat-value {{ font-size: 2rem; }}
}}
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
    output_file.write_text(html, encoding='utf-8')
    
    mode_str = " (dry-run)" if dry_run else ""
    print(f"✓ Report generated{mode_str}: {output_file}")
    print(f"  Pages: {len(pages)}")
    print(f"  Data points: {len(data_points)}")
    print(f"  LLM sections: {len(llm_content)}")
    
    return output_file
'''
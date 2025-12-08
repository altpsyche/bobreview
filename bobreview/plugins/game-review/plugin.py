"""
BobReview Game Review Plugin - Video Game Review System.

This plugin provides game review functionality for BobReview.
It provides:
- Game Review LLM Generator (review_text)
- JSON Config Parser (game.json)
- Themes (dark, light, high contrast)
- Video Game Review report system and templates

Other plugins can override any of these components.
For performance analysis, use the MayhemAutomation plugin.
"""

import json
import logging
from pathlib import Path
from ...plugins import BasePlugin

logger = logging.getLogger(__name__)


class GameReviewPlugin(BasePlugin):
    """
    BobReview Game Review Plugin.
    
    Provides the video game review system with LLM-powered
    review generation based on game.json configuration.
    """
    
    name = "game-review"
    version = "1.0.0"
    author = "BobReview Team"
    description = "Video Game Review: LLM-powered game reviews from JSON config"
    dependencies = []
    
    def __init__(self):
        super().__init__()
    
    def on_load(self, registry) -> None:
        """Register all components."""
        config = self.get_config()
        
        # Register LLM generators
        if config.get('register_generators', True):
            self._register_generators(registry)
        
        # Register data parsers (JSON config parser)
        if config.get('register_parsers', True):
            self._register_parsers(registry)
        
        # Register themes
        if config.get('register_themes', True):
            self._register_themes(registry)
        
        # Register report systems
        if config.get('register_report_systems', True):
            self._register_report_systems(registry)
        
        # Register templates
        if config.get('register_templates', True):
            self._register_templates(registry)
        
        logger.info(f"Loaded {self.name} - Video Game Review plugin")
    
    def _register_generators(self, registry) -> None:
        """Register game review LLM generators."""
        from .generators import generate_review_text
        
        generators = [
            ('review_text', generate_review_text),
        ]
        
        for gen_id, gen_func in generators:
            wrapper = self._create_generator_wrapper(gen_id, gen_func)
            registry.register_llm_generator(wrapper, plugin_name=self.name)
    
    def _create_generator_wrapper(self, name: str, func):
        """Create a wrapper class for registering functions."""
        class GeneratorWrapper:
            generator_name = name
            generate = staticmethod(func)
        return GeneratorWrapper
    
    def _register_parsers(self, registry) -> None:
        """Register JSON config parser for game.json files."""
        from .parsers import GameConfigParser
        
        class GameConfigParserWrapper:
            parser_name = "json_config"
            parser_class = GameConfigParser
        
        registry.register_data_parser(GameConfigParserWrapper, plugin_name=self.name)
    
    def _register_themes(self, registry) -> None:
        """Register built-in themes."""
        from ...core.themes import BUILTIN_THEMES
        
        for theme in BUILTIN_THEMES:
            registry.register_theme(theme, plugin_name=self.name)
    
    def _register_report_systems(self, registry) -> None:
        """Register built-in report systems."""
        report_systems_dir = Path(__file__).parent / 'report_systems'
        
        if report_systems_dir.exists():
            for json_file in report_systems_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        system_def = json.load(f)
                    
                    system_name = json_file.stem
                    registry.register_report_system(
                        name=system_name,
                        system_def=system_def,
                        plugin_name=self.name
                    )
                except Exception as e:
                    logger.error(f"Failed to load report system {json_file}: {e}")
    
    def _register_templates(self, registry) -> None:
        """Register built-in templates."""
        template_dir = Path(__file__).parent / 'templates'
        if template_dir.exists():
            registry.register_template_path(
                template_dir,
                plugin_name=self.name,
                priority=1000
            )
        
        # Register context builder for game_review
        self._register_context_builders(registry)
    
    def _register_context_builders(self, registry) -> None:
        """Register context builders for our report systems."""
        from .context import GameReviewContextBuilder
        
        registry.register_context_builder(
            report_system_id='game_review',
            builder=GameReviewContextBuilder,
            plugin_name=self.name
        )
    
    def on_unload(self) -> None:
        """Clean up when plugin is unloaded."""
        pass

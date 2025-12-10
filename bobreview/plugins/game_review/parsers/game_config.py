"""
Game Configuration Parser.

Parses game.json files for video game reviews.

Implements DataParserInterface from core.api.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from bobreview.core.api import DataParserInterface

if TYPE_CHECKING:
    from ...engine.schema import DataSourceConfig

logger = logging.getLogger(__name__)


class GameConfigParser(DataParserInterface):
    """
    Parser for game.json configuration files.
    
    Loads game review data from a JSON config file containing:
    - title, developer, publisher, genre
    - scores (gameplay, graphics, story, sound, value)
    - pros, cons
    - summary, verdict
    - cover_image, screenshots
    """
    
    def __init__(self, config: "DataSourceConfig"):
        """
        Initialize parser with configuration.
        
        Parameters:
            config: DataSourceConfig from report system JSON definition
        """
        super().__init__(config)
        # Extract config file name from config if available, otherwise default
        self.config_file = getattr(config, 'config_file', 'game.json')
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single game.json file.
        
        Implements DataParserInterface.parse_file().
        
        Parameters:
            file_path: Path to the game.json file
        
        Returns:
            Dictionary with game data, or None if parsing fails
        """
        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._validate_and_normalize(data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """
        Discover game.json files in a directory.
        
        Implements DataParserInterface.discover_files().
        
        Parameters:
            directory: Directory to scan
        
        Returns:
            List of game.json file paths
        """
        config_path = directory / self.config_file
        if config_path.exists():
            return [config_path]
        return []
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize game data."""
        # Support both old 'title' and new 'name' field
        name = data.get('name') or data.get('title', 'Unknown Game')
        
        # Support new simplified input fields
        game = {
            # Core fields (new API)
            'name': name,
            'my_review': data.get('my_review', ''),
            'what_i_liked': data.get('what_i_liked', []),
            'needs_improvement': data.get('needs_improvement', []),
            'my_score': data.get('my_score', 7),
            
            # Optional metadata
            'genre': data.get('genre', ''),
            'cover_image': data.get('cover_image', ''),
            'screenshots': data.get('screenshots', []),
            
            # Category scores (optional)
            'scores': self._normalize_scores(data.get('scores', {})),
            
            # Legacy fields for backward compat (mapped to new)
            'title': name,  # alias
            'developer': data.get('developer', ''),
            'publisher': data.get('publisher', ''),
            'release_date': data.get('release_date', ''),
            'platforms': data.get('platforms', []),
            'pros': data.get('what_i_liked', data.get('pros', [])),  # new -> old
            'cons': data.get('needs_improvement', data.get('cons', [])),  # new -> old
            'summary': data.get('my_review', data.get('summary', '')),  # new -> old
            'verdict': data.get('verdict', ''),
        }
        
        return game
    
    def _normalize_scores(self, scores: Dict[str, Any]) -> Dict[str, float]:
        """Normalize scores to 1-10 range."""
        default_scores = {
            'gameplay': 5.0,
            'graphics': 5.0,
            'story': 5.0,
            'sound': 5.0,
            'value': 5.0,
        }
        
        for key in default_scores:
            if key in scores:
                try:
                    value = float(scores[key])
                    default_scores[key] = max(1.0, min(10.0, value))
                except (ValueError, TypeError):
                    pass
        
        return default_scores
    
    def get_sample_count(self) -> int:
        """Return number of items (1 for a single game review)."""
        return 1
    
    def get_data_summary(self, data: Dict[str, Any]) -> str:
        """Return a summary of the parsed data."""
        scores = data.get('scores', {})
        overall = sum(scores.values()) / len(scores) if scores else 0
        return f"{data.get('title', 'Unknown')} ({data.get('genre', 'Unknown')}) - {overall:.1f}/10"

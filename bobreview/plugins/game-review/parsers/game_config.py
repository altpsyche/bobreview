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
    from ...report_systems.schema import DataSourceConfig

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
        # Ensure required fields
        game = {
            'title': data.get('title', 'Unknown Game'),
            'developer': data.get('developer', 'Unknown'),
            'publisher': data.get('publisher', ''),
            'release_date': data.get('release_date', ''),
            'platforms': data.get('platforms', []),
            'genre': data.get('genre', 'Unknown'),
            'cover_image': data.get('cover_image', ''),
            'screenshots': data.get('screenshots', []),
            'scores': self._normalize_scores(data.get('scores', {})),
            'pros': data.get('pros', []),
            'cons': data.get('cons', []),
            'summary': data.get('summary', ''),
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
    
    def _get_default_game(self) -> Dict[str, Any]:
        """Return default game data structure."""
        return {
            'title': 'Unknown Game',
            'developer': 'Unknown',
            'publisher': '',
            'release_date': '',
            'platforms': [],
            'genre': 'Unknown',
            'cover_image': '',
            'screenshots': [],
            'scores': {
                'gameplay': 5.0,
                'graphics': 5.0,
                'story': 5.0,
                'sound': 5.0,
                'value': 5.0,
            },
            'pros': [],
            'cons': [],
            'summary': '',
            'verdict': '',
        }
    
    def get_sample_count(self) -> int:
        """Return number of items (1 for a single game review)."""
        return 1
    
    def get_data_summary(self, data: Dict[str, Any]) -> str:
        """Return a summary of the parsed data."""
        scores = data.get('scores', {})
        overall = sum(scores.values()) / len(scores) if scores else 0
        return f"{data.get('title', 'Unknown')} ({data.get('genre', 'Unknown')}) - {overall:.1f}/10"

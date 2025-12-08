"""
Game review context builder for game-review plugin.

Adds game-specific template context: game data alias.
"""
from typing import Dict, List, Any
from pathlib import Path


class GameReviewContextBuilder:
    """
    Builds template context for game review reports.
    
    Adds:
    - game: Alias for stats/data (for {{ game.title }}, {{ game.scores }})
    """
    
    def build(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        system_def: Any,
        input_dir: Path = None
    ) -> Dict[str, Any]:
        """
        Build game review-specific template context.
        
        Args:
            data_points: List of data points
            stats: Game data (title, scores, etc.)
            config: Report configuration
            system_def: Report system definition
            input_dir: Input directory
            
        Returns:
            Dict of additional context to merge into base context
        """
        return {
            'game': stats,  # Alias for {{ game.title }}, {{ game.scores }}
        }

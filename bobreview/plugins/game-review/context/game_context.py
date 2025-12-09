"""
Game review context builder for game-review plugin.

Adds game-specific template context: game data alias.

Implements ContextBuilderInterface from core.api.
"""
from typing import Dict, List, Any, TYPE_CHECKING
from pathlib import Path

from bobreview.core.api import ContextBuilderInterface

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig


class GameReviewContextBuilder(ContextBuilderInterface):
    """
    Builds template context for game review reports.
    
    Adds:
    - game: Alias for stats/data (for {{ game.title }}, {{ game.scores }})
    """
    
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build template context from data and statistics.
        
        Implements ContextBuilderInterface.build_context().
        
        Parameters:
            data_points: List of parsed data points
            stats: Statistical analysis results (for game reviews, this IS the game data)
            config: ReportConfig with settings
            base_context: Base context already prepared by framework
        
        Returns:
            Enriched context dictionary. Should merge with base_context.
        """
        # For game reviews, stats contains the game data from game.json
        return {
            **base_context,
            'game': stats,  # Alias for {{ game.title }}, {{ game.scores }}
        }


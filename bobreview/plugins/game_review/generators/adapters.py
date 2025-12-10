"""
LLM Generator Adapters for game_review plugin.

These adapter classes wrap the generator functions to implement LLMGeneratorInterface
from core.api, making them compatible with the core API.
"""

from typing import Dict, List, Any, TYPE_CHECKING

from bobreview.core.api import LLMGeneratorInterface

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

from .review_text import (
    generate_full_review,
    generate_target_audience,
    generate_similar_games,
    generate_expanded_pros,
    generate_expanded_cons,
    generate_verdict
)


class FullReviewGenerator(LLMGeneratorInterface):
    """Adapter for full review generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate expanded review text."""
        images_dir = context.get('images_dir_rel', '') if isinstance(context, dict) else ''
        return generate_full_review(data_points, stats, config, images_dir)


class TargetAudienceGenerator(LLMGeneratorInterface):
    """Adapter for target audience generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate 'Perfect for...' section."""
        images_dir = context.get('images_dir_rel', '') if isinstance(context, dict) else ''
        return generate_target_audience(data_points, stats, config, images_dir)


class SimilarGamesGenerator(LLMGeneratorInterface):
    """Adapter for similar games recommendations generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate game recommendations."""
        images_dir = context.get('images_dir_rel', '') if isinstance(context, dict) else ''
        return generate_similar_games(data_points, stats, config, images_dir)


class ExpandedProsGenerator(LLMGeneratorInterface):
    """Adapter for expanded pros generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate expanded pros list."""
        images_dir = context.get('images_dir_rel', '') if isinstance(context, dict) else ''
        return generate_expanded_pros(data_points, stats, config, images_dir)


class ExpandedConsGenerator(LLMGeneratorInterface):
    """Adapter for expanded cons generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate expanded cons list."""
        images_dir = context.get('images_dir_rel', '') if isinstance(context, dict) else ''
        return generate_expanded_cons(data_points, stats, config, images_dir)


class VerdictGenerator(LLMGeneratorInterface):
    """Adapter for verdict generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate final verdict."""
        images_dir = context.get('images_dir_rel', '') if isinstance(context, dict) else ''
        return generate_verdict(data_points, stats, config, images_dir)


# Backward compatibility alias
ReviewTextGenerator = FullReviewGenerator

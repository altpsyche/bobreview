"""
LLM Generator Adapters for game-review plugin.

These adapter classes wrap the generator functions to implement LLMGeneratorInterface
from core.api, making them compatible with the core API.
"""

from typing import Dict, List, Any, TYPE_CHECKING

from ...core.api import LLMGeneratorInterface

if TYPE_CHECKING:
    from ...core.config import ReportConfig

from .review_text import generate_review_text


class ReviewTextGenerator(LLMGeneratorInterface):
    """Adapter for review text generator."""
    
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: "ReportConfig",
        context: Dict[str, Any]
    ) -> str:
        """Generate review text."""
        return generate_review_text(data_points, stats, config, context.get('images_dir_rel', ''))


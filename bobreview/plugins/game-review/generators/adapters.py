"""
LLM Generator Adapters for game-review plugin.

These adapter classes wrap the generator functions to implement LLMGeneratorInterface
from core.api, making them compatible with the core API.
"""

from typing import Dict, List, Any, TYPE_CHECKING

from bobreview.core.api import LLMGeneratorInterface

if TYPE_CHECKING:
    from bobreview.core.config import ReportConfig

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
        # Ensure context is a dict and extract images_dir_rel safely
        if isinstance(context, dict):
            images_dir = context.get('images_dir_rel', '')
        else:
            images_dir = str(context) if context else ''
        return generate_review_text(data_points, stats, config, images_dir)


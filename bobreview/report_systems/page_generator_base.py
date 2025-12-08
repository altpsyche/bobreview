"""
Page generator base class for report page rendering.

Page generators are responsible for rendering HTML pages using templates
and data.

This class extends PageGeneratorInterface from core.api.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from .schema import PageConfig
from ..core.api import PageGeneratorInterface

if TYPE_CHECKING:
    from ..core.config import ReportConfig


class PageGeneratorTemplate(PageGeneratorInterface):
    """Template-based page generator."""
    
    def __init__(self, config: PageConfig):
        """
        Initialize the page generator with configuration.
        
        Parameters:
            config: Page configuration from JSON
        """
        self.config = config
    
    def render(
        self,
        stats: Dict[str, Any],
        llm_content: Dict[str, Any],
        config: 'ReportConfig',
        context: Dict[str, Any]
    ) -> str:
        """
        Render HTML page from template and data.
        
        Parameters:
            stats: Statistical analysis results
            llm_content: Generated LLM content (dict of generator_id -> content)
            config: ReportConfig with settings
            context: Additional context (data_points, images, charts, etc.)
        
        Returns:
            Rendered HTML string
        """
        # Extract common context items for backward compatibility
        data_points = context.get('data_points')
        images_dir_rel = context.get('images_dir_rel')
        image_data_uris = context.get('image_data_uris')
        
        # This is a simplified version
        # In practice, this would use the template system to render the page
        return f"<html><body>Page: {self.config.id}</body></html>"



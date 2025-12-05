"""
Abstract base class for page generators.

Page generators are responsible for rendering HTML pages using templates
and data.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from .schema import PageConfig


class PageGeneratorTemplate:
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
        report_config,
        data_points: Optional[List[Dict[str, Any]]] = None,
        images_dir_rel: Optional[str] = None,
        image_data_uris: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Render HTML page from template and data.
        
        Parameters:
            stats: Statistical analysis results
            llm_content: Generated LLM content
            report_config: Report configuration
            data_points: Optional list of data points
            images_dir_rel: Optional relative path to images
            image_data_uris: Optional base64 encoded images
        
        Returns:
            Rendered HTML string
        """
        # This is a simplified version
        # In practice, this would use the template system to render the page
        return f"<html><body>Page: {self.config.id}</body></html>"


class PageGeneratorAdapter:
    """
    Adapter for using Python-based page generators with JSON configuration.
    
    This allows existing Python page generator functions to work with the new
    JSON-based system.
    """
    
    def __init__(self, generator_func, config: PageConfig):
        """
        Initialize adapter with Python generator function.
        
        Parameters:
            generator_func: Python function that generates HTML page
            config: Page configuration
        """
        self.generator_func = generator_func
        self.config = config
    
    def render(
        self,
        stats: Dict[str, Any],
        llm_content: Dict[str, Any],
        report_config,
        data_points: Optional[List[Dict[str, Any]]] = None,
        images_dir_rel: Optional[str] = None,
        image_data_uris: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Call the Python page generator function.
        
        Parameters:
            stats: Statistical analysis results
            llm_content: Generated LLM content
            report_config: Report configuration
            data_points: Optional list of data points
            images_dir_rel: Optional relative path to images
            image_data_uris: Optional base64 encoded images
        
        Returns:
            Rendered HTML string
        """
        # Build kwargs based on what the generator needs
        kwargs = {
            'stats': stats,
            'config': report_config
        }
        
        # Add data points if needed
        if self.config.data_requirements.data_points and data_points is not None:
            kwargs['data_points'] = data_points
        
        # Add images if needed
        if self.config.data_requirements.images:
            if images_dir_rel is not None:
                kwargs['images_dir_rel'] = images_dir_rel
            if image_data_uris is not None:
                kwargs['image_data_uris'] = image_data_uris
        
        # Add LLM content
        # Different pages expect different kwargs for LLM content
        # This will be handled by the executor based on page ID
        
        return self.generator_func(**kwargs)


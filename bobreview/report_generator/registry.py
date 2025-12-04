"""
Page registry system for modular report generation.

This module provides a registry pattern that allows pages to self-register,
making it easy to add or remove report pages without modifying core orchestration code.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional


@dataclass
class PageDefinition:
    """
    Defines a report page with all metadata needed for generation and navigation.
    
    Attributes:
        id: Unique identifier (e.g., 'metrics', 'zones')
        filename: Output filename (e.g., 'metrics.html')
        nav_label: Label shown in navigation (e.g., 'Metrics')
        nav_order: Sort order in navigation (lower = earlier)
        llm_section: Name of LLM content section this page needs
        page_generator: Function that generates the page HTML
        requires_images: Whether this page needs image data
        requires_data_points: Whether this page needs raw data points
    """
    id: str
    filename: str
    nav_label: str
    nav_order: int
    llm_section: str
    page_generator: Callable[..., str]
    requires_images: bool = False
    requires_data_points: bool = False


# Global registry of all pages
_PAGE_REGISTRY: Dict[str, PageDefinition] = {}

# Current disabled pages (set at report generation time)
_CURRENT_DISABLED_IDS: List[str] = []


def register_page(page: PageDefinition) -> None:
    """
    Register a page definition in the global registry.
    
    Parameters:
        page: PageDefinition instance to register
    
    Raises:
        ValueError: If a page with the same ID is already registered
    """
    if page.id in _PAGE_REGISTRY:
        raise ValueError(f"Page '{page.id}' is already registered")
    _PAGE_REGISTRY[page.id] = page


def set_disabled_pages(disabled_ids: List[str]) -> None:
    """
    Set the currently disabled page IDs for this report generation.
    
    Parameters:
        disabled_ids: List of page IDs to disable
    """
    global _CURRENT_DISABLED_IDS
    _CURRENT_DISABLED_IDS = list(disabled_ids) if disabled_ids else []


def get_disabled_pages() -> List[str]:
    """Get the currently disabled page IDs."""
    return _CURRENT_DISABLED_IDS.copy()


def get_all_pages() -> Dict[str, PageDefinition]:
    """Get the full page registry dictionary."""
    return _PAGE_REGISTRY.copy()


def get_enabled_pages(disabled_ids: Optional[List[str]] = None) -> List[PageDefinition]:
    """
    Get all enabled pages sorted by nav_order.
    
    Parameters:
        disabled_ids: List of page IDs to exclude (uses _CURRENT_DISABLED_IDS if None)
    
    Returns:
        List of PageDefinition objects sorted by nav_order
    """
    disabled = set(disabled_ids if disabled_ids is not None else _CURRENT_DISABLED_IDS)
    return sorted(
        [p for p in _PAGE_REGISTRY.values() if p.id not in disabled],
        key=lambda p: p.nav_order
    )


def get_nav_items(active_page: str, disabled_ids: Optional[List[str]] = None) -> List[tuple]:
    """
    Generate navigation items from enabled pages.
    
    Parameters:
        active_page: Filename of the currently active page
        disabled_ids: List of page IDs to exclude (uses _CURRENT_DISABLED_IDS if None)
    
    Returns:
        List of (label, url, is_active) tuples for navigation
    """
    return [
        (p.nav_label, p.filename, p.filename == active_page)
        for p in get_enabled_pages(disabled_ids)
    ]


def clear_registry() -> None:
    """Clear all registered pages. Mainly used for testing."""
    global _CURRENT_DISABLED_IDS
    _PAGE_REGISTRY.clear()
    _CURRENT_DISABLED_IDS = []

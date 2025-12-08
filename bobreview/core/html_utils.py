"""
Core HTML utilities for BobReview.

This module provides HTML sanitization and formatting utilities that plugins can use.
Moved from pages.base to core to remove core dependency on framework modules.
"""

from html import escape
from pathlib import Path

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


def sanitize_llm_html(content: str) -> str:
    """
    Sanitize LLM-generated HTML to prevent XSS while preserving safe formatting tags.
    
    Uses the bleach library (whitelist-based approach) when available, otherwise
    returns escaped HTML as a fallback.
    
    Allowed tags: p, strong, em, b, i, u, ul, ol, li, br, span, div, h1-h6, a, code, pre
    Allowed attributes: class (on span/div), href (on a)
    
    Parameters:
        content: HTML content from LLM
    
    Returns:
        Sanitized HTML string
    
    Example:
        safe_html = sanitize_llm_html(llm_response)
    """
    if not content:
        return ""
    
    if not BLEACH_AVAILABLE:
        # Fallback: escape all HTML if bleach is not available
        return escape(content)
    
    # Whitelist of safe tags
    allowed_tags = [
        'p', 'strong', 'em', 'b', 'i', 'u', 
        'ul', 'ol', 'li', 'br', 'span', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'code', 'pre', 'blockquote'
    ]
    
    # Whitelist of safe attributes
    allowed_attributes = {
        'span': ['class'],
        'div': ['class'],
        'a': ['href'],
        'code': ['class']
    }
    
    # Whitelist of safe protocols for links
    allowed_protocols = ['http', 'https', 'mailto']
    
    # Sanitize using bleach
    sanitized = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True  # Strip disallowed tags instead of escaping them
    )
    
    return sanitized.strip()


def get_shared_css() -> str:
    """
    Get shared CSS for reports.
    
    Plugins can use this to get consistent styling.
    Returns CSS string with theme variables and base styles.
    
    This function reads the CSS content from the styles.css file located in the
    pages directory. The CSS is the single source of truth for all report styling.
    
    Returns:
        str: Complete CSS content for embedding in HTML
    """
    # CSS is in pages directory, not core directory
    # We need to find it relative to the package root
    from .. import pages
    css_path = Path(pages.__file__).parent / "styles.css"
    return css_path.read_text(encoding='utf-8')


def get_trend_icon(trend: str) -> str:
    """
    Get trend icon HTML/emoji.
    
    Parameters:
        trend: 'improving', 'stable', or 'degrading'
    
    Returns:
        FontAwesome icon name without 'fa-' prefix
    
    Example:
        icon = get_trend_icon('improving')  # Returns: "arrow-down"
    """
    if trend == 'improving':
        return 'arrow-down'
    elif trend == 'degrading':
        return 'arrow-up'
    else:  # stable
        return 'arrow-right'


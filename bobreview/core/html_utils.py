"""
Core HTML utilities for BobReview.

This module provides HTML sanitization and formatting utilities that plugins can use.
Moved from pages.base to core to remove core dependency on framework modules.
"""

from pathlib import Path

import bleach
import markdown


def markdown_to_html(content: str) -> str:
    """
    Convert markdown content to HTML.
    
    Parameters:
        content: Markdown content string
    
    Returns:
        HTML string
    """
    if not content:
        return ""
    
    # Convert markdown to HTML
    # Extensions provide better markdown support (tables, fenced code, better lists)
    # HTML will be sanitized by sanitize_llm_html after conversion
    html = markdown.markdown(
        content,
        extensions=['extra', 'nl2br', 'sane_lists'],  # Support tables, fenced code, better lists
    )
    
    return html


def sanitize_llm_html(content: str) -> str:
    """
    Sanitize LLM-generated markdown content to prevent XSS while preserving safe formatting.
    
    Converts markdown to HTML, then sanitizes the HTML using bleach.
    
    Allowed tags: p, strong, em, b, i, u, ul, ol, li, br, span, div, h1-h6, a, code, pre, blockquote
    Allowed attributes: class (on span/div), href (on a)
    
    Parameters:
        content: Markdown content from LLM
    
    Returns:
        Sanitized HTML string
    
    Example:
        safe_html = sanitize_llm_html(llm_response)
    """
    if not content:
        return ""
    
    # Convert markdown to HTML first
    html_content = markdown_to_html(content)
    
    # Whitelist of safe tags
    allowed_tags = [
        'p', 'strong', 'em', 'b', 'i', 'u', 
        'ul', 'ol', 'li', 'br', 'span', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'code', 'pre', 'blockquote',
        # Common markdown outputs (safe, structural)
        'hr',
        'table', 'thead', 'tbody', 'tr', 'th', 'td'
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
        html_content,
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
    core/static directory. The CSS is the single source of truth for all report styling.
    
    Returns:
        str: Complete CSS content for embedding in HTML
    """
    # CSS is in core/static directory
    css_path = Path(__file__).parent / "static" / "styles.css"
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


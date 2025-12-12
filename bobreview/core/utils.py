#!/usr/bin/env python3
"""
Utility functions for BobReview including logging and formatting.
"""

import sys
import base64
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import ReportConfig

# Try to import rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.theme import Theme
    RICH_AVAILABLE = True
    
    # Custom theme for consistent styling
    _theme = Theme({
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "debug": "dim blue",
    })
    console = Console(theme=_theme)
    err_console = Console(theme=_theme, stderr=True)
except ImportError:
    RICH_AVAILABLE = False
    console = None
    err_console = None


def log_info(message: str, config: "Optional[ReportConfig]" = None):
    """Log an informational message to stdout."""
    if config and config.execution.quiet:
        return
    if RICH_AVAILABLE:
        console.print(f"[info]●[/info] {message}")
    else:
        print(f"● {message}")


def log_success(message: str, config: "Optional[ReportConfig]" = None):
    """Log a success message to stdout."""
    if config and config.execution.quiet:
        return
    if RICH_AVAILABLE:
        console.print(f"[success]✓[/success] {message}")
    else:
        print(f"✓ {message}")


def log_warning(message: str, config: "Optional[ReportConfig]" = None):
    """Log a warning message to stdout."""
    if config and config.execution.quiet:
        return
    if RICH_AVAILABLE:
        console.print(f"[warning]⚠[/warning] {message}")
    else:
        print(f"⚠ {message}")


def log_error(message: str):
    """Log an error message to stderr."""
    if RICH_AVAILABLE:
        err_console.print(f"[error]✗[/error] {message}")
    else:
        print(f"✗ {message}", file=sys.stderr)


def log_verbose(message: str, config: "Optional[ReportConfig]" = None):
    """Log a debug message when verbose mode is enabled."""
    if config and config.execution.verbose and not config.execution.quiet:
        if RICH_AVAILABLE:
            console.print(f"[debug]• {message}[/debug]")
        else:
            print(f"• {message}")


def format_number(n, decimals=1):
    """
    Return the number formatted with thousands separators and a fixed number of decimal places.
    
    If ``n`` is ``None`` or cannot be formatted as a number, returns ``"N/A"``.
    
    Parameters:
        n (int | float | None): The numeric value to format.
        decimals (int): Number of digits to show after the decimal point. If set to 0, the value is converted to an integer and the fractional part is discarded.
    
    Returns:
        formatted (str): The number as a string with comma separators for thousands and the requested decimal precision,
            or ``"N/A"`` when the value is missing or invalid.
    """
    if n is None:
        return 'N/A'
    try:
        if decimals == 0:
            return f"{int(n):,}"
        else:
            return f"{n:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(n) if n else 'N/A'


def image_to_base64(image_path: Path) -> Optional[str]:
    """
    Convert an image file to a base64-encoded data URI.
    
    Parameters:
        image_path (Path): Path to the image file.
    
    Returns:
        str | None: A data URI string (e.g., "data:image/png;base64,iVBORw0KG...") 
                    or None if the file cannot be read.
    """
    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            b64_data = base64.b64encode(img_data).decode('utf-8')
            
            # Determine MIME type from extension
            ext = image_path.suffix.lower()
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml'
            }.get(ext, 'image/png')  # Default to PNG
            
            return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        log_error(f"Failed to encode image {image_path}: {e}")
        return None


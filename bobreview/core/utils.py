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

# Try to import optional dependencies
try:
    from colorama import init as colorama_init, Fore, Style
    COLORAMA_AVAILABLE = True
    colorama_init(autoreset=True)
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback: create dummy color classes
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''


def log_info(message: str, config: "Optional[ReportConfig]" = None):
    """
    Log an informational message to standard output unless quiet mode is enabled.
    
    If color support is available, the message is prefixed with a cyan "[INFO]" tag; otherwise a plain "[INFO]" tag is used. If a `config` is provided and `config.quiet` is True, the message is suppressed.
    
    Parameters:
        message (str): The message to log.
        config (ReportConfig, optional): Configuration that may suppress output when `config.quiet` is True.
    """
    if config and config.quiet:
        return
    if COLORAMA_AVAILABLE:
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")
    else:
        print(f"[INFO] {message}")


def log_success(message: str, config: "Optional[ReportConfig]" = None):
    """
    Log a success message to stdout, prefixed with a check mark.
    
    If a ReportConfig with `quiet=True` is provided, the message is suppressed.
    When terminal coloring is available, the check mark is rendered in green.
    
    Parameters:
        message (str): The message to print.
        config (ReportConfig, optional): Configuration used to determine whether output is suppressed.
    """
    if config and config.quiet:
        return
    if COLORAMA_AVAILABLE:
        print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {message}")
    else:
        print(f"[OK] {message}")


def log_warning(message: str, config: "Optional[ReportConfig]" = None):
    """
    Print a warning message to stdout unless suppressed by configuration.
    
    Parameters:
        message (str): The warning text to display.
        config (ReportConfig, optional): If provided and `config.quiet` is True, the warning is not printed.
    """
    if config and config.quiet:
        return
    if COLORAMA_AVAILABLE:
        print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")
    else:
        print(f"[WARNING] {message}")


def log_error(message: str):
    """
    Write an error message to standard error with an "[ERROR]" prefix; when the terminal supports color, the prefix is shown in red.
    
    Parameters:
        message (str): The error text to display.
    """
    if COLORAMA_AVAILABLE:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}", file=sys.stderr)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)


def log_verbose(message: str, config: "Optional[ReportConfig]" = None):
    """
    Log a debug message when verbose mode is enabled and not suppressed by quiet mode.
    
    Prints the provided message to stdout only if `config` is provided, `config.verbose` is True, and `config.quiet` is False. When colorama is available, the log is prefixed with a colored `[DEBUG]` marker.
    
    Parameters:
        message (str): The message to log.
        config (ReportConfig, optional): Configuration controlling verbosity and quiet suppression. If omitted or falsy, no output is produced.
    """
    if config and config.verbose and not config.quiet:
        if COLORAMA_AVAILABLE:
            print(f"{Fore.BLUE}[DEBUG]{Style.RESET_ALL} {message}")
        else:
            print(f"[DEBUG] {message}")


def format_number(n, decimals=1):
    """
    Return the number formatted with thousands separators and a fixed number of decimal places.
    
    Parameters:
        n (int | float): The numeric value to format.
        decimals (int): Number of digits to show after the decimal point. If set to 0, the value is converted to an integer and the fractional part is discarded.
    
    Returns:
        formatted (str): The number as a string with comma separators for thousands and the requested decimal precision.
    """
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


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


#!/usr/bin/env python3
"""
BobReview - Report Generation Framework

A comprehensive tool for generating detailed reports with LLM-powered insights.

v1.0.9: Flet GUI
"""

__version__ = "1.0.9"
__author__ = "Siva Vadlamani"
__description__ = "Report generation with plugins"

# Import from new package structure
from .core import Config
from .cli import main as cli_main
from .gui import main as gui_main

__all__ = [
    '__author__',
    '__description__',
    '__version__',
    'Config',
    'cli_main',
    'gui_main',
]


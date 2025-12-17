#!/usr/bin/env python3
"""
BobReview - Report Generation Framework

A comprehensive tool for generating detailed reports with LLM-powered insights.

v1.0.8: Standardized APIs & DataFrame Support
"""

__version__ = "1.0.8"
__author__ = "Siva Vadlamani"
__description__ = "Report generation framework with plugin support"

# Import from new package structure
from .core import Config
from .cli import main as cli_main

__all__ = [
    '__author__',
    '__description__',
    '__version__',
    'Config',
    'cli_main',
]


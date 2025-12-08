#!/usr/bin/env python3
"""
BobReview - Performance Analysis and Review Tool

A comprehensive tool for analyzing game performance captures and generating
detailed reports with LLM-powered insights.

v1.0.7: Plugin System
"""

__version__ = "1.0.7"
__author__ = "BobReview Contributors"
__description__ = "Performance analysis and review tool for game development"

# Import from new package structure
from .core import ReportConfig, analyze_data
from .cli import main as cli_main

__all__ = [
    '__author__',
    '__description__',
    '__version__',
    'ReportConfig',
    'analyze_data',
    'cli_main',
]

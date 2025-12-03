#!/usr/bin/env python3
"""
BobReview - Performance Analysis and Review Tool

A comprehensive tool for analyzing game performance captures and generating
detailed reports with LLM-powered insights.
"""

__version__ = "1.0.1"
__author__ = "BobReview Contributors"
__description__ = "Performance analysis and review tool for game development"

# Import main components for easier access
from .config import ReportConfig
from .data_parser import parse_filename, DataPoint
from .analysis import analyze_data
from .report_generator import generate_html_report
from .cli import main as cli_main

# Legacy alias for backward compatibility
generate_html = generate_html_report

__all__ = [
    '__author__',
    '__description__',
    '__version__',
    'DataPoint',
    'ReportConfig',
    'analyze_data',
    'cli_main',
    'generate_html',  # Legacy name
    'generate_html_report',
    'parse_filename',
]


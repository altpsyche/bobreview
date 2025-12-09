#!/usr/bin/env python3
"""
Setup script for BobReview - Performance Analysis and Review Tool

This file reads dependencies from requirements.txt to maintain a single source of truth.
All runtime dependencies should be defined in requirements.txt.
"""

from setuptools import setup, find_packages
from pathlib import Path


def read_requirements():
    """
    Read and parse requirements.txt.
    
    Returns a list of requirement strings, excluding comments and empty lines.
    This ensures requirements.txt is the single source of truth for dependencies.
    """
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        import warnings
        warnings.warn("requirements.txt not found; no dependencies will be installed", stacklevel=2)
        return []
    
    requirements = []
    for line in requirements_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Remove inline comments
        if "#" in line:
            line = line.split("#")[0].strip()
        # Skip empty lines and comments
        if line:
            requirements.append(line)
    
    return requirements


# Read requirements from requirements.txt (single source of truth)
install_requires = read_requirements()

# Note: Most configuration is in pyproject.toml (modern standard)
# This setup.py exists to:
# 1. Read dependencies from requirements.txt
# 2. Provide backward compatibility with older tools
# Package configuration is handled in pyproject.toml
setup(
    install_requires=install_requires,
)


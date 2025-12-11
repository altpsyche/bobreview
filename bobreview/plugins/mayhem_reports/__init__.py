"""
mayhem-reports Plugin for BobReview.

Provides performance analysis for game development:
- PNG filename parser for performance data
- Performance-focused context builder
- Chart generators (histogram, timeline, scatter)
- Performance analyzer function
- Built-in themes
"""

from .plugin import MayhemReportsPlugin

__all__ = ['MayhemReportsPlugin']

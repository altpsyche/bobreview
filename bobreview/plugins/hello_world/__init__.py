"""
Hello World Plugin for BobReview.

This is a complete example plugin that demonstrates all BobReview core
extension points:
- Data Parser: CSV file parsing
- Context Builder: Custom template context
- Chart Generator: Chart.js configurations
- Theme: Custom color scheme
- Report System: JSON-based report definition

Use this as a reference for building your own plugins.
"""

from .plugin import HelloWorldPlugin

__all__ = ['HelloWorldPlugin']

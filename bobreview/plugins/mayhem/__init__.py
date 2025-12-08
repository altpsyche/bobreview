"""MayhemAutomation Plugin - Full-featured BobReview automation."""
from .plugin import CorePlugin as MayhemPlugin

# Alias for compatibility
CorePlugin = MayhemPlugin

__all__ = ['MayhemPlugin', 'CorePlugin']

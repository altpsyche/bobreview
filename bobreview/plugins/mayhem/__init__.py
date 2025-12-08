"""MayhemAutomation Plugin - Performance analysis for BobReview."""
from .plugin import MayhemAutomationPlugin

# Aliases for compatibility
MayhemPlugin = MayhemAutomationPlugin
CorePlugin = MayhemAutomationPlugin  # Legacy alias

__all__ = ['MayhemAutomationPlugin', 'MayhemPlugin', 'CorePlugin']

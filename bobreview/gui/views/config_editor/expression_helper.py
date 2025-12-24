"""
Expression Helper - Generates Jinja2 template expressions.

Creates data expression options based on available columns.
"""

from typing import List, Tuple


class ExpressionHelper:
    """Generates Jinja2 template expressions for data fields."""
    
    def __init__(self, columns: List[str] = None):
        self.columns = columns or []
    
    def set_columns(self, columns: List[str]):
        """Update available columns."""
        self.columns = columns
    
    def get_expressions(self) -> List[Tuple[str, str]]:
        """
        Get list of (expression, label) tuples for dropdown.
        """
        expressions = [
            ("{{ data_points | length }}", "Total Count"),
        ]
        
        # Add expressions for each column (limit to 10)
        for col in self.columns[:10]:
            expressions.extend([
                (f"{{{{ stats.{col}.max }}}}", f"Max {col.title()}"),
                (f"{{{{ stats.{col}.min }}}}", f"Min {col.title()}"),
                (f"{{{{ stats.{col}.mean | round(1) }}}}", f"Avg {col.title()}"),
                (f"{{{{ data_points[0].{col} }}}}", f"First {col.title()}"),
            ])
        
        # Add config expressions
        expressions.append(("{{ config.adventure_theme }}", "Config Theme"))
        
        return expressions
    
    def get_common_expressions(self) -> List[Tuple[str, str]]:
        """Get common expressions without column-specific ones."""
        return [
            ("{{ data_points | length }}", "Total Count"),
            ("{{ config.adventure_theme }}", "Config Theme"),
            ("{{ config.name }}", "Report Name"),
        ]

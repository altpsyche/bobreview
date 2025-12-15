"""
Abstract base class for LLM generators.

LLM generators are responsible for creating AI-generated content
using configured prompts and templates.

Note: LLMGeneratorTemplate is a framework utility class for template-based
generation from JSON config. It is not an interface implementation.
Plugins should implement LLMGeneratorInterface from core.api directly.
"""

from typing import Dict, List, Any, TYPE_CHECKING
from .schema import LLMGeneratorConfig, PromptCategoryConfig

if TYPE_CHECKING:
    from ..core.config import Config


class LLMGeneratorTemplate:
    """Template-based LLM content generator."""
    
    def __init__(self, config: LLMGeneratorConfig):
        """
        Initialize the LLM generator with configuration.
        
        Parameters:
            config: LLM generator configuration from JSON
        """
        self.config = config
    
    def build_prompt(
        self,
        stats: Dict[str, Any],
        data_points: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """
        Build prompt from template with variable substitution.
        
        Parameters:
            stats: Statistical analysis results
            data_points: List of parsed data points
            context: Additional context (config, thresholds, etc.)
        
        Returns:
            Formatted prompt string
        """
        prompt = self.config.prompt_template
        
        # Build categories section
        categories_text = self._build_categories()
        
        # Prepare substitution context
        substitution_context = {
            'stats': stats,
            'context': context,
            'categories': categories_text
        }
        
        # Perform variable substitution
        prompt = self._substitute_variables(prompt, substitution_context)
        
        return prompt
    
    def _build_categories(self) -> str:
        """Build the categories section of the prompt."""
        if not self.config.categories:
            return ""
        
        # Sort categories by priority
        sorted_categories = sorted(self.config.categories, key=lambda c: c.priority)
        
        lines = []
        for i, category in enumerate(sorted_categories, 1):
            lines.append(f"{i}. {category.title} - {category.focus}")
        
        return '\n'.join(lines)
    
    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Substitute variables in template.
        
        Supports:
        - {stats.draws.mean} - nested dictionary access
        - {context.location} - nested dictionary access
        - {categories} - direct substitution
        """
        import re
        
        # Find all {var.path} patterns
        pattern = r'\{([^}]+)\}'
        
        def replace_var(match):
            var_path = match.group(1)
            
            # Direct substitution (no dots)
            if '.' not in var_path:
                return str(context.get(var_path, match.group(0)))
            
            # Nested path like stats.draws.mean
            parts = var_path.split('.')
            value = context
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    # Variable not found, keep original
                    return match.group(0)
            
            # Format numbers nicely
            if isinstance(value, float):
                return f"{value:.1f}"
            return str(value)
        
        return re.sub(pattern, replace_var, template)
    
    def select_data_samples(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Select data samples according to configured strategy.
        
        Parameters:
            data_points: All available data points
            stats: Statistical analysis results (for critical/high-load selection)
        
        Returns:
            Selected subset of data points
        """
        if not self.config.data_table:
            return data_points
        
        table_config = self.config.data_table
        strategy = table_config.sample_strategy
        
        if strategy == 'all':
            return data_points[:table_config.max_rows]
        
        if strategy == 'random':
            import random
            k = min(table_config.max_rows, len(data_points))
            return random.sample(data_points, k)
        
        if strategy == 'sequential':
            return data_points[:table_config.max_rows]
        
        if strategy == 'mixed' and table_config.samples:
            selected = []
            samples_config = table_config.samples
            
            # Add critical samples
            if 'critical' in samples_config and stats.get('critical'):
                critical_idx, critical_point = stats['critical']
                if 0 <= critical_idx < len(data_points):
                    selected.append(data_points[critical_idx])
            
            # Add high-load samples
            if 'high_load' in samples_config and stats.get('high_load'):
                count = samples_config['high_load']
                for idx, point in stats['high_load'][:count]:
                    if idx < len(data_points) and data_points[idx] not in selected:
                        selected.append(data_points[idx])
            
            # Add low-load samples
            if 'low_load' in samples_config and stats.get('low_load'):
                count = samples_config['low_load']
                for idx, point in stats['low_load'][:count]:
                    if idx < len(data_points) and data_points[idx] not in selected:
                        selected.append(data_points[idx])
            
            # Add random samples to fill remaining slots
            if 'random' in samples_config:
                count = samples_config['random']
                remaining = [p for p in data_points if p not in selected]
                if remaining:
                    import random
                    k = min(count, len(remaining))
                    selected.extend(random.sample(remaining, k))
            
            return selected[:table_config.max_rows]
        
        return data_points[:table_config.max_rows]
    
    def format_data_table(
        self,
        data_points: List[Dict[str, Any]]
    ) -> str:
        """
        Format data points as a text table for LLM consumption.
        
        Parameters:
            data_points: Data points to format
        
        Returns:
            Formatted table string
        """
        if not data_points or not self.config.data_table:
            return ""
        
        columns = self.config.data_table.columns
        
        # Build header
        header = " | ".join(columns)
        separator = "-|-".join(["-" * len(col) for col in columns])
        
        # Build rows
        rows = []
        for i, point in enumerate(data_points):
            row_values = []
            for col in columns:
                if col == 'index':
                    row_values.append(str(i))
                elif col in point:
                    value = point[col]
                    # Format numbers
                    if isinstance(value, float):
                        row_values.append(f"{value:.1f}")
                    elif isinstance(value, int):
                        row_values.append(str(value))
                    else:
                        row_values.append(str(value))
                else:
                    row_values.append("-")
            rows.append(" | ".join(row_values))
        
        return f"{header}\n{separator}\n" + "\n".join(rows)

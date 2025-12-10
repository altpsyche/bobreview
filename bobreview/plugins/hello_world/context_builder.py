"""
Context Builder for Hello World Plugin.

Implements ContextBuilderInterface to add custom data to template context.
"""

from typing import Dict, List, Any

from bobreview.core.api import ContextBuilderInterface


class HelloContextBuilder(ContextBuilderInterface):
    """
    Build template context for Hello World reports.
    
    Adds plugin-specific data like:
    - Sorted rankings
    - Score categories (excellent, good, needs improvement)
    - Trend indicators
    """
    
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build enriched context for template rendering.
        """
        context = dict(base_context)
        
        # Sort data by score (descending)
        ranked_data = sorted(data_points, key=lambda x: x.get('score', 0), reverse=True)
        context['ranked_data'] = ranked_data
        
        # Add rankings
        for i, item in enumerate(ranked_data, 1):
            item['rank'] = i
        
        # Categorize by score
        context['excellent'] = [d for d in data_points if d.get('score', 0) >= 90]
        context['good'] = [d for d in data_points if 70 <= d.get('score', 0) < 90]
        context['needs_improvement'] = [d for d in data_points if d.get('score', 0) < 70]
        
        # Calculate category counts
        context['category_counts'] = {
            'excellent': len(context['excellent']),
            'good': len(context['good']),
            'needs_improvement': len(context['needs_improvement']),
        }
        
        # Get top and bottom performers
        if ranked_data:
            context['top_performer'] = ranked_data[0]
            context['bottom_performer'] = ranked_data[-1]
        
        # Add score range
        scores = [d.get('score', 0) for d in data_points]
        if scores:
            context['score_range'] = {
                'min': min(scores),
                'max': max(scores),
                'spread': max(scores) - min(scores),
            }
        
        return context

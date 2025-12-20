"""
Component System for Property Controls.

This package provides the infrastructure for the Property Controls pattern,
where plugins register components with their schemas and core validates
YAML against those schemas.

Key exports:
    - PropTypes: Factory for creating property definitions
    - register_component: Decorator to register component classes
    - ComponentProcessor: Validates YAML against component schemas
    - ValidatedComponent: Result of processing a YAML component

Example plugin usage:
    from bobreview.core.components import register_component, PropTypes
    
    @register_component("chart")
    class ChartComponent:
        '''Renders data visualizations.'''
        
        props = {
            "id": PropTypes.string(required=True),
            "chart": PropTypes.choice(["bar", "line", "pie"], default="bar"),
            "title": PropTypes.string(default=""),
            "x": PropTypes.string(),
            "y": PropTypes.string(),
            "animated": PropTypes.boolean(default=True),
        }
        
        template = "components/chart.html.j2"

Example core usage:
    from bobreview.core.components import get_component_processor
    
    processor = get_component_processor()
    validated = processor.process({
        "type": "chart",
        "id": "my_chart",
        "chart": "bar",
        "title": "Sales"
    })
    # validated.props contains validated, typed values
"""

# PropTypes API
from .prop_types import (
    PropTypes,
    PropDef,
    PropType,
)

# Registry
from .registry import (
    register_component,
    get_component_registry,
    ComponentRegistry,
    ComponentDefinition,
)

# Processor
from .processor import (
    ComponentProcessor,
    ValidatedComponent,
    ComponentValidationError,
    get_component_processor,
)

# Renderer
from .renderer import (
    ComponentRenderer,
    RenderedComponent,
    get_component_renderer,
    reset_component_renderer,
)

# Note: Plugins register their own components - no built-ins in core

__all__ = [
    # PropTypes
    'PropTypes',
    'PropDef',
    'PropType',
    # Registry
    'register_component',
    'get_component_registry',
    'ComponentRegistry',
    'ComponentDefinition',
    # Processor
    'ComponentProcessor',
    'ValidatedComponent',
    'ComponentValidationError',
    'get_component_processor',
    # Renderer
    'ComponentRenderer',
    'RenderedComponent',
    'get_component_renderer',
    'reset_component_renderer',
]

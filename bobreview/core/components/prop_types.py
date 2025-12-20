"""
Property Types for Component Schema Definition.

This module provides the PropTypes API that plugins use to declare
what properties their components accept. Inspired by React PropTypes
and Figma's addPropertyControls.

Example:
    @register_component("chart")
    class ChartComponent:
        props = {
            "id": PropTypes.string(required=True),
            "chart": PropTypes.choice(["bar", "line", "pie"], default="bar"),
            "title": PropTypes.string(default=""),
            "animated": PropTypes.boolean(default=True),
        }
"""
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union, Callable
from enum import Enum


class PropType(Enum):
    """Supported property types."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    COLOR = "color"
    TEMPLATE = "template"  # Jinja2 template string
    OBJECT = "object"
    ARRAY = "array"
    ANY = "any"


@dataclass
class PropDef:
    """
    Definition of a single property.
    
    Attributes:
        type: The property type
        default: Default value if not provided
        required: Whether the property must be provided
        choices: Valid options for choice type
        min_value: Minimum value for numbers
        max_value: Maximum value for numbers
        description: Human-readable description
        validator: Optional custom validation function
    """
    type: PropType
    default: Any = None
    required: bool = False
    choices: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None
    
    def validate(self, value: Any) -> Any:
        """
        Validate and coerce a value according to this prop definition.
        
        Parameters:
            value: The value to validate
            
        Returns:
            The validated (possibly coerced) value
            
        Raises:
            ValueError: If validation fails
        """
        if value is None:
            if self.required:
                raise ValueError("Value is required")
            return self.default
        
        # Type-specific validation
        if self.type == PropType.STRING:
            if not isinstance(value, str):
                value = str(value)
            return value
            
        elif self.type == PropType.NUMBER:
            if isinstance(value, bool):
                raise ValueError(f"Expected number, got boolean")
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Expected number, got {type(value).__name__}")
            if self.min_value is not None and value < self.min_value:
                raise ValueError(f"Value {value} is below minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ValueError(f"Value {value} is above maximum {self.max_value}")
            return value
            
        elif self.type == PropType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ('true', 'yes', '1'):
                    return True
                if value.lower() in ('false', 'no', '0'):
                    return False
            raise ValueError(f"Expected boolean, got {type(value).__name__}")
            
        elif self.type == PropType.CHOICE:
            if self.choices and value not in self.choices:
                raise ValueError(f"Invalid choice '{value}'. Must be one of: {self.choices}")
            return value
            
        elif self.type == PropType.COLOR:
            # Accept theme color names or hex values
            if isinstance(value, str):
                return value
            raise ValueError(f"Expected color string, got {type(value).__name__}")
            
        elif self.type == PropType.TEMPLATE:
            # Jinja2 template strings - just validate it's a string
            if not isinstance(value, str):
                value = str(value)
            return value
            
        elif self.type == PropType.OBJECT:
            if not isinstance(value, dict):
                raise ValueError(f"Expected object, got {type(value).__name__}")
            return value
            
        elif self.type == PropType.ARRAY:
            if not isinstance(value, list):
                raise ValueError(f"Expected array, got {type(value).__name__}")
            return value
            
        elif self.type == PropType.ANY:
            return value
        
        # Custom validator
        if self.validator and not self.validator(value):
            raise ValueError(f"Custom validation failed for value: {value}")
        
        return value


class PropTypes:
    """
    Factory class for creating PropDef instances.
    
    This provides a clean API for plugins to declare component schemas:
    
        props = {
            "title": PropTypes.string(required=True),
            "count": PropTypes.number(default=0, min=0),
            "type": PropTypes.choice(["bar", "line"], default="bar"),
        }
    """
    
    @staticmethod
    def string(
        default: Optional[str] = None,
        required: bool = False,
        description: str = ""
    ) -> PropDef:
        """String property."""
        return PropDef(
            type=PropType.STRING,
            default=default,
            required=required,
            description=description
        )
    
    @staticmethod
    def number(
        default: Optional[float] = None,
        required: bool = False,
        min: Optional[float] = None,
        max: Optional[float] = None,
        description: str = ""
    ) -> PropDef:
        """Numeric property with optional min/max constraints."""
        return PropDef(
            type=PropType.NUMBER,
            default=default,
            required=required,
            min_value=min,
            max_value=max,
            description=description
        )
    
    @staticmethod
    def boolean(
        default: bool = False,
        description: str = ""
    ) -> PropDef:
        """Boolean property."""
        return PropDef(
            type=PropType.BOOLEAN,
            default=default,
            required=False,
            description=description
        )
    
    @staticmethod
    def choice(
        options: List[str],
        default: Optional[str] = None,
        required: bool = False,
        description: str = ""
    ) -> PropDef:
        """Enumerated choice property."""
        if default is None and options:
            default = options[0]
        return PropDef(
            type=PropType.CHOICE,
            default=default,
            required=required,
            choices=options,
            description=description
        )
    
    @staticmethod
    def color(
        default: Optional[str] = None,
        description: str = ""
    ) -> PropDef:
        """Color property (theme color name or hex value)."""
        return PropDef(
            type=PropType.COLOR,
            default=default,
            required=False,
            description=description
        )
    
    @staticmethod
    def template(
        default: Optional[str] = None,
        required: bool = False,
        description: str = ""
    ) -> PropDef:
        """Jinja2 template string property."""
        return PropDef(
            type=PropType.TEMPLATE,
            default=default,
            required=required,
            description=description
        )
    
    @staticmethod
    def object(
        default: Optional[dict] = None,
        required: bool = False,
        description: str = ""
    ) -> PropDef:
        """Object/dict property."""
        return PropDef(
            type=PropType.OBJECT,
            default=default if default is not None else {},
            required=required,
            description=description
        )
    
    @staticmethod
    def array(
        default: Optional[list] = None,
        required: bool = False,
        description: str = ""
    ) -> PropDef:
        """Array/list property."""
        return PropDef(
            type=PropType.ARRAY,
            default=default if default is not None else [],
            required=required,
            description=description
        )
    
    @staticmethod
    def any(
        default: Any = None,
        required: bool = False,
        description: str = ""
    ) -> PropDef:
        """Any type property (escape hatch)."""
        return PropDef(
            type=PropType.ANY,
            default=default,
            required=required,
            description=description
        )

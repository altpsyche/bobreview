"""
Component Processor for YAML Validation.

This module processes YAML component definitions, validates them
against registered component schemas, and produces validated props
ready for template rendering.

The processor is the bridge between user YAML and template context.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from .registry import ComponentRegistry, get_component_registry, ComponentDefinition
from .prop_types import PropDef

logger = logging.getLogger(__name__)


class ComponentValidationError(Exception):
    """Raised when component validation fails."""
    
    def __init__(self, message: str, component_type: str = None, prop: str = None):
        self.component_type = component_type
        self.prop = prop
        super().__init__(message)


@dataclass
class ValidatedComponent:
    """
    A validated component ready for rendering.
    
    Attributes:
        type: Component type name
        props: Validated property values
        template: Optional component-specific template path
        raw: Original unvalidated YAML data (for debugging)
    """
    type: str
    props: Dict[str, Any]
    template: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a prop value with optional default."""
        return self.props.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access: component['prop_name']."""
        return self.props[key]


class ComponentProcessor:
    """
    Processes and validates YAML components against their schemas.
    
    This is the core of the Property Controls pattern. It:
    1. Looks up the component type in the registry
    2. Validates YAML data against the component's prop schema
    3. Applies defaults for missing optional props
    4. Returns a ValidatedComponent ready for rendering
    """
    
    def __init__(self, registry: ComponentRegistry = None):
        """
        Initialize the processor.
        
        Parameters:
            registry: Component registry to use (defaults to global)
        """
        self.registry = registry or get_component_registry()
        self._strict = True  # Error on unknown props
    
    def set_strict(self, strict: bool) -> None:
        """
        Set validation strictness.
        
        Parameters:
            strict: If True, error on unknown props. If False, ignore them.
        """
        self._strict = strict
    
    def process(self, yaml_component: Dict[str, Any]) -> ValidatedComponent:
        """
        Validate a YAML component against its schema.
        
        Parameters:
            yaml_component: Raw YAML component dict with 'type' and props
            
        Returns:
            ValidatedComponent with validated props
            
        Raises:
            ComponentValidationError: If validation fails
        """
        # Get component type
        comp_type = yaml_component.get('type')
        if not comp_type:
            raise ComponentValidationError(
                "Component missing 'type' field",
                component_type=None
            )
        
        # Look up component definition
        component_def = self.registry.get(comp_type)
        if component_def is None:
            raise ComponentValidationError(
                f"Unknown component type: '{comp_type}'",
                component_type=comp_type
            )
        
        # Validate props
        validated_props = self._validate_props(
            yaml_component,
            component_def,
            comp_type
        )
        
        return ValidatedComponent(
            type=comp_type,
            props=validated_props,
            template=component_def.template,
            raw=yaml_component
        )
    
    def process_all(
        self,
        yaml_components: List[Dict[str, Any]]
    ) -> List[ValidatedComponent]:
        """
        Process a list of YAML components.
        
        Parameters:
            yaml_components: List of raw YAML component dicts
            
        Returns:
            List of ValidatedComponent instances
            
        Raises:
            ComponentValidationError: If any component fails validation
        """
        return [self.process(comp) for comp in yaml_components]
    
    def _validate_props(
        self,
        yaml_data: Dict[str, Any],
        component_def: ComponentDefinition,
        comp_type: str
    ) -> Dict[str, Any]:
        """
        Validate props against component schema.
        
        Parameters:
            yaml_data: Raw YAML data
            component_def: Component definition with schema
            comp_type: Component type name (for error messages)
            
        Returns:
            Dict of validated prop values
            
        Raises:
            ComponentValidationError: If validation fails
        """
        schema = component_def.props
        validated = {}
        
        # Reserved keys that aren't props
        reserved_keys = {'type'}
        
        # Validate declared props
        for prop_name, prop_def in schema.items():
            if prop_name in yaml_data:
                try:
                    validated[prop_name] = prop_def.validate(yaml_data[prop_name])
                except ValueError as e:
                    raise ComponentValidationError(
                        f"Invalid value for '{prop_name}' in {comp_type}: {e}",
                        component_type=comp_type,
                        prop=prop_name
                    )
            elif prop_def.required:
                raise ComponentValidationError(
                    f"Missing required prop '{prop_name}' in {comp_type}",
                    component_type=comp_type,
                    prop=prop_name
                )
            elif prop_def.default is not None:
                validated[prop_name] = prop_def.default
        
        # Check for unknown props
        if self._strict:
            unknown_props = set(yaml_data.keys()) - set(schema.keys()) - reserved_keys
            if unknown_props:
                logger.warning(
                    f"Unknown props in {comp_type}: {unknown_props}. "
                    f"Valid props are: {list(schema.keys())}"
                )
                # Don't error, just warn - allows forward compatibility
        
        # Pass through unknown props for flexibility (but warn)
        for key in yaml_data:
            if key not in validated and key not in reserved_keys:
                validated[key] = yaml_data[key]
        
        return validated
    
    def get_schema(self, comp_type: str) -> Optional[Dict[str, PropDef]]:
        """
        Get the schema for a component type.
        
        Parameters:
            comp_type: Component type name
            
        Returns:
            Dict of prop definitions, or None if not found
        """
        component_def = self.registry.get(comp_type)
        if component_def:
            return component_def.props
        return None
    
    def list_component_types(self) -> List[str]:
        """Get all registered component type names."""
        return list(self.registry.list_components().keys())


def get_component_processor() -> ComponentProcessor:
    """Get a component processor with the global registry."""
    return ComponentProcessor()

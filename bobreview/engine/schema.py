"""
JSON schema definition and validation for report systems.

This module defines the complete schema for JSON-based report system definitions,
including validation logic and dataclass representations of all configuration sections.
"""

from dataclasses import dataclass, field, fields
from typing import Dict, List, Any, Optional


@dataclass
class FieldConfig:
    """Configuration for a data field in the data source."""
    type: str  # 'string', 'integer', 'float', 'boolean'
    required: bool = True
    min: Optional[float] = None
    max: Optional[float] = None
    pattern: Optional[str] = None
    default: Optional[Any] = None


@dataclass
class ValidationConfig:
    """Validation rules for data parsing."""
    allow_missing_fields: bool = False
    skip_invalid: bool = True
    strict_mode: bool = False


@dataclass
class DataSourceConfig:
    """Configuration for data source parsing."""
    type: str  # 'filename_pattern', 'csv', 'json', 'api', 'custom'
    input_format: str  # 'png', 'csv', 'json', etc.
    pattern: Optional[str] = None  # Pattern for filename_pattern type
    fields: Dict[str, FieldConfig] = field(default_factory=dict)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    # For CSV/JSON formats
    column_mapping: Optional[Dict[str, str]] = None
    header_row: Optional[int] = None
    # For API formats
    endpoint: Optional[str] = None
    auth: Optional[Dict[str, str]] = None


# Note: Domain-specific schema classes should be defined by plugins.


# LLMConfig removed - use flat fields in ReportSystemDefinition

# ============================================================================
# GENERIC DICT-BASED STRUCTURES (Plugin-First Architecture)
# ============================================================================
# Domain-specific structures (LLM generators, pages, charts) are now stored as
# Dict[str, Any] instead of typed dataclasses. This gives plugins full
# flexibility to define their own JSON structure.
#
# Core validation only requires: schema_version, id, data_source
# All other fields pass through as generic dicts for plugin consumption.
#
# Previously typed as:
#   - LLMGeneratorConfig, PromptCategoryConfig, DataTableConfig
#   - PageConfig, ChartConfig, TemplateConfig, DataRequirements
#
# These are now just Dict[str, Any] - plugins access fields directly.
# ============================================================================


class Labels:
    """
    Simple dict-based label storage for UI text.
    
    Templates use: labels.get('key', 'Default Text')
    JSON defines overrides in the 'labels' section.
    No need to pre-define every label - just use get() with a default.
    
    This replaces the verbose dataclass approach with a simpler dict wrapper.
    """
    
    def __init__(self, data: Dict[str, str] = None):
        self._data = data or {}
    
    def get(self, key: str, default: str = '') -> str:
        """Get a label by key with a default fallback."""
        return self._data.get(key, default)
    
    def __getattr__(self, key: str) -> str:
        """Allow attribute-style access: labels.foo returns labels._data.get('foo', '')"""
        if key.startswith('_'):
            raise AttributeError(key)
        return self._data.get(key, '')
    
    def __getitem__(self, key: str) -> str:
        """Allow dict-style access: labels['foo']"""
        return self._data.get(key, '')
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def update(self, other: Dict[str, str]):
        """Merge in additional labels."""
        self._data.update(other)
    
    @property
    def data(self) -> Dict[str, str]:
        """Access the underlying dict."""
        return self._data



@dataclass
class ReportSystemDefinition:
    """
    Report system structure from JSON.
    
    Contains ONLY structural data (pages, generators, data_source).
    Config settings (llm_*, theme, etc.) come from Config class.
    """
    # Required metadata
    schema_version: str
    id: str
    name: str
    version: str
    description: str
    author: str
    
    # Structural data (what the report contains) - generic dicts for plugin flexibility
    data_source: DataSourceConfig
    llm_generators: List[Dict[str, Any]] = field(default_factory=list)
    pages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Plugin extensions (passed to components)
    extensions: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    
    # Content/labels for templates
    labels: Labels = field(default_factory=lambda: Labels({}))
    content_blocks: Dict[str, Any] = field(default_factory=dict)
    
    # Optional metadata
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    title: Optional[str] = None


def validate_report_system(data: Dict[str, Any]) -> List[str]:
    """
    Validate a report system JSON definition.
    
    Parameters:
        data: Parsed JSON data
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required top-level fields
    # Note: 'pages' and 'llm_generators' are optional - defined by users in YAML
    # Note: LLM settings are flat: llm_provider, llm_model, llm_temperature (optional)
    required_fields = ['schema_version', 'id', 'name', 'version', 'description', 
                      'author', 'data_source']
    
    for field_name in required_fields:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")
    
    if errors:
        return errors
    
    # Validate schema version
    if data.get('schema_version') != '1.0':
        errors.append(f"Unsupported schema version: {data.get('schema_version')} (expected 1.0)")
    
    # Validate ID format
    id_val = data.get('id', '')
    if not id_val or not id_val.replace('_', '').isalnum():
        errors.append(f"Invalid ID format: {id_val} (must be alphanumeric with underscores)")
    
    # Validate data source
    data_source = data.get('data_source', {})
    if 'type' not in data_source:
        errors.append("data_source.type is required")
    if 'input_format' not in data_source:
        errors.append("data_source.input_format is required")
    
    # Note: Domain-specific validation (llm_generators, pages, charts, thresholds)
    # is now plugin responsibility via ComponentProcessor.
    # Core only validates the minimal structural requirements above.
    
    # Optional: Validate llm_generators and pages are lists if present
    if 'llm_generators' in data and not isinstance(data['llm_generators'], list):
        errors.append("llm_generators must be a list")
    
    if 'pages' in data and not isinstance(data['pages'], list):
        errors.append("pages must be a list")
    
    return errors


def parse_field_config(data: Dict[str, Any]) -> FieldConfig:
    """Parse a field configuration from JSON."""
    return FieldConfig(
        type=data.get('type', 'string'),
        required=data.get('required', True),
        min=data.get('min'),
        max=data.get('max'),
        pattern=data.get('pattern'),
        default=data.get('default')
    )


def parse_validation_config(data: Dict[str, Any]) -> ValidationConfig:
    """Parse validation configuration from JSON."""
    return ValidationConfig(
        allow_missing_fields=data.get('allow_missing_fields', False),
        skip_invalid=data.get('skip_invalid', True),
        strict_mode=data.get('strict_mode', False)
    )


def parse_data_source_config(data: Dict[str, Any]) -> DataSourceConfig:
    """Parse data source configuration from JSON."""
    fields = {}
    if 'fields' in data:
        for field_name, field_data in data['fields'].items():
            fields[field_name] = parse_field_config(field_data)
    
    validation = ValidationConfig()
    if 'validation' in data:
        validation = parse_validation_config(data['validation'])
    
    return DataSourceConfig(
        type=data['type'],
        input_format=data['input_format'],
        pattern=data.get('pattern'),
        fields=fields,
        validation=validation,
        column_mapping=data.get('column_mapping'),
        header_row=data.get('header_row'),
        endpoint=data.get('endpoint'),
        auth=data.get('auth')
    )

# Note: Domain-specific parsers removed - plugins handle their own JSON structure
# These are now just Dict[str, Any] pass-through


def parse_label_config(data: Optional[Dict[str, Any]]) -> Labels:
    """
    Parse label configuration from JSON.
    
    Simply wraps the JSON labels dict in a Labels object.
    Templates use labels.get('key', 'Default Text') pattern.
    
    Parameters:
        data: Optional dictionary from JSON labels section
    
    Returns:
        Labels object wrapping the provided dict (or empty dict if None)
    """
    if data is None:
        return Labels({})
    
    # Ensure all values are strings
    string_data = {k: str(v) for k, v in data.items()}
    return Labels(string_data)



def parse_report_system_definition(data: Dict[str, Any]) -> ReportSystemDefinition:
    """
    Parse complete report system definition from JSON.
    
    Domain-specific structures (llm_generators, pages, charts) are passed through
    as generic dicts for plugin consumption. Core only parses data_source.
    
    Parameters:
        data: Parsed JSON data (flat format)
    
    Returns:
        ReportSystemDefinition object
    
    Raises:
        ValueError: If validation fails
    """
    # Validate first
    errors = validate_report_system(data)
    if errors:
        error_msg = "Report system validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    # Pass through llm_generators and pages as generic dicts - plugins handle parsing
    return ReportSystemDefinition(
        schema_version=data['schema_version'],
        id=data['id'],
        name=data['name'],
        version=data['version'],
        description=data['description'],
        author=data['author'],
        data_source=parse_data_source_config(data['data_source']),
        llm_generators=data.get('llm_generators', []),  # Pass through as dicts
        pages=data.get('pages', []),  # Pass through as dicts
        extensions=data.get('extensions', {}),
        thresholds=data.get('thresholds', {}),
        labels=parse_label_config(data.get('labels')),
        content_blocks=data.get('content_blocks', {}),
        tags=data.get('tags', []),
        documentation_url=data.get('documentation_url'),
        examples=data.get('examples', []),
        title=data.get('title')
    )

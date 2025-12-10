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


@dataclass
class LLMConfig:
    """Configuration for LLM provider and settings."""
    provider: str = 'openai'  # 'openai', 'anthropic', 'ollama'
    model: str = 'gpt-4o'
    temperature: float = 0.7
    max_tokens: int = 2000
    chunk_size: int = 10
    enable_cache: bool = True
    api_base: Optional[str] = None  # Custom API endpoint
    api_key: Optional[str] = None  # API key for the selected provider
    api_key_env: Optional[str] = None  # Environment variable for API key


@dataclass
class PromptCategoryConfig:
    """Configuration for a prompt category."""
    id: str
    title: str
    focus: str
    priority: int = 50


@dataclass
class DataTableConfig:
    """Configuration for data table in LLM prompts."""
    columns: List[str]
    sample_strategy: str = 'mixed'  # 'mixed', 'random', 'sequential', 'critical'
    samples: Optional[Dict[str, int]] = None  # {'critical': 1, 'high_load': 3, ...}
    max_rows: int = 50


@dataclass
class LLMGeneratorConfig:
    """Configuration for an LLM content generator."""
    id: str
    name: str
    description: str
    prompt_template: str
    categories: List[PromptCategoryConfig] = field(default_factory=list)
    data_table: Optional[DataTableConfig] = None
    returns: str = 'string'  # 'string' or 'dict'
    enabled: bool = True


@dataclass
class ChartConfig:
    """Configuration for a chart on a page."""
    id: str
    type: str  # 'line', 'bar', 'scatter', 'histogram'
    title: str
    x_field: str
    y_field: str
    # Plugin-specific options go in the options dict (e.g., performance_zones)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateConfig:
    """Configuration for page template."""
    type: str  # 'builtin', 'custom', 'inline'
    name: Optional[str] = None
    content: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRequirements:
    """What data a page needs to render."""
    # All default to False - plugins opt-in to what they need
    data_points: bool = False
    images: bool = False
    # Plugin-specific requirements go in extensions
    extensions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PageConfig:
    """Configuration for a report page."""
    id: str
    filename: str
    nav_label: str
    nav_order: int
    template: TemplateConfig
    llm_content: List[str] = field(default_factory=list)
    # Maps template variable names to generator IDs
    # e.g., {'review_text': 'review_text', 'exec_summary': 'executive_summary'}
    llm_mappings: Dict[str, str] = field(default_factory=dict)
    data_requirements: DataRequirements = field(default_factory=DataRequirements)
    charts: List[ChartConfig] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    # Homepage card display
    card_icon: str = ""
    card_description: str = ""


@dataclass
class ThemeConfig:
    """Configuration for report theme."""
    default: str = 'dark'
    override_colors: Dict[str, str] = field(default_factory=dict)


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    default_filename: str = 'report.html'
    embed_images: bool = True
    linked_css: bool = False


@dataclass
class ContentBlockConfig:
    """Configuration for a content block with title and description."""
    title: str
    description: str


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


# Type alias for backward compatibility
LabelConfig = Labels


@dataclass
class ReportSystemDefinition:
    """Complete report system definition from JSON."""
    # Required fields (no defaults)
    schema_version: str
    id: str
    name: str
    version: str
    description: str
    author: str
    data_source: DataSourceConfig
    llm_config: LLMConfig
    llm_generators: List[LLMGeneratorConfig]
    pages: List[PageConfig]
    # Optional fields with defaults
    # Plugin-specific extensions (metrics, analytics config, etc.)
    extensions: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # CMS-style labels - simple dict wrapper, templates use labels.get('key', 'default')
    labels: Labels = field(default_factory=lambda: Labels({}))
    
    # Content blocks for longer descriptive text (lists of ContentBlockConfig or strings)
    content_blocks: Dict[str, Any] = field(default_factory=dict)
    
    # Optional metadata
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    location: Optional[str] = None  # Optional metadata


def validate_report_system(data: Dict[str, Any]) -> List[str]:
    """
    Validate a report system JSON definition.
    
    Parameters:
        data: Parsed JSON data
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Required top-level fields (metrics and thresholds are optional for non-analytics reports)
    required_fields = ['schema_version', 'id', 'name', 'version', 'description', 
                      'author', 'data_source', 'llm_config', 'llm_generators', 'pages']
    
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
    
    # Note: metrics validation is now plugin responsibility
    # Extensions are validated by plugins, not core
    
    # Validate LLM generators
    llm_generators = data.get('llm_generators', [])
    if not isinstance(llm_generators, list):
        errors.append("llm_generators must be a list")
    else:
        generator_ids = set()
        for i, gen in enumerate(llm_generators):
            if not isinstance(gen, dict):
                errors.append(f"llm_generators[{i}] must be an object")
                continue
            
            gen_id = gen.get('id')
            if not gen_id:
                errors.append(f"llm_generators[{i}] missing required field 'id'")
            elif gen_id in generator_ids:
                errors.append(f"Duplicate LLM generator ID: {gen_id}")
            else:
                generator_ids.add(gen_id)
            
            if 'name' not in gen:
                errors.append(f"llm_generators[{i}] ({gen_id}) missing required field 'name'")
            if 'prompt_template' not in gen:
                errors.append(f"llm_generators[{i}] ({gen_id}) missing required field 'prompt_template'")
    
    # Validate pages
    pages = data.get('pages', [])
    if not isinstance(pages, list):
        errors.append("pages must be a list")
    else:
        page_ids = set()
        for i, page in enumerate(pages):
            if not isinstance(page, dict):
                errors.append(f"pages[{i}] must be an object")
                continue
            
            page_id = page.get('id')
            if not page_id:
                errors.append(f"pages[{i}] missing required field 'id'")
            elif page_id in page_ids:
                errors.append(f"Duplicate page ID: {page_id}")
            else:
                page_ids.add(page_id)
            
            required_page_fields = ['filename', 'nav_label', 'nav_order', 'template']
            for field_name in required_page_fields:
                if field_name not in page:
                    errors.append(f"pages[{i}] ({page_id}) missing required field '{field_name}'")
    
    # Validate thresholds are numeric
    thresholds = data.get('thresholds', {})
    if not isinstance(thresholds, dict):
        errors.append("thresholds must be an object")
    else:
        for key, value in thresholds.items():
            if not isinstance(value, (int, float)):
                errors.append(f"thresholds.{key} must be a number (got {type(value).__name__})")
    
    # Validate LLM config
    llm_config = data.get('llm_config', {})
    if isinstance(llm_config, dict):
        if 'temperature' in llm_config:
            temp = llm_config['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append(f"llm_config.temperature must be between 0 and 2 (got {temp})")
        
        if 'chunk_size' in llm_config:
            chunk = llm_config['chunk_size']
            if not isinstance(chunk, int) or chunk <= 0:
                errors.append(f"llm_config.chunk_size must be a positive integer (got {chunk})")
    
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

# Note: Domain-specific parsers should be defined by plugins.



def parse_llm_config(data: Dict[str, Any]) -> LLMConfig:
    """
    Create an LLMConfig from a mapping of configuration values.
    
    Parameters:
        data (dict): Mapping containing optional keys to configure the LLM:
            - provider: provider identifier (default 'openai')
            - model: model name (default 'gpt-4o')
            - temperature: sampling temperature (default 0.7)
            - max_tokens: maximum token limit (default 2000)
            - chunk_size: chunk size for batching (default 10)
            - enable_cache: whether to enable caching (default True)
            - api_base: optional custom API base URL
            - api_key: optional API key for the selected provider
            - api_key_env: optional environment variable name holding the API key
    
    Returns:
        LLMConfig: An LLMConfig populated from the provided mapping, using defaults for any missing fields.
    """
    return LLMConfig(
        provider=data.get('provider', 'openai'),
        model=data.get('model', 'gpt-4o'),
        temperature=data.get('temperature', 0.7),
        max_tokens=data.get('max_tokens', 2000),
        chunk_size=data.get('chunk_size', 10),
        enable_cache=data.get('enable_cache', True),
        api_base=data.get('api_base'),
        api_key=data.get('api_key'),
        api_key_env=data.get('api_key_env')
    )


def parse_prompt_category_config(data: Dict[str, Any]) -> PromptCategoryConfig:
    """Parse prompt category configuration from JSON."""
    return PromptCategoryConfig(
        id=data['id'],
        title=data['title'],
        focus=data['focus'],
        priority=data.get('priority', 50)
    )


def parse_data_table_config(data: Dict[str, Any]) -> DataTableConfig:
    """Parse data table configuration from JSON."""
    return DataTableConfig(
        columns=data['columns'],
        sample_strategy=data.get('sample_strategy', 'mixed'),
        samples=data.get('samples'),
        max_rows=data.get('max_rows', 50)
    )


def parse_llm_generator_config(data: Dict[str, Any]) -> LLMGeneratorConfig:
    """Parse LLM generator configuration from JSON."""
    categories = []
    if 'categories' in data:
        categories = [parse_prompt_category_config(c) for c in data['categories']]
    
    data_table = None
    if 'data_table' in data:
        data_table = parse_data_table_config(data['data_table'])
    
    return LLMGeneratorConfig(
        id=data['id'],
        name=data['name'],
        description=data['description'],
        prompt_template=data['prompt_template'],
        categories=categories,
        data_table=data_table,
        returns=data.get('returns', 'string'),
        enabled=data.get('enabled', True)
    )


def parse_chart_config(data: Dict[str, Any]) -> ChartConfig:
    """Parse chart configuration from JSON."""
    return ChartConfig(
        id=data['id'],
        type=data['type'],
        title=data['title'],
        x_field=data['x_field'],
        y_field=data['y_field'],
        options=data.get('options', {})
    )


def parse_template_config(data: Dict[str, Any]) -> TemplateConfig:
    """Parse template configuration from JSON."""
    return TemplateConfig(
        type=data['type'],
        name=data.get('name'),
        content=data.get('content'),
        variables=data.get('variables', {})
    )


def parse_data_requirements(data: Dict[str, Any]) -> DataRequirements:
    """Parse data requirements from JSON."""
    return DataRequirements(
        data_points=data.get('data_points', False),
        images=data.get('images', False),
        extensions=data.get('extensions', {})
    )


def parse_page_config(data: Dict[str, Any]) -> PageConfig:
    """Parse page configuration from JSON."""
    charts = []
    if 'charts' in data:
        charts = [parse_chart_config(c) for c in data['charts']]
    
    data_requirements = DataRequirements()
    if 'data_requirements' in data:
        data_requirements = parse_data_requirements(data['data_requirements'])
    
    return PageConfig(
        id=data['id'],
        filename=data['filename'],
        nav_label=data['nav_label'],
        nav_order=data['nav_order'],
        template=parse_template_config(data['template']),
        llm_content=data.get('llm_content', []),
        llm_mappings=data.get('llm_mappings', {}),
        data_requirements=data_requirements,
        charts=charts,
        features=data.get('features', {}),
        enabled=data.get('enabled', True),
        card_icon=data.get('card_icon', ''),
        card_description=data.get('card_description', '')
    )


def parse_theme_config(data: Dict[str, Any]) -> ThemeConfig:
    """Parse theme configuration from JSON."""
    return ThemeConfig(
        default=data.get('default', 'dark'),
        override_colors=data.get('override_colors', {})
    )


def parse_output_config(data: Dict[str, Any]) -> OutputConfig:
    """Parse output configuration from JSON."""
    return OutputConfig(
        default_filename=data.get('default_filename', 'report.html'),
        embed_images=data.get('embed_images', True),
        linked_css=data.get('linked_css', False)
    )


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
    
    Parameters:
        data: Parsed JSON data
    
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
    
    # Parse all sections
    llm_generators = [parse_llm_generator_config(g) for g in data['llm_generators']]
    pages = [parse_page_config(p) for p in data['pages']]
    
    return ReportSystemDefinition(
        schema_version=data['schema_version'],
        id=data['id'],
        name=data['name'],
        version=data['version'],
        description=data['description'],
        author=data['author'],
        data_source=parse_data_source_config(data['data_source']),
        # Plugin-specific extensions (metrics, analytics, etc.) - parsed by plugins
        extensions=data.get('extensions', {}),
        thresholds=data.get('thresholds', {}),
        llm_config=parse_llm_config(data['llm_config']),
        llm_generators=llm_generators,
        pages=pages,
        theme=parse_theme_config(data.get('theme', {})),
        output=parse_output_config(data.get('output', {})),
        labels=parse_label_config(data.get('labels')),
        content_blocks=data.get('content_blocks', {}),
        tags=data.get('tags', []),
        documentation_url=data.get('documentation_url'),
        examples=data.get('examples', []),
        location=data.get('location')
    )

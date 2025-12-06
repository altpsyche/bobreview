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


@dataclass
class DerivedMetricConfig:
    """Configuration for a derived metric calculation."""
    id: str
    description: str
    calculation: str  # Expression or function name
    dependencies: List[str] = field(default_factory=list)


@dataclass
class StatisticsConfig:
    """Configuration for statistical calculations."""
    basic: List[str] = field(default_factory=lambda: ['min', 'max', 'mean', 'median', 'stdev'])
    advanced: List[str] = field(default_factory=lambda: ['p90', 'p95', 'p99', 'variance', 'cv'])
    analysis: List[str] = field(default_factory=lambda: ['confidence_interval', 'trend', 'outliers'])


@dataclass
class MetricConfig:
    """Configuration for metrics and analysis."""
    primary: List[str]
    derived: List[DerivedMetricConfig] = field(default_factory=list)
    statistics: StatisticsConfig = field(default_factory=StatisticsConfig)


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
    performance_zones: Optional[Dict[str, Any]] = None
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
    stats: bool = True
    data_points: bool = False
    images: bool = False


@dataclass
class PageConfig:
    """Configuration for a report page."""
    id: str
    filename: str
    nav_label: str
    nav_order: int
    template: TemplateConfig
    llm_content: List[str] = field(default_factory=list)
    data_requirements: DataRequirements = field(default_factory=DataRequirements)
    charts: List[ChartConfig] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class ThemeConfig:
    """Configuration for report theme."""
    default: str = 'dark'
    override_colors: Dict[str, str] = field(default_factory=dict)


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    default_filename: str = 'performance_report.html'
    embed_images: bool = True
    linked_css: bool = False


@dataclass
class LabelConfig:
    """
    CMS-style UI text labels - all configurable via JSON.
    
    No hardcoded strings in templates. All display text comes from here.
    """
    # Metric labels
    draw_calls: str = "Draw Calls"
    triangles: str = "Triangle Count"
    
    # Section headers
    executive_summary: str = "Executive Summary"
    detailed_analysis: str = "Detailed Analysis"
    quick_stats: str = "Quick Statistics"
    metric_deep_dive: str = "Metric Deep Dive"
    performance_zones: str = "Performance Zones & Hotspots"
    visual_analysis: str = "Visual Analysis"
    optimization: str = "Optimization Checklist"
    statistical_summary: str = "Statistical Summary"
    full_sample_table: str = "Full Sample Table"
    
    # Stats labels
    average: str = "Average"
    minimum: str = "Min"
    maximum: str = "Max"
    median: str = "Median"
    mean: str = "Mean"
    std_dev: str = "Std Dev"
    variance: str = "Variance"
    cv: str = "CV (Coefficient of Variation)"
    total_captures: str = "Total Captures"
    
    # Status labels
    high_load: str = "High-Load"
    low_load: str = "Low-Load"
    peak_hotspot: str = "Peak Hotspot"
    high_load_frames: str = "High-Load Frames"
    low_load_frames: str = "Low-Load Frames"
    
    # Trend labels
    improving: str = "Improving"
    degrading: str = "Degrading"
    stable: str = "Stable"
    trend: str = "Trend"
    
    # Range labels
    range_label: str = "Range"
    performance_variance: str = "Performance Variance"
    
    # Table headers
    index: str = "Index"
    testcase: str = "Test Case"
    timestamp: str = "Timestamp"
    screenshot: str = "Screenshot"
    
    # Navigation
    home: str = "Home"
    metrics: str = "Metrics"
    zones: str = "Zones"
    visuals: str = "Visuals"
    
    # Footer
    footer_text: str = "Generated by BobReview - Performance Analysis and Review Tool"
    
    # Threshold labels
    soft_cap: str = "Soft Cap"
    hard_cap: str = "Hard Cap"
    threshold: str = "Threshold"
    
    # Percentile labels
    p90: str = "P90"
    p95: str = "P95"
    p99: str = "P99"
    
    # Action labels  
    view_details: str = "View Details"
    explore: str = "Explore"
    
    # Custom labels (user-defined via JSON)
    custom: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReportSystemDefinition:
    """Complete report system definition from JSON."""
    schema_version: str
    id: str
    name: str
    version: str
    description: str
    author: str
    data_source: DataSourceConfig
    metrics: MetricConfig
    thresholds: Dict[str, Any]
    llm_config: LLMConfig
    llm_generators: List[LLMGeneratorConfig]
    pages: List[PageConfig]
    theme: ThemeConfig
    output: OutputConfig
    
    # CMS-style labels
    labels: LabelConfig = field(default_factory=LabelConfig)
    
    # Optional metadata
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)


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
    required_fields = ['schema_version', 'id', 'name', 'version', 'description', 
                      'author', 'data_source', 'metrics', 'thresholds', 
                      'llm_config', 'llm_generators', 'pages', 'theme', 'output']
    
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
    
    # Validate metrics
    metrics = data.get('metrics', {})
    if 'primary' not in metrics or not isinstance(metrics['primary'], list):
        errors.append("metrics.primary must be a list of primary metric names")
    
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


def parse_derived_metric_config(data: Dict[str, Any]) -> DerivedMetricConfig:
    """Parse derived metric configuration from JSON."""
    return DerivedMetricConfig(
        id=data['id'],
        description=data['description'],
        calculation=data['calculation'],
        dependencies=data.get('dependencies', [])
    )


def parse_statistics_config(data: Dict[str, Any]) -> StatisticsConfig:
    """Parse statistics configuration from JSON."""
    return StatisticsConfig(
        basic=data.get('basic', ['min', 'max', 'mean', 'median', 'stdev']),
        advanced=data.get('advanced', ['p90', 'p95', 'p99', 'variance', 'cv']),
        analysis=data.get('analysis', ['confidence_interval', 'trend', 'outliers'])
    )


def parse_metric_config(data: Dict[str, Any]) -> MetricConfig:
    """Parse metric configuration from JSON."""
    derived = []
    if 'derived' in data:
        derived = [parse_derived_metric_config(d) for d in data['derived']]
    
    statistics = StatisticsConfig()
    if 'statistics' in data:
        statistics = parse_statistics_config(data['statistics'])
    
    return MetricConfig(
        primary=data['primary'],
        derived=derived,
        statistics=statistics
    )


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
        performance_zones=data.get('performance_zones'),
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
        stats=data.get('stats', True),
        data_points=data.get('data_points', False),
        images=data.get('images', False)
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
        data_requirements=data_requirements,
        charts=charts,
        features=data.get('features', {}),
        enabled=data.get('enabled', True)
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
        default_filename=data.get('default_filename', 'performance_report.html'),
        embed_images=data.get('embed_images', True),
        linked_css=data.get('linked_css', False)
    )


def parse_label_config(data: Optional[Dict[str, Any]]) -> LabelConfig:
    """
    Parse label configuration from JSON.
    
    Supports all standard LabelConfig fields plus custom keys.
    Any keys not matching standard fields are placed in the custom dict.
    
    Parameters:
        data: Optional dictionary from JSON labels section
    
    Returns:
        LabelConfig with defaults overridden by provided values
    """
    if data is None:
        return LabelConfig()
    
    # Get all standard field names from LabelConfig
    standard_fields = {f.name for f in fields(LabelConfig)}
    
    # Separate standard fields from custom fields
    standard_values = {}
    custom_values = {}
    
    for key, value in data.items():
        if key in standard_fields:
            standard_values[key] = value
        else:
            # Custom label not in standard fields
            custom_values[key] = value
    
    # Create LabelConfig with standard values
    label_config = LabelConfig(**standard_values)
    
    # Merge custom values into the custom dict
    if custom_values:
        label_config.custom.update(custom_values)
    
    return label_config


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
        metrics=parse_metric_config(data['metrics']),
        thresholds=data['thresholds'],
        llm_config=parse_llm_config(data['llm_config']),
        llm_generators=llm_generators,
        pages=pages,
        theme=parse_theme_config(data['theme']),
        output=parse_output_config(data['output']),
        labels=parse_label_config(data.get('labels')),
        tags=data.get('tags', []),
        documentation_url=data.get('documentation_url'),
        examples=data.get('examples', [])
    )

"""
Preset factory functions for report system creation.

Provides sensible defaults for common report system configurations,
reducing boilerplate when creating simple report systems.
"""

from typing import Any, Dict, List, Optional
from .schema import (
    ReportSystemDefinition,
    DataSourceConfig,
    FieldConfig,
    ValidationConfig,
    LLMConfig,
    LLMGeneratorConfig,
    PageConfig,
    TemplateConfig,
    ChartConfig,
    ThemeConfig,
    OutputConfig,
    Labels,
)


def create_simple_report_system(
    id: str,
    name: str,
    data_parser_type: str,
    template_name: str,
    *,
    description: str = "",
    author: str = "",
    fields: Optional[Dict[str, Dict[str, Any]]] = None,
    primary_metrics: Optional[List[str]] = None,
    theme: str = "dark",
    charts: Optional[List[Dict[str, Any]]] = None,
    llm_generators: Optional[List[Dict[str, Any]]] = None,
) -> ReportSystemDefinition:
    """
    Create a simple single-page report system with sensible defaults.
    
    Parameters:
        id: Unique identifier for the report system
        name: Display name
        data_parser_type: Parser type (e.g., "my_csv", "png_filename")
        template_name: Jinja2 template name (e.g., "my_plugin/pages/home.html.j2")
        description: Optional description
        author: Optional author
        fields: Field definitions (defaults to name/score/timestamp)
        primary_metrics: Primary metric fields (defaults to ["score"])
        theme: Default theme ID
        charts: Chart configurations
        llm_generators: LLM generator configurations
    
    Returns:
        ReportSystemDefinition ready to use
    
    Example:
        system = create_simple_report_system(
            id="my_scores",
            name="My Scores Report",
            data_parser_type="my_csv",
            template_name="my_plugin/pages/home.html.j2",
        )
    """
    # Default fields
    if fields is None:
        fields = {
            "name": {"type": "string", "required": True},
            "score": {"type": "float", "required": True},
            "timestamp": {"type": "integer", "required": False},
        }
    
    # Convert field dicts to FieldConfig
    field_configs = {}
    for field_name, field_def in fields.items():
        field_configs[field_name] = FieldConfig(
            type=field_def.get("type", "string"),
            required=field_def.get("required", False),
            min=field_def.get("min"),
            max=field_def.get("max"),
            pattern=field_def.get("pattern"),
        )
    
    # Build data source config
    data_source = DataSourceConfig(
        type=data_parser_type,
        input_format="csv",
        fields=field_configs,
        validation=ValidationConfig(skip_invalid=True, strict_mode=False),
    )
    
    # Build charts
    chart_configs = []
    if charts:
        for chart in charts:
            chart_configs.append(ChartConfig(
                id=chart.get("id", "chart"),
                type=chart.get("type", "bar"),
                title=chart.get("title", "Chart"),
                x_field=chart.get("x_field", "name"),
                y_field=chart.get("y_field", "score"),
                options=chart.get("options", {}),
            ))
    
    # Build LLM generators
    llm_generator_configs = []
    if llm_generators:
        for gen in llm_generators:
            llm_generator_configs.append(LLMGeneratorConfig(
                id=gen.get("id", "summary"),
                name=gen.get("name", "Summary"),
                description=gen.get("description", ""),
                prompt_template=gen.get("prompt_template", ""),
                returns=gen.get("returns", "string"),
                enabled=gen.get("enabled", True),
            ))
    
    # Build single page
    pages = [
        PageConfig(
            id="home",
            filename="index.html",
            nav_label="Overview",
            nav_order=1,
            template=TemplateConfig(type="jinja2", name=template_name),
            charts=chart_configs,
            enabled=True,
        )
    ]
    
    # Build extensions (just a dict in the schema)
    extensions = {
        "metrics": {
            "primary": primary_metrics or ["score"],
            "timestamp_field": "timestamp",
        }
    }
    
    return ReportSystemDefinition(
        schema_version="1.0",
        id=id,
        name=name,
        version="1.0.0",
        description=description,
        author=author,
        data_source=data_source,
        llm_config=LLMConfig(),
        llm_generators=llm_generator_configs,
        theme=ThemeConfig(preset=theme),
        pages=pages,
        output=OutputConfig(default_filename=f"{id}_report.html"),
        extensions=extensions,
        labels=Labels(),
    )


def create_csv_report_system(
    id: str,
    name: str,
    csv_columns: List[str],
    *,
    score_column: str = "score",
    template_name: Optional[str] = None,
    description: str = "",
    author: str = "",
    theme: str = "dark",
) -> ReportSystemDefinition:
    """
    Create a report system for analyzing CSV data.
    
    Parameters:
        id: Unique identifier
        name: Display name
        csv_columns: List of column names in the CSV
        score_column: Which column contains the primary score
        template_name: Optional custom template
        description: Optional description
        author: Optional author
        theme: Default theme ID
    
    Returns:
        ReportSystemDefinition for CSV analysis
    
    Example:
        system = create_csv_report_system(
            id="sales_report",
            name="Sales Report",
            csv_columns=["product", "revenue", "quantity", "date"],
            score_column="revenue",
        )
    """
    # Build fields from column names
    fields = {}
    for col in csv_columns:
        if col == score_column:
            fields[col] = {"type": "float", "required": True}
        elif "date" in col.lower() or "time" in col.lower():
            fields[col] = {"type": "integer", "required": False}
        else:
            fields[col] = {"type": "string", "required": False}
    
    # Default template if not provided
    if template_name is None:
        template_name = f"{id}/pages/home.html.j2"
    
    return create_simple_report_system(
        id=id,
        name=name,
        data_parser_type=f"{id}_csv",
        template_name=template_name,
        description=description,
        author=author,
        fields=fields,
        primary_metrics=[score_column],
        theme=theme,
        charts=[
            {"id": "main_chart", "type": "bar", "title": f"{score_column.title()} Comparison"}
        ],
    )


def create_multi_page_report_system(
    id: str,
    name: str,
    data_parser_type: str,
    pages: List[Dict[str, Any]],
    *,
    description: str = "",
    author: str = "",
    fields: Optional[Dict[str, Dict[str, Any]]] = None,
    theme: str = "dark",
) -> ReportSystemDefinition:
    """
    Create a multi-page report system.
    
    Parameters:
        id: Unique identifier
        name: Display name
        data_parser_type: Parser type
        pages: List of page definitions, each with:
            - id: Page ID
            - filename: Output filename
            - template: Template name
            - nav_label: Navigation label
            - charts: Optional list of charts
        description: Optional description
        author: Optional author
        fields: Field definitions
        theme: Default theme ID
    
    Returns:
        ReportSystemDefinition with multiple pages
    
    Example:
        system = create_multi_page_report_system(
            id="analytics",
            name="Analytics Report",
            data_parser_type="analytics_csv",
            pages=[
                {"id": "overview", "filename": "index.html", "template": "...", "nav_label": "Overview"},
                {"id": "details", "filename": "details.html", "template": "...", "nav_label": "Details"},
            ],
        )
    """
    # Default fields
    if fields is None:
        fields = {
            "name": {"type": "string", "required": True},
            "score": {"type": "float", "required": True},
            "timestamp": {"type": "integer", "required": False},
        }
    
    # Convert field dicts to FieldConfig
    field_configs = {}
    for field_name, field_def in fields.items():
        field_configs[field_name] = FieldConfig(
            type=field_def.get("type", "string"),
            required=field_def.get("required", False),
        )
    
    # Build page configs
    page_configs = []
    for i, page in enumerate(pages, 1):
        chart_configs = []
        for chart in page.get("charts", []):
            chart_configs.append(ChartConfig(
                id=chart.get("id", f"chart_{i}"),
                type=chart.get("type", "bar"),
                title=chart.get("title", "Chart"),
            ))
        
        page_configs.append(PageConfig(
            id=page["id"],
            filename=page["filename"],
            nav_label=page.get("nav_label", page["id"].title()),
            nav_order=i,
            template=TemplateConfig(type="jinja2", name=page["template"]),
            charts=chart_configs,
            enabled=True,
        ))
    
    return ReportSystemDefinition(
        schema_version="1.0",
        id=id,
        name=name,
        version="1.0.0",
        description=description,
        author=author,
        data_source=DataSourceConfig(
            type=data_parser_type,
            input_format="csv",
            fields=field_configs,
        ),
        llm_config=LLMConfig(),
        llm_generators=[],
        theme=ThemeConfig(preset=theme),
        pages=page_configs,
        output=OutputConfig(default_filename=f"{id}_report.html"),
        extensions={},
        labels=Labels(),
    )

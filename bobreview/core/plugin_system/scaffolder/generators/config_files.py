"""
Configuration file generators for plugin scaffolding.

Generates JSON/configuration structures:
- manifest.json
- report_system.json
"""

from typing import Dict, Any, Literal


def generate_manifest(
    name: str,
    safe_name: str,
    class_name: str,
    template: Literal['minimal', 'full']
) -> Dict[str, Any]:
    """Generate manifest.json content as a dictionary."""
    manifest = {
        "name": name,
        "version": "1.0.0",
        "author": "Your Name",
        "description": f"Plugin for {name}",
        "entry_point": f"plugin:{class_name}Plugin",
        "dependencies": [],
        "provides": {
            "report_systems": [safe_name],
            "data_parsers": [f"{safe_name}_csv"],
        }
    }
    
    if template == 'full':
        manifest["provides"]["context_builders"] = [safe_name]
        manifest["provides"]["chart_generators"] = [safe_name]
    
    return manifest


def generate_report_system(name: str, safe_name: str, color_theme: str = 'dark') -> Dict[str, Any]:
    """Generate report system JSON with theme preset support."""
    return {
        "schema_version": "1.0",
        "id": safe_name,
        "name": f"{name} Report",
        "version": "1.0.0",
        "description": f"Report system for {name}",
        "author": "Your Name",
        
        "data_source": {
            "type": f"{safe_name}_csv",
            "input_format": "csv",
            "fields": {
                "name": {"type": "string", "required": True},
                "score": {"type": "float", "required": True},
                "category": {"type": "string", "required": False}
            }
        },
        
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2000,
            "chunk_size": 10
        },
        
        "llm_generators": [
            {
                "id": "summary",
                "name": "Summary",
                "description": "Executive summary of the data analysis",
                "prompt_template": f"Analyze this {name} data and provide a brief executive summary. Highlight key trends, outliers, and notable patterns.",
                "data_table": {
                    "columns": ["name", "score"],
                    "sample_strategy": "all",
                    "max_rows": 50
                },
                "returns": "string",
                "enabled": True
            },
            {
                "id": "recommendations",
                "name": "Recommendations",
                "description": "Actionable recommendations based on the data",
                "prompt_template": f"Based on this {name} data, provide 3-5 actionable recommendations for improvement.",
                "data_table": {
                    "columns": ["name", "score"],
                    "sample_strategy": "all",
                    "max_rows": 50
                },
                "returns": "string",
                "enabled": True
            }
        ],
        
        "theme": {
            "preset": color_theme  # dark, ocean, purple, terminal, sunset
        },
        
        "pages": [
            {
                "id": "home",
                "filename": "index.html",
                "nav_label": "Overview",
                "nav_order": 1,
                "template": {
                    "type": "jinja2",
                    "name": f"{safe_name}/pages/home.html.j2"
                },
                "llm_content": ["summary", "recommendations"],
                "llm_mappings": {
                    "summary": "summary",
                    "recommendations": "recommendations"
                },
                "charts": [
                    {
                        "id": "score_chart",
                        "type": "bar",
                        "title": "Score Comparison",
                        "x_field": "name",
                        "y_field": "score"
                    }
                ],
                "data_requirements": {
                    "data_points": False,
                    "images": False
                },
                "enabled": True
            },
            {
                "id": "details",
                "filename": "details.html",
                "nav_label": "Details",
                "nav_order": 2,
                "card_icon": "fa-chart-bar",
                "card_description": "Detailed statistics and full data table.",
                "template": {
                    "type": "jinja2",
                    "name": f"{safe_name}/pages/details.html.j2"
                },
                "charts": [
                    {
                        "id": "distribution_chart",
                        "type": "histogram",
                        "title": "Score Distribution",
                        "y_field": "score"
                    }
                ],
                "data_requirements": {
                    "data_points": True,
                    "images": False
                },
                "enabled": True
            }
        ],
        
        "output": {
            "default_filename": f"{safe_name}_report.html"
        }
    }

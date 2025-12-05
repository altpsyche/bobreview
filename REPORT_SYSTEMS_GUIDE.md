# BobReview Report Systems Guide

**Version:** 1.0.4  
**Last Updated:** December 5, 2025

---

## Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [JSON Schema Reference](#json-schema-reference)
- [Creating Custom Report Systems](#creating-custom-report-systems)
- [Template Variables](#template-variables)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Introduction

BobReview v1.0.4 introduces a powerful JSON-based report system framework that allows you to create custom report generation pipelines without modifying code. Each report system is defined by a single JSON file that specifies:

- **Data Source:** How to parse input files
- **Metrics:** What to measure and analyze
- **LLM Generators:** AI-powered content generation
- **Pages:** HTML report structure
- **Configuration:** Thresholds, themes, and output options

### Benefits

- **Flexibility:** Support any data format and metrics
- **Reusability:** Share report systems across teams
- **Version Control:** Track report definitions in git
- **No Coding:** Create new analysis types without Python
- **Domain-Specific:** Tailor reports to your exact needs

---

## Quick Start

### Using Built-in Systems

List available report systems:
```bash
bobreview --list-report-systems
```

Use a specific system:
```bash
bobreview --report-system png_data_points --dir ./screenshots
```

### Creating Your First Custom System

1. **Copy the template:**
```bash
mkdir -p ~/.bobreview/report_systems
cp bobreview/report_systems/builtin/png_data_points.json ~/.bobreview/report_systems/my_system.json
```

2. **Edit the JSON:**
```json
{
  "id": "my_system",
  "name": "My Custom Analysis",
  "description": "Custom performance analysis",
  ...
}
```

3. **Use it:**
```bash
bobreview --report-system my_system --dir ./data
```

---

## JSON Schema Reference

### Top-Level Structure

```json
{
  "schema_version": "1.0",
  "id": "system_id",
  "name": "System Name",
  "version": "1.0.0",
  "description": "System description",
  "author": "Your Name",
  "tags": ["tag1", "tag2"],
  
  "data_source": {...},
  "metrics": {...},
  "thresholds": {...},
  "llm_config": {...},
  "llm_generators": [...],
  "pages": [...],
  "theme": {...},
  "output": {...}
}
```

### Data Source Configuration

#### Filename Pattern Parser

Extracts data from filename patterns:

```json
{
  "data_source": {
    "type": "filename_pattern",
    "input_format": "png",
    "pattern": "{field1}_{field2}_{field3}.ext",
    "fields": {
      "field1": {
        "type": "string",
        "required": true
      },
      "field2": {
        "type": "integer",
        "required": true,
        "min": 0
      }
    },
    "validation": {
      "allow_missing_fields": false,
      "skip_invalid": true,
      "strict_mode": false
    }
  }
}
```

**Field Types:**
- `string` - Text values
- `integer` - Whole numbers
- `float` - Decimal numbers
- `boolean` - True/false values

**Field Options:**
- `required` - Must be present (default: true)
- `min` - Minimum value (numeric types)
- `max` - Maximum value (numeric types)
- `pattern` - Regex pattern (string type)
- `default` - Default value if missing

### Metrics Configuration

```json
{
  "metrics": {
    "primary": ["metric1", "metric2"],
    "derived": [
      {
        "id": "derived_metric",
        "description": "Description",
        "calculation": "expression"
      }
    ],
    "statistics": {
      "basic": ["min", "max", "mean", "median", "stdev"],
      "advanced": ["p90", "p95", "p99", "variance", "cv"],
      "analysis": ["confidence_interval", "trend", "outliers"]
    }
  }
}
```

### Thresholds

Define performance thresholds:

```json
{
  "thresholds": {
    "metric_soft_cap": 100,
    "metric_hard_cap": 150,
    "high_load_threshold": 150,
    "low_load_threshold": 50
  }
}
```

### LLM Configuration

```json
{
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 2000,
    "chunk_size": 10,
    "enable_cache": true
  }
}
```

### LLM Generators

Define AI-powered content generation:

```json
{
  "llm_generators": [
    {
      "id": "generator_id",
      "name": "Generator Name",
      "description": "What this generates",
      "prompt_template": "Your prompt with {variables}...",
      "categories": [
        {
          "id": "cat1",
          "title": "Category Title",
          "focus": "What to focus on",
          "priority": 10
        }
      ],
      "data_table": {
        "columns": ["col1", "col2"],
        "sample_strategy": "mixed",
        "samples": {
          "critical": 1,
          "high_load": 3,
          "random": 5
        },
        "max_rows": 50
      },
      "returns": "string",
      "enabled": true
    }
  ]
}
```

**Sample Strategies:**
- `all` - Use all data points
- `random` - Random sampling
- `sequential` - First N points
- `mixed` - Combination of critical, high-load, low-load, and random

**Returns:**
- `string` - Single HTML string
- `dict` - Dictionary of sections

### Pages Configuration

Define HTML pages:

```json
{
  "pages": [
    {
      "id": "page_id",
      "filename": "page.html",
      "nav_label": "Page Label",
      "nav_order": 10,
      "template": {
        "type": "builtin",
        "name": "template_name"
      },
      "llm_content": ["generator_id1", "generator_id2"],
      "data_requirements": {
        "stats": true,
        "data_points": false,
        "images": false
      },
      "charts": [
        {
          "id": "chart_id",
          "type": "line",
          "title": "Chart Title",
          "x_field": "field1",
          "y_field": "field2",
          "performance_zones": {
            "good": {"max": "threshold1", "color": "green"},
            "warning": {"min": "threshold1", "max": "threshold2", "color": "yellow"},
            "critical": {"min": "threshold2", "color": "red"}
          }
        }
      ],
      "enabled": true
    }
  ]
}
```

**Chart Types:**
- `line` - Line chart
- `bar` - Bar chart
- `scatter` - Scatter plot
- `histogram` - Distribution histogram

### Theme Configuration

```json
{
  "theme": {
    "default": "dark",
    "override_colors": {
      "accent": "#ff0000"
    }
  }
}
```

**Available Themes:**
- `dark` (default)
- `light`
- `high_contrast`

### Output Configuration

```json
{
  "output": {
    "default_filename": "report.html",
    "embed_images": true,
    "linked_css": false
  }
}
```

---

## Creating Custom Report Systems

### Example: CSV Performance Metrics

```json
{
  "schema_version": "1.0",
  "id": "csv_metrics",
  "name": "CSV Performance Metrics",
  "version": "1.0.0",
  "description": "Analyze performance metrics from CSV files",
  "author": "Your Team",
  
  "data_source": {
    "type": "csv",
    "input_format": "csv",
    "header_row": 0,
    "column_mapping": {
      "timestamp": "Time",
      "cpu_usage": "CPU %",
      "memory_usage": "Memory %",
      "response_time": "Response Time (ms)"
    },
    "validation": {
      "skip_invalid": true
    }
  },
  
  "metrics": {
    "primary": ["cpu_usage", "memory_usage", "response_time"],
    "statistics": {
      "basic": ["min", "max", "mean", "median", "stdev"],
      "advanced": ["p90", "p95", "p99"]
    }
  },
  
  "thresholds": {
    "cpu_soft_cap": 70,
    "cpu_hard_cap": 90,
    "memory_soft_cap": 75,
    "memory_hard_cap": 95,
    "response_time_soft_cap": 200,
    "response_time_hard_cap": 500
  },
  
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7
  },
  
  "llm_generators": [
    {
      "id": "summary",
      "name": "Performance Summary",
      "prompt_template": "Analyze this system performance data...",
      "categories": [
        {"id": "cpu", "title": "CPU Analysis", "focus": "usage patterns", "priority": 10},
        {"id": "memory", "title": "Memory Analysis", "focus": "memory trends", "priority": 20}
      ]
    }
  ],
  
  "pages": [
    {
      "id": "dashboard",
      "filename": "index.html",
      "nav_label": "Dashboard",
      "nav_order": 10,
      "template": {"type": "builtin", "name": "homepage"},
      "llm_content": ["summary"]
    }
  ],
  
  "theme": {"default": "dark"},
  "output": {"default_filename": "performance_dashboard.html"}
}
```

---

## Template Variables

Use template variables in prompt templates to inject dynamic data:

### Available Variables

#### Stats Variables
```
{stats.count}                    - Number of samples
{stats.draws.mean}              - Mean draw calls
{stats.draws.median}            - Median draw calls
{stats.draws.p90}               - 90th percentile
{stats.draws.p95}               - 95th percentile
{stats.draws.p99}               - 99th percentile
{stats.draws.cv}                - Coefficient of variation
{stats.confidence_intervals.draws.0}  - CI lower bound
{stats.confidence_intervals.draws.1}  - CI upper bound
{stats.trends.draws.direction}  - Trend direction
```

#### Context Variables
```
{context.location}              - Report location
{context.title}                 - Report title
{context.draw_hard_cap}         - Threshold values
{context.tri_hard_cap}
```

#### Special Variables
```
{categories}                    - Auto-generated category list
```

### Example Prompt with Variables

```json
{
  "prompt_template": "Analyze performance for {context.location}.\n\nKey Metrics:\n- Samples: {stats.count}\n- Mean draws: {stats.draws.mean}\n- P95 draws: {stats.draws.p95}\n- Trend: {stats.trends.draws.direction}\n\nProvide analysis covering:\n{categories}"
}
```

---

## Examples

### Minimal Report System

```json
{
  "schema_version": "1.0",
  "id": "minimal",
  "name": "Minimal Report",
  "version": "1.0.0",
  "description": "Simplest possible report system",
  "author": "You",
  
  "data_source": {
    "type": "filename_pattern",
    "input_format": "txt",
    "pattern": "{name}_{value}.txt",
    "fields": {
      "name": {"type": "string"},
      "value": {"type": "integer", "min": 0}
    }
  },
  
  "metrics": {
    "primary": ["value"]
  },
  
  "thresholds": {},
  
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  
  "llm_generators": [
    {
      "id": "summary",
      "name": "Summary",
      "prompt_template": "Summarize this data: {stats.count} samples, mean value: {stats.value.mean}"
    }
  ],
  
  "pages": [
    {
      "id": "home",
      "filename": "index.html",
      "nav_label": "Home",
      "nav_order": 10,
      "template": {"type": "builtin", "name": "homepage"},
      "llm_content": ["summary"]
    }
  ],
  
  "theme": {"default": "dark"},
  "output": {"default_filename": "report.html"}
}
```

---

## Best Practices

### 1. Descriptive IDs and Names
Use clear, descriptive identifiers:
```json
{
  "id": "web_server_performance",  // Good
  "name": "Web Server Performance Analysis"
}
```

### 2. Comprehensive Validation
Define strict field validation:
```json
{
  "fields": {
    "response_time": {
      "type": "float",
      "required": true,
      "min": 0,
      "max": 60000
    }
  }
}
```

### 3. Meaningful Categories
Structure LLM prompts with focused categories:
```json
{
  "categories": [
    {"id": "performance", "title": "Performance Assessment", "focus": "overall health"},
    {"id": "bottlenecks", "title": "Bottleneck Identification", "focus": "specific issues"},
    {"id": "recommendations", "title": "Recommendations", "focus": "actionable steps"}
  ]
}
```

### 4. Progressive Data Sampling
Use mixed sampling for large datasets:
```json
{
  "data_table": {
    "sample_strategy": "mixed",
    "samples": {
      "critical": 1,
      "high_load": 3,
      "low_load": 2,
      "random": 10
    },
    "max_rows": 50
  }
}
```

### 5. Version Your Systems
Track changes with semantic versioning:
```json
{
  "version": "1.2.0",
  "description": "Added memory analysis (v1.2.0)"
}
```

---

## Troubleshooting

### JSON Validation Errors

**Error:** `Missing required field: data_source`
**Solution:** Ensure all required top-level fields are present.

**Error:** `Unsupported schema version: 2.0`
**Solution:** Use `"schema_version": "1.0"`.

### Data Parsing Issues

**Error:** `No data points found after parsing`
**Solution:** Check your filename pattern matches actual files.

**Error:** `Invalid data in file: example.png`
**Solution:** Enable `skip_invalid` in validation config.

### LLM Generator Issues

**Error:** `Unknown page ID: custom_page`
**Solution:** Ensure page IDs match their configuration.

**Error:** `Variable not found: {stats.custom.field}`
**Solution:** Check variable path matches actual data structure.

### Performance Issues

**Problem:** Slow report generation
**Solutions:**
- Reduce `chunk_size` in llm_config
- Use `sample_strategy: "random"` with lower sample counts
- Enable caching with `"enable_cache": true`

---

## Advanced Topics

### Custom Data Parsers

While v1.0.4 includes built-in parsers, you can extend the system:

1. Create a Python module implementing `DataParser`
2. Register it with the framework
3. Reference it by type in JSON

(Full implementation guide coming in future version)

### Custom Page Templates

Future versions will support custom Jinja2 templates:

```json
{
  "template": {
    "type": "custom",
    "name": "my_template",
    "content": "path/to/template.html"
  }
}
```

---

## Support and Feedback

- **Issues:** https://github.com/DiggingNebula8/bobreview/issues
- **Documentation:** https://github.com/DiggingNebula8/bobreview
- **Examples:** `report_systems_examples/` directory

---

**Last Updated:** December 5, 2025  
**BobReview Version:** 1.0.4


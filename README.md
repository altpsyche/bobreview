# BobReview

**Extensible Report Generation Framework**

Generate comprehensive HTML reports from data using LLM-powered analysis. Plugins provide domain-specific parsing, analysis, and templates.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Report Systems](#report-systems)
- [File Format](#file-format)
- [Configuration](#configuration)
- [Report Structure](#report-structure)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Overview

BobReview is a plugin-based report generation framework. Plugins define:
- How to parse input data
- What metrics to analyze
- What analysis to perform
- What templates to use for HTML output

**Key Feature:** Sends structured data tables to the LLM instead of images, significantly reducing token usage and costs by approximately 90%.

---

## Features

- **Plugin System** - All domain-specific logic provided by plugins
- **JSON-Based Report Systems** - Define custom analysis pipelines with JSON
- **Multi-Provider LLM Support** - OpenAI, Anthropic Claude, or local Ollama
- **Extensible Data Parsing** - Plugins define how to extract data
- **Statistical Analysis** - Generic utilities for stats, outliers, trends
- **LLM-Powered Insights** - Generate contextual analysis using AI models
- **Professional Reports** - Generate presentation-ready HTML reports
- **Standalone HTML** - Images embedded as base64 for easy sharing
- **Intelligent Caching** - Cache LLM responses to reduce costs
- **Modular Architecture** - Clean packages with max 200 lines per file
- **Global CLI Command** - Run from any directory after installation

---

## Architecture

BobReview v1.0.7 uses a **fully modular plugin system** with focused architecture following SOLID and DRY principles:

```text
bobreview/
├── __init__.py        # Package entry
├── cli.py             # Command-line interface
│
├── core/              # Foundational utilities
│   ├── config.py      # ReportConfig (composes focused configs)
│   ├── config_classes.py  # Focused config classes (ThresholdConfig, LLMConfig, etc.)
│   ├── cache.py       # LLM response caching
│   ├── utils.py       # Logging, formatting
│   ├── analysis.py    # Statistics calculation
│   ├── template_engine.py  # Jinja2 template loading
│   ├── plugin_utils.py     # Plugin utility functions
│   ├── config_utils.py     # Config utility functions
│   └── plugin_system/      # Plugin infrastructure (v1.0.8)
│       ├── registry.py     # PluginRegistry (composes focused registries)
│       ├── base.py         # BasePlugin abstract class
│       ├── loader.py       # PluginLoader for discovery and loading
│       └── registries/     # Focused registries (11 files)
│
├── plugins/           # Actual plugin implementations
│   ├── my-plugin/     # Example plugin
│   │   ├── plugin.py  # Plugin class
│   │   ├── report_systems/
│   │   └── templates/
│   └── another-plugin/
│       ├── plugin.py
│       └── ...
│
├── services/          # Pluggable services
│   ├── container.py   # ServiceContainer
│   ├── data_service.py
│   ├── analytics_service.py
│   ├── chart_service.py
│   └── llm_service.py
│
├── report_systems/    # Report execution
│   ├── schema.py, loader.py, executor.py
│   ├── config_merger.py      # Config merging responsibility
│   ├── service_validator.py  # Service validation responsibility
│   └── plugin_lifecycle.py   # Plugin lifecycle responsibility
│
└── llm/               # LLM abstraction layer
    ├── client.py      # call_llm, call_llm_chunked
    ├── providers/     # Pluggable LLM providers
    └── generators/    # Content generators
```

**Design Principles:**
- **SOLID Principles** - Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY Principle** - Don't Repeat Yourself (extracted utilities, no code duplication)
- **Focused Interfaces** - Each registry/config handles one concern
- **Dependency Injection** - Dependencies passed explicitly (no global singletons)
- **Plugin-First** - All functionality provided by plugins
- **Registry Pattern** - Self-registration for all extension points

### Package Overview

| Package | Purpose |
|---------|---------|
| `core/plugin_system/` | Plugin infrastructure with 11 focused registries (themes, generators, parsers, etc.) |
| `core/plugin_system/registries/` | Focused registries following Interface Segregation Principle |
| `core/` | Configuration (focused config classes), caching, logging, analysis, utilities |
| `plugins/` | Actual plugin implementations (user-provided) |
| `services/` | Pluggable service container with data, analytics, charts, LLM |
| `report_systems/` | JSON-based pipeline configuration with focused responsibility classes |
| `llm/` | LLM providers (OpenAI/Anthropic/Ollama), generators |

### Focused Architecture Benefits

**Interface Segregation:**
- Clients only depend on registries/configs they need
- `registry.themes` for themes, `registry.llm_generators` for generators
- `config.thresholds` for thresholds, `config.llm` for LLM settings

**Dependency Injection:**
- No global singletons (better testability)
- Dependencies passed explicitly
- Easier to mock in tests

**Single Responsibility:**
- Each class has one clear purpose
- ConfigMerger merges config, ServiceValidator validates services
- Executor orchestrates, doesn't merge or validate

---

## Installation

### Quick Install (Recommended)

Install BobReview as a global CLI command:

```bash
# Clone the repository
git clone https://github.com/DiggingNebula8/bobreview.git
cd bobreview

# Install BobReview
pip install .

# Set up your OpenAI API key
# Linux/macOS:
export OPENAI_API_KEY=sk-your-api-key-here
# Windows PowerShell:
$env:OPENAI_API_KEY="sk-your-api-key-here"
# Windows Command Prompt:
set OPENAI_API_KEY=sk-your-api-key-here

# Run from any directory
cd /path/to/screenshots
bobreview --plugin <plugin-name> --dir .
```

**Alternative LLM Providers (v1.0.5):**
```bash
# Use Anthropic Claude
export ANTHROPIC_API_KEY=your-key
bobreview --plugin <plugin-name> --dir . --llm-provider anthropic

# Use local Ollama (no API key needed)
bobreview --plugin <plugin-name> --dir . --llm-provider ollama --llm-model llama2
```

After installation, the `bobreview` command is available globally.

### Development Install

For developers modifying BobReview:

```bash
# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

Changes to source code take effect immediately without reinstalling.

### Manual Install

Run without installing the package:

```bash
# Install dependencies only
pip install -r requirements.txt

# Run from source directory
python bobreview.py --plugin <plugin-name> --dir /path/to/screenshots
```

**Important:** When using `bobreview.py` directly:
- All features work normally
- Must run from the BobReview source directory
- The `bobreview` command is not available globally

**Example:**
```bash
# Must be in BobReview source directory
cd /path/to/bobreview-source

# Analyze any folder
python bobreview.py --plugin <plugin-name> --dir /path/to/screenshots

# Won't work from other directories
cd /some/other/directory
python bobreview.py --plugin <plugin-name> --dir .  # Error: file not found
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

---

## Quick Start

### 1. Install
```bash
pip install .
```

### 2. Set API Key
```bash
# Linux/macOS
export OPENAI_API_KEY=sk-your-api-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows Command Prompt
set OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run
```bash
cd /path/to/screenshots
bobreview --plugin <plugin-name> --dir .
```

### 4. View Report
```bash
open performance_report.html
```

See [QUICKSTART.md](QUICKSTART.md) for a complete guide.

---

## Usage

### Basic Usage

```bash
# Plugin is required
bobreview --plugin <plugin-name> --dir /path/to/screenshots

# With custom output
bobreview --plugin <plugin-name> --dir ./screenshots --output report.html

# Custom title and location
bobreview --plugin <plugin-name> --dir ./screenshots \
  --title "Forest Level Performance" \
  --location "Dark Forest Area"
```

### Common Operations

```bash
# Test without LLM API calls
bobreview --plugin <plugin-name> --dir ./screenshots --dry-run

# Process subset of data
bobreview --plugin <plugin-name> --dir ./screenshots --sample 20

# Verbose output
bobreview --plugin <plugin-name> --dir ./screenshots --verbose

# List available plugins
bobreview plugins list

# List available report systems
bobreview --list-report-systems
```

### Caching

Caching is enabled by default to reduce costs:

```bash
# First run - calls LLM and caches
bobreview --plugin <plugin-name> --dir ./screenshots

# Second run - uses cache (instant)
bobreview --plugin <plugin-name> --dir ./screenshots

# Clear cache and regenerate
bobreview --plugin <plugin-name> --dir ./screenshots --clear-cache

# Disable caching
bobreview --plugin <plugin-name> --dir ./screenshots --no-cache
```

### Standalone HTML Reports

BobReview creates self-contained HTML files with embedded images:

```bash
# Generate standalone HTML
bobreview --plugin <plugin-name> --dir ./screenshots

# Result: Single HTML file you can share without image folder
# Perfect for email attachments or sharing via messaging apps
```

To use external image files instead (reduces HTML file size):

```bash
# Use the --no-embed-images flag
bobreview --plugin <plugin-name> --dir ./screenshots --no-embed-images
```

**Note:** Embedded images increase HTML file size but eliminate external dependencies, making sharing much easier.

### Python API

#### Basic Usage

```python
from bobreview import ReportConfig
from bobreview.report_systems import load_report_system, ReportSystemExecutor
from pathlib import Path

# Create configuration with focused config classes
config = ReportConfig(
    title="Performance Analysis",
    location="Test Level",
)

# Configure thresholds
config.thresholds.draw_soft_cap = 550
config.thresholds.draw_hard_cap = 600
config.thresholds.tri_soft_cap = 100000
config.thresholds.tri_hard_cap = 120000

# Configure LLM settings
config.llm.provider = "openai"
config.llm.api_key = "sk-..."
config.llm.model = "gpt-4o"
config.llm.temperature = 0.7

# Configure execution
config.execution.dry_run = False
config.execution.verbose = True
config.execution.sample_size = None

# Configure output
config.output.theme_id = "dark"
config.output.embed_images = True

# Load report system and execute
system_def = load_report_system("png_data_points")
executor = ReportSystemExecutor(system_def, config)
executor.execute(Path("./screenshots"), Path("report.html"))
```

#### Plugin API

Create a custom plugin:

```python
from bobreview.core.plugin_system import BasePlugin
from bobreview.core.themes import ReportTheme

class MyCustomPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    author = "Your Name"
    description = "Custom plugin with themes and generators"
    dependencies = []
    
    def on_load(self, registry) -> None:
        """Register plugin components using focused registries."""
        
        # Register a theme
        custom_theme = ReportTheme(
            id="custom",
            name="Custom Theme",
            primary_color="#FF5733",
            secondary_color="#33FF57",
            # ... other theme properties
        )
        registry.themes.register(custom_theme, plugin_name=self.name)
        
        # Register an LLM generator
        def generate_custom_content(llm_provider, data_points, stats, context, dry_run, report_config):
            # Your generator logic here
            return "Custom content"
        
        class CustomGenerator:
            @staticmethod
            def generate(llm_provider, data_points, stats, context, dry_run, report_config):
                return generate_custom_content(llm_provider, data_points, stats, context, dry_run, report_config)
        
        registry.llm_generators.register(CustomGenerator, plugin_name=self.name)
        
        # Register a data parser
        def parse_custom_format(file_path):
            # Your parser logic here
            return {"data": "parsed"}
        
        registry.data_parsers.register("custom_format", parse_custom_format, plugin_name=self.name)
        
        # Register a report system
        system_def = {
            "id": "my_system",
            "name": "My Custom System",
            "version": "1.0.0",
            # ... system definition
        }
        registry.report_systems.register("my_system", system_def, plugin_name=self.name)
        
        # Register template paths
        template_path = Path(__file__).parent / "templates"
        registry.template_paths.register(template_path, plugin_name=self.name, priority=50)
```

#### Accessing Registry Components

```python
from bobreview.core.plugin_system import get_registry

registry = get_registry()

# Get themes
theme = registry.themes.get("dark")
all_themes = registry.themes.get_all()

# Get LLM generators
generator = registry.llm_generators.get("summary")
all_generators = registry.llm_generators.get_all()

# Get data parsers
parser = registry.data_parsers.get("png_filename")
all_parsers = registry.data_parsers.get_all()

# Get report systems
system = registry.report_systems.get("png_data_points")
all_systems = registry.report_systems.get_all()

# Get template paths
paths = registry.template_paths.get_paths()
```

#### Config API

```python
from bobreview import ReportConfig

config = ReportConfig()

# Access focused config classes
config.thresholds.draw_soft_cap = 600
config.thresholds.tri_hard_cap = 120000

config.llm.provider = "openai"
config.llm.model = "gpt-4o"
config.llm.temperature = 0.7

config.execution.dry_run = False
config.execution.verbose = True
config.execution.sample_size = 100

config.output.theme_id = "dark"
config.output.embed_images = True
config.output.disabled_pages = ["stats"]

config.cache.cache_dir = Path(".cache")
config.cache.clear_cache = False
```

---

## Report Systems

**NEW in v1.0.4:** BobReview now supports JSON-based report system definitions, allowing you to create custom analysis pipelines without modifying code.

### What are Report Systems?

Report systems are JSON files that define:
- How to parse input data
- What metrics to analyze
- What LLM-generated insights to include
- What pages to generate
- How to theme and configure the output

### Using Plugins (Recommended)

Plugins provide report systems, templates, and generators. A plugin can provide **multiple report systems**. Use `--plugin` to select a plugin:

```bash
# Use plugin (uses default report system - first one alphabetically)
bobreview --plugin <plugin-name> --dir ./screenshots

# Explicitly specify which report system from plugin (useful when plugin has multiple)
bobreview --plugin <plugin-name> --report-system <system-id> --dir ./screenshots

# If plugin has multiple systems, select a different one
bobreview --plugin <plugin-name> --report-system <system-id> --dir ./data

# Example with different plugin
bobreview --plugin <plugin-name> --dir ./game_data
```

**Note:** 
- If a plugin has **only one** report system, it's automatically selected when using `--plugin`.
- If a plugin has **multiple** report systems, you **must** specify `--report-system` to choose which one to use.

#### List Available Systems
```bash
# List available plugins
bobreview plugins list

# List available report systems
bobreview --list-report-systems
```

Output:
```
Available report systems:

  system_1 (plugin:my-plugin) - v1.0.0
    Description of what this system does
    Path: plugin:my-plugin

  system_2 (plugin:my-plugin) - v1.0.0
    Another report system description
    Path: plugin:my-plugin
```

#### Custom Report Systems
```bash
# Custom report systems can be placed in ~/.bobreview/report_systems/
# They can be accessed via a plugin or directly by specifying the JSON file path

# Use a custom JSON file directly
bobreview --plugin <plugin-name> --report-system /path/to/custom_system.json --dir ./data
```

### Creating Custom Report Systems

1. **Create a JSON file** in `~/.bobreview/report_systems/`:

```json
{
  "schema_version": "1.0",
  "id": "my_system",
  "name": "My Custom Analysis",
  "version": "1.0.0",
  "description": "Custom performance analysis",
  "author": "Your Name",
  
  "data_source": {
    "type": "filename_pattern",
    "input_format": "csv",
    "pattern": "{timestamp}_{metric}_{value}.csv",
    "fields": {...}
  },
  
  "metrics": {...},
  "thresholds": {...},
  "llm_generators": [...],
  "pages": [...]
}
```

2. **Use it:**
```bash
# Plugin is required
bobreview --plugin my_plugin --report-system my_system --dir ./data

# Or if it's a standalone JSON file
bobreview --plugin <plugin-name> --report-system /path/to/my_system.json --dir ./data
```

### Built-in Report Systems

#### png_data_points (Default)

Analyzes game performance from PNG filename metadata.

**Pattern:** `{testcase}_{tris}_{draws}_{timestamp}.png`  
**Example:** `Level1_85000_520_1234567890.png`

**Features:**
- Triangle count and draw call analysis
- Performance zone identification
- Trend detection
- Outlier analysis (3 methods)
- Interactive Chart.js visualizations
- 6 HTML pages with AI-generated insights

### Report System Capabilities

- **Flexible Data Sources:** Parse any file format with custom patterns
- **Custom Metrics:** Define primary and derived metrics
- **Configurable LLM:** Custom prompts, categories, and sampling strategies
- **Dynamic Pages:** Define custom page layouts and navigation
- **Theme Support:** Use built-in themes or create custom ones
- **Reusable:** Share report systems across teams

### Documentation

See **[REPORT_SYSTEMS_GUIDE.md](REPORT_SYSTEMS_GUIDE.md)** for:
- Complete JSON schema reference
- Creating custom report systems
- Template variable reference
- Examples and best practices

---

## File Format

BobReview expects PNG files with performance data encoded in the filename:

### Format

```text
TestCase_tricount_drawcalls_timestamp.png
```

### Example

```text
Level1_85000_520_1234567890.png
```

**Components:**
- `Level1` - Test case or level name
- `85000` - Triangle count (integer)
- `520` - Draw call count (integer)
- `1234567890` - Unix timestamp (integer)

### Valid Examples

```text
ForestArea_95000_580_1701234567.png
City_120000_650_1701234568.png
Boss_85000_520_1701234569.png
```

### Invalid Examples

```text
screenshot.png                    # Missing data
Level1_85000_520.png             # Missing timestamp
Level1_abc_520_1234567890.png   # Non-numeric values
```

---

## Configuration

### Command-Line Options

**Essential:**
```bash
--dir PATH              # Directory with PNG files
--output FILE           # Output HTML filename
--title TEXT            # Report title
--location TEXT         # Level/scene name
```

**Performance Thresholds:**
```bash
--draw-soft-cap N       # Soft limit for draw calls (default: 550)
--draw-hard-cap N       # Hard limit for draw calls (default: 600)
--tri-soft-cap N        # Soft limit for triangles (default: 100000)
--tri-hard-cap N        # Hard limit for triangles (default: 120000)
--high-load-draws N     # High-load threshold for draws
--high-load-tris N      # High-load threshold for triangles
--low-load-draws N      # Low-load threshold for draws (default: 400)
--low-load-tris N       # Low-load threshold for triangles (default: 50000)
--outlier-sigma N       # Outlier detection sigma (default: 2.0)
```

**LLM Provider Configuration (v1.0.5):**
```bash
--llm-provider PROVIDER # Provider: openai, anthropic, ollama (default: openai)
--llm-api-key KEY       # API key for the selected provider
--llm-api-base URL      # Custom API endpoint (e.g., for Ollama)
--llm-model MODEL       # Model name (default depends on provider)
--llm-temperature N     # Temperature 0-2 (default: 0.7)
--llm-max-tokens N      # Maximum tokens for LLM responses (default: 2000)
--llm-chunk-size N      # Samples per LLM call (default: 10)
--list-providers        # List available LLM providers
--no-recommendations    # Disable system recommendations
```

**Caching:**
```bash
--cache-dir PATH        # Cache directory (default: .bobreview_cache)
--use-cache            # Use cached responses (default: enabled)
--no-cache             # Disable caching
--clear-cache          # Clear cache before run
```

**Execution:**
```bash
--dry-run              # Skip LLM calls
--sample N             # Process N random samples
--verbose, -v          # Detailed output
--quiet, -q            # Errors only
--no-embed-images      # Use external image files
--linked-css           # Use external CSS file (styles.css)
--disable-page ID      # Disable a page (home, metrics, zones, visuals, optimization, stats)
--version              # Show version
--help                 # Show help
```

---

## Report Structure

Generated HTML reports include:

### 1. Executive Summary
- Overall performance assessment
- Key metrics overview
- Peak hotspot identification
- Variance analysis

### 2. Metric Deep Dive
- Draw calls analysis (min, max, mean, median, quartiles, std dev)
- Triangle count analysis
- Temporal behavior analysis
- Correlation analysis

### 3. Performance Zones and Hotspots
- High-load frame identification
- Low-load baseline frames
- Pattern analysis
- Common characteristics

### 4. Optimization Checklist
- Critical hotspot analysis
- High-geometry optimization recommendations
- High-draw call optimization strategies
- Actionable next steps

### 5. System-Level Recommendations (Optional)
- LOD system improvements
- Occlusion and visibility optimizations
- Lighting and shadow strategies
- Material and texture recommendations

### 6. Statistical Summary
- Complete statistical breakdown
- Distribution analysis
- Outlier identification

### 7. Full Sample Table
- All captures with thumbnails
- Sortable data table
- Complete traceability

---

## Performance Optimization

### Token Efficiency
- Sends structured data tables instead of images
- Reduces token usage by approximately 90% vs image analysis
- Lower costs per analysis

### Caching Strategy
- Enabled by default (directory: `.bobreview_cache/`)
- Subsequent runs with same data are instant
- Cache invalidated automatically on data/config changes
- Significant cost savings on repeated analyses

### Chunked Processing
- Large datasets processed in chunks (default: 10 samples)
- Prevents API rate limits
- Better token management

### Cost Optimization

```bash
# Use cache (default behavior)
bobreview --plugin <plugin-name> --dir ./screenshots

# Test with dry-run
bobreview --plugin <plugin-name> --dir ./screenshots --dry-run

# Use sampling for quick tests
bobreview --plugin <plugin-name> --dir ./screenshots --sample 20

# Adjust chunk size if needed
bobreview --plugin <plugin-name> --dir ./screenshots --llm-chunk-size 5
```

---

## Troubleshooting

### Command Not Found

**Error:** `bobreview: command not found`

**Solutions:**
```bash
# Reinstall
pip install .

# Or use Python module syntax
python -m bobreview.cli --plugin <plugin-name> --dir ./screenshots

# Or use script directly
cd /path/to/bobreview-source
python bobreview.py --plugin <plugin-name> --dir /path/to/screenshots
```

### API Key Not Found

**Error:** `OpenAI API key not found`

**Solutions:**
```bash
# Set environment variable (Linux/macOS)
export OPENAI_API_KEY=sk-your-api-key-here

# Set environment variable (Windows PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Set environment variable (Windows Command Prompt)
set OPENAI_API_KEY=sk-your-api-key-here

# Or use command-line argument (all platforms)
bobreview --plugin <plugin-name> --dir ./screenshots --llm-api-key sk-your-api-key-here

# Add to shell profile for persistence (Linux/macOS)
echo 'export OPENAI_API_KEY=sk-your-key' >> ~/.bashrc
```

### No PNG Files Found

**Error:** `No PNG files found`

**Solutions:**
- Verify PNG files exist in directory
- Check filename format: `TestCase_tricount_drawcalls_timestamp.png`
- Ensure correct directory path

### Invalid Filename Format

**Error:** `Invalid filename format`

**Solutions:**
- Use correct format: `TestCase_tricount_drawcalls_timestamp.png`
- All numeric fields must be integers
- All values must be non-negative
- File must have `.png` extension

### Configuration Validation Failed

**Error:** `Configuration validation failed`

**Solutions:**
- Ensure `draw_soft_cap <= draw_hard_cap`
- Ensure `tri_soft_cap <= tri_hard_cap`
- Ensure `outlier_sigma > 0`
- Ensure `llm_temperature` between 0 and 2

### Slow Performance

First run with LLM API calls takes time. This is normal.

**Solutions:**
- Subsequent runs use cache and are instant
- Use `--sample N` for quick testing
- Use `--dry-run` to test configuration

### High API Costs

**Prevention:**
- Cache is enabled by default
- Test with `--dry-run` first
- Use `--sample` for testing
- Only use `--clear-cache` when necessary

---

## Requirements

### Python
- Python 3.7 or higher
- Tested on Python 3.8, 3.9, 3.10, 3.11, 3.12

### Dependencies
**Required:**
- `openai>=1.0.0,<2.0.0` - OpenAI API client

**Optional (Recommended):**
- `tqdm>=4.65.0,<5.0.0` - Progress bars
- `colorama>=0.4.6,<1.0.0` - Colored terminal output

### System
- Internet connection for LLM API calls
- OpenAI API key
- Approximately 50MB disk space

---

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[ROADMAP.md](ROADMAP.md)** - Future plans and features
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

---

## Examples

### Basic Workflow
```bash
# Install
pip install .

# Set API key (choose based on your platform)
export OPENAI_API_KEY=sk-your-key              # Linux/macOS
$env:OPENAI_API_KEY="sk-your-key"              # Windows PowerShell
set OPENAI_API_KEY=sk-your-key                 # Windows Command Prompt

# Run analysis
cd /path/to/screenshots
bobreview --plugin <plugin-name> --dir .

# Open report
open performance_report.html                   # macOS
start performance_report.html                  # Windows
xdg-open performance_report.html               # Linux
```

### CI/CD Integration
```yaml
# .github/workflows/performance.yml
name: Performance Analysis
on: [push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install BobReview
        run: pip install .
      - name: Analyze Performance
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: bobreview --plugin <plugin-name> --dir ./captures --output report.html
```
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: performance-report
          path: report.html
```

---

## Contributing

Contributions are welcome. To contribute:

1. Check [ROADMAP.md](ROADMAP.md) for planned features
2. Create a branch: `git checkout -b feature-name`
3. Make changes in appropriate module
4. Test thoroughly
5. Submit pull request

### Development Setup

```bash
git clone https://github.com/DiggingNebula8/bobreview.git
cd bobreview
pip install -e ".[dev]"
```

### Adding New Report Pages

BobReview uses a modular page registry system. To add a new page:

**1. Create a new page module** in `bobreview/report_generator/`:

```python
# bobreview/report_generator/custom_page.py
"""Custom analysis page."""

from typing import Dict, List, Any
from .base import get_html_template, get_page_header, sanitize_llm_html
from .registry import register_page, PageDefinition, get_nav_items


def generate_custom_page(
    stats: Dict[str, Any],
    config,
    custom_content: str
) -> str:
    """Generate the custom analysis page."""
    nav_items = get_nav_items('custom.html')
    header = get_page_header("Custom Analysis", f"{stats['count']} captures", nav_items)
    
    body_content = f"""{header}
    <section class="panel">
      <h2>Custom Analysis</h2>
      {sanitize_llm_html(custom_content)}
    </section>
"""
    return get_html_template(f"{config.title} - Custom", body_content, linked_css=config.output.linked_css)


# Register the page
register_page(PageDefinition(
    id='custom',
    filename='custom.html',
    nav_label='Custom',
    nav_order=70,  # After stats (60)
    llm_section='Custom Analysis',
    page_generator=generate_custom_page,
    requires_images=False,
    requires_data_points=False
))
```

**2. Import the module** in `bobreview/report_generator/__init__.py`:

```python
# Add with other imports
from . import custom_page
```

**3. Add LLM generator** (optional) in `bobreview/llm_provider.py` if you need AI-generated content.

**4. Done!** Navigation auto-updates and the page is generated with all reports.

**Page Definition Fields:**

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (used with `--disable-page`) |
| `filename` | Output HTML filename |
| `nav_label` | Navigation menu label |
| `nav_order` | Sort order (10=Home, 20=Metrics, etc.) |
| `llm_section` | LLM content key from `llm_provider.py` |
| `page_generator` | Function that returns HTML |
| `requires_images` | Whether page needs image data |
| `requires_data_points` | Whether page needs raw data |
| `card_icon` | Font Awesome icon for homepage card |
| `card_description` | Description for homepage navigation card |

### Adding LLM Generators with Categories

LLM generators use a registry pattern with configurable prompt categories:

```python
# bobreview/llm_provider.py
from .llm_registry import register_llm_generator, LLMGeneratorDefinition, PromptCategory

def generate_custom_analysis(data_points, stats, config, images_dir):
    """Generate custom analysis content."""
    prompt = f"""Analyze data covering:
{_build_category_prompt('Custom Analysis')}
"""
    return call_llm(prompt, config=config)

# Register with categories
register_llm_generator(LLMGeneratorDefinition(
    section_name='Custom Analysis',
    generator_func=generate_custom_analysis,
    description='Custom performance analysis',
    categories=[
        PromptCategory('overview', 'Performance Overview', 'general assessment', priority=10),
        PromptCategory('issues', 'Key Issues', 'main problems found', priority=20),
        PromptCategory('actions', 'Action Items', 'recommended next steps', priority=30),
    ]
))
```

**To modify categories**: Just edit the `categories` list - prompts update automatically.

### Customizing Report Appearance

**Set theme in config (recommended):**

```python
from bobreview import ReportConfig

# Built-in themes: 'dark' (default), 'light', 'high_contrast'
config = ReportConfig(theme_id='light')
```

**Or via CLI:**
```bash
bobreview --plugin <plugin-name> --dir . --theme light
```

**Create a custom theme:**

```python
from bobreview.core.plugin_system import BasePlugin, get_registry
from bobreview.core.themes import ReportTheme

# Recommended: Via plugin
class MyThemePlugin(BasePlugin):
    name = "my-theme-plugin"
    version = "1.0.0"
    
    def on_load(self, registry):
        custom_theme = ReportTheme(
            id='brand',
            name='Brand Theme',
            bg='#1a1a2e',
            accent='#e94560',
            text_main='#ffffff',
            text_soft='#aaaaaa',
            border_subtle='#333333'
        )
        registry.themes.register(custom_theme, plugin_name=self.name)

# Or directly (if not using a plugin)
from bobreview.core.plugin_system import get_registry
registry = get_registry()
registry.themes.register(ReportTheme(
    id='brand',
    name='Brand Theme',
    bg='#1a1a2e',
    accent='#e94560',
    text_main='#ffffff',
    text_soft='#aaaaaa',
    border_subtle='#333333'
), plugin_name="custom")

# Then use it
config = ReportConfig(theme_id='brand')
```

**Available properties**: `bg`, `bg_elevated`, `bg_soft`, `accent`, `accent_soft`, `accent_strong`, `text_main`, `text_soft`, `border_subtle`, `danger`, `warn`, `ok`, `font_mono`, `font_sans`, `radius_lg`, `radius_md`, `shadow_soft`, `chart_grid_opacity`

### Customizing Chart Appearance

Charts use colors directly from `ReportTheme`. To customize chart appearance, create a custom theme with chart-specific properties:

```python
from bobreview.core.plugin_system import BasePlugin
from bobreview.core.themes import ReportTheme

class MyChartThemePlugin(BasePlugin):
    name = "my-chart-theme"
    version = "1.0.0"
    
    def on_load(self, registry):
        # Custom theme with adjusted chart grid opacity
        custom_theme = ReportTheme(
            id='custom',
            name='Custom Theme',
            text_soft='#aaaaaa',      # Chart text color
            border_subtle='#333333',    # Chart grid color
            chart_grid_opacity=0.3     # Subtle grid lines (0.0-1.0)
        )
        registry.themes.register(custom_theme, plugin_name=self.name)
```

Chart colors are automatically derived from the theme's accent colors and status colors (danger, warn, ok). The `chart_grid_opacity` property controls the opacity of chart grid lines.

---

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Version

**Current:** v1.0.7 - Plugin System

**Key Features:**
- **Plugin System** - Fully modular plugin architecture with SOLID & DRY principles
- **Focused Registries** - 11 focused registries (themes, generators, parsers, etc.)
- **Focused Config Classes** - 5 focused config classes (thresholds, LLM, execution, output, cache)
- **Dependency Injection** - No global singletons, better testability
- **Single Responsibility** - Focused responsibility classes
- **DRY Utilities** - Extracted common patterns
- JSON-based report systems framework
- Multi-provider LLM support (OpenAI, Anthropic, Ollama)
- Plugin system with extensible registries
- Global CLI command
- Intelligent caching
- Complete documentation

---

BobReview - Performance analysis and review tool for game development.

# BobReview

**Performance Analysis and Review Tool for Game Development**

Generate comprehensive HTML performance reports from game engine performance capture screenshots using LLM-powered analysis.

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

BobReview analyzes performance data extracted from PNG screenshot files and generates detailed HTML reports with statistical analysis, performance hotspots identification, and LLM-powered optimization recommendations.

**Key Feature:** Sends structured data tables to the LLM instead of images, significantly reducing token usage and costs by approximately 90%.

---

## Features

- **JSON-Based Report Systems** - Define custom analysis pipelines with JSON
- **Automated Data Extraction** - Parse performance metrics from PNG filenames
- **Statistical Analysis** - Calculate comprehensive statistics and identify patterns
- **Hotspot Identification** - Automatically find high-load and low-load performance zones
- **LLM-Powered Insights** - Generate contextual analysis using OpenAI GPT models
- **Professional Reports** - Generate presentation-ready HTML reports
- **Standalone HTML** - Images embedded as base64 for easy sharing
- **Intelligent Caching** - Cache LLM responses to reduce costs
- **Modular Architecture** - Clean packages with max 200 lines per file
- **Global CLI Command** - Run from any directory after installation

---

## Architecture

BobReview v1.0.4 uses a clean modular architecture:

```text
bobreview/
├── __init__.py        # Package entry
├── cli.py             # Command-line interface
├── data_parser.py     # PNG filename parsing
│
├── core/              # Foundational utilities
│   ├── config.py      # ReportConfig dataclass
│   ├── cache.py       # LLM response caching
│   ├── utils.py       # Logging, formatting
│   └── analysis.py    # Statistics calculation
│
├── registry/          # Unified registries
│   ├── themes.py      # Visual themes (dark, light, high_contrast)
│   ├── charts.py      # Chart.js configurations
│   └── pages.py       # Page definitions
│
├── llm/               # LLM abstraction layer
│   ├── client.py      # call_llm, call_llm_chunked
│   └── generators/    # Content generators
│       ├── executive.py, metrics.py, zones.py
│       ├── optimization.py, recommendations.py
│       ├── visuals.py, stats.py
│
├── pages/             # HTML page renderers
│   ├── base.py        # Shared templates
│   ├── homepage.py, metrics.py, zones.py
│   ├── visuals.py, optimization.py, stats.py
│   └── styles.css
│
└── report_systems/    # JSON-based configuration
    ├── schema.py, loader.py, executor.py
    └── builtin/png_data_points.json
```

**Design Principles:**
- Single Responsibility - Each module has one clear purpose (max 200 lines)
- Dependency Injection - Configuration passed through parameters
- No Circular Dependencies - Clean import hierarchy
- Testable - Each module can be tested independently
- Registry Pattern - Self-registration for pages, LLM generators, and charts

### Package Overview

| Package | Purpose |
|---------|---------|
| `core/` | Configuration, caching, logging, analysis |
| `registry/` | Themes, charts, pages (unified access) |
| `llm/` | LLM client and 7 content generators |
| `pages/` | 6 HTML page renderers + CSS |
| `report_systems/` | JSON-based pipeline configuration |

| Theme Registry | `theme_registry.py` | Report colors, fonts, and CSS variables |

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
bobreview --dir .
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
python bobreview.py --dir /path/to/screenshots
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
python bobreview.py --dir /path/to/screenshots

# Won't work from other directories
cd /some/other/directory
python bobreview.py --dir .  # Error: file not found
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
bobreview --dir .
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
# From any directory (after installation)
bobreview --dir /path/to/screenshots

# With custom output
bobreview --dir ./screenshots --output report.html

# Custom title and location
bobreview --dir ./screenshots \
  --title "Forest Level Performance" \
  --location "Dark Forest Area"
```

### Common Operations

```bash
# Test without LLM API calls
bobreview --dir ./screenshots --dry-run

# Process subset of data
bobreview --dir ./screenshots --sample 20

# Verbose output
bobreview --dir ./screenshots --verbose

# Custom thresholds
bobreview --dir ./screenshots \
  --draw-hard-cap 700 \
  --tri-hard-cap 150000
```

### Caching

Caching is enabled by default to reduce costs:

```bash
# First run - calls LLM and caches
bobreview --dir ./screenshots

# Second run - uses cache (instant)
bobreview --dir ./screenshots

# Clear cache and regenerate
bobreview --dir ./screenshots --clear-cache

# Disable caching
bobreview --dir ./screenshots --no-cache
```

### Standalone HTML Reports

BobReview creates self-contained HTML files with embedded images:

```bash
# Generate standalone HTML
bobreview --dir ./screenshots

# Result: Single HTML file you can share without image folder
# Perfect for email attachments or sharing via messaging apps
```

To use external image files instead (reduces HTML file size):

```bash
# Use the --no-embed-images flag
bobreview --dir ./screenshots --no-embed-images
```

**Note:** Embedded images increase HTML file size but eliminate external dependencies, making sharing much easier.

### Python API

Use BobReview as a library:

```python
from bobreview import ReportConfig, parse_filename, analyze_data, generate_html_report
from pathlib import Path

# Parse data
data_points = [parse_filename("Level1_85000_520_1234567890.png")]

# Configure
config = ReportConfig(
    title="Performance Analysis",
    location="Test Level",
    openai_api_key="sk-...",
)

# Analyze
stats = analyze_data(data_points, config)

# Generate report
html = generate_html_report(
    data_points, stats, "./screenshots", Path("report.html"), config
)

# Save
Path("report.html").write_text(html, encoding='utf-8')
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

### Using Report Systems

#### List Available Systems
```bash
bobreview --list-report-systems
```

Output:
```
Available report systems:

  png_data_points (built-in) - v1.0.0
    Game performance analysis from PNG filename metadata
    Path: bobreview/report_systems/builtin/png_data_points.json
```

#### Use a Specific System
```bash
# Use built-in system (default)
bobreview --report-system png_data_points --dir ./screenshots

# Use custom system
bobreview --report-system my_custom_system --dir ./data

# Use JSON file directly
bobreview --report-system /path/to/system.json --dir ./data
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
bobreview --report-system my_system --dir ./data
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

**LLM Configuration:**
```bash
--openai-key KEY        # OpenAI API key
--openai-model MODEL    # Model to use (default: gpt-4o)
--llm-temperature N     # Temperature 0-2 (default: 0.7)
--llm-max-tokens N      # Maximum tokens for LLM responses (default: 2000)
--llm-chunk-size N      # Samples per LLM call (default: 10)
--llm-combine-warning-threshold N  # Character threshold for chunk combination warning (default: 100000, advanced)
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
bobreview --dir ./screenshots

# Test with dry-run
bobreview --dir ./screenshots --dry-run

# Use sampling for quick tests
bobreview --dir ./screenshots --sample 20

# Adjust chunk size if needed
bobreview --dir ./screenshots --llm-chunk-size 5
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
python -m bobreview.cli --dir ./screenshots

# Or use script directly
cd /path/to/bobreview-source
python bobreview.py --dir /path/to/screenshots
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
bobreview --dir ./screenshots --openai-key sk-your-api-key-here

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
bobreview --dir .

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
        run: bobreview --dir ./captures --output report.html
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
    return get_html_template(f"{config.title} - Custom", body_content, linked_css=config.linked_css)


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
bobreview --dir . --theme light
```

**Create a custom theme:**

```python
from bobreview.theme_registry import register_theme, ReportTheme

register_theme(ReportTheme(
    id='brand',
    name='Brand Theme',
    bg='#1a1a2e',
    accent='#e94560',
    text_main='#ffffff',
    text_soft='#aaaaaa',
    border_subtle='#333333'
))

# Then use it
config = ReportConfig(theme_id='brand')
```

**Available properties**: `bg`, `bg_elevated`, `bg_soft`, `accent`, `accent_soft`, `accent_strong`, `text_main`, `text_soft`, `border_subtle`, `danger`, `warn`, `ok`, `font_mono`, `font_sans`, `radius_lg`, `radius_md`, `shadow_soft`, `chart_grid_opacity`

### Customizing Chart Appearance

Charts use colors directly from `ReportTheme`. To customize:

```python
from bobreview.theme_registry import register_theme, ReportTheme

# Custom theme with adjusted chart grid opacity
register_theme(ReportTheme(
    id='custom',
    name='Custom Theme',
    text_soft='#aaaaaa',      # Chart text color
    border_subtle='#333333',  # Chart grid color
    chart_grid_opacity=0.3    # Subtle grid lines (0.0-1.0)
))

# Add custom dataset styles
from bobreview.chart_registry import register_dataset, ChartDataset

register_dataset(ChartDataset(
    id='custom_metric',
    label='Custom Metric',
    primary_color='rgba(255, 0, 128, 0.8)',
    secondary_color='rgba(255, 0, 128, 1)'
))
```

---

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Version

**Current:** v1.0.4

**Features:**
- JSON-based report systems framework
- Custom analysis pipelines without coding
- Built-in `png_data_points` system
- Report system discovery and loading
- Template variable substitution
- Backward compatible with v1.0.3
- Modular architecture
- Global CLI command
- Intelligent caching
- Complete documentation

---

BobReview - Performance analysis and review tool for game development.

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

- **Automated Data Extraction** - Parse performance metrics from PNG filenames
- **Statistical Analysis** - Calculate comprehensive statistics and identify patterns
- **Hotspot Identification** - Automatically find high-load and low-load performance zones
- **LLM-Powered Insights** - Generate contextual analysis using OpenAI GPT models
- **Professional Reports** - Generate presentation-ready HTML reports
- **Standalone HTML** - Images embedded as base64 for easy sharing
- **Intelligent Caching** - Cache LLM responses to reduce costs
- **Modular Architecture** - Clean, maintainable codebase
- **Global CLI Command** - Run from any directory after installation

---

## Architecture

BobReview uses a modular architecture with clear separation of concerns:

```text
bobreview/
├── bobreview/              # Main package
│   ├── __init__.py         # Public API exports
│   ├── config.py           # Configuration and validation
│   ├── utils.py            # Logging and formatting
│   ├── cache.py            # LLM response caching
│   ├── data_parser.py      # PNG filename parsing
│   ├── analysis.py         # Statistical analysis
│   ├── llm_provider.py     # LLM API interaction
│   ├── report_generator.py # HTML generation
│   └── cli.py              # Command-line interface
│
├── bobreview.py            # Entry point script
├── requirements.txt        # Dependencies (single source of truth)
├── setup.py                # Package installer
└── pyproject.toml          # Package configuration
```

**Design Principles:**
- Single Responsibility - Each module has one clear purpose
- Dependency Injection - Configuration passed through parameters
- No Circular Dependencies - Clean import hierarchy
- Testable - Each module can be tested independently

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
--image-chunk-size N    # Samples per LLM call (default: 10)
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
bobreview --dir ./screenshots --image-chunk-size 5
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

---

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## Version

**Current:** v1.0.1

**Features:**
- Modular architecture
- Global CLI command
- Intelligent caching
- Complete documentation

---

BobReview - Performance analysis and review tool for game development.

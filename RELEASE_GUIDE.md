# BobReview - Release Guide

## Extensible Report Generation Framework

Version 1.0.7 - Plugin System

### What's New in v1.0.7

- **PluginHelper Facade** (`core/plugin_system/plugin_helper.py`):
  - Simplified registration API: `add_data_parser()`, `add_theme()`, `add_templates()`
  - One-call setup: `setup_complete_report_system()`

- **Plugin Scaffolding CLI**:
  - `bobreview plugins create my-plugin` - Generate complete plugin skeleton
  - `--template minimal|full` - Choose template complexity
  - Generates: manifest.json, plugin.py, parsers, templates, report_systems, sample_data

- **PageRenderer Class** (`engine/page_renderer.py`):
  - ~300 lines extracted from executor.py for better modularity

- **Preset Factory Functions** (`engine/presets.py`):
  - `create_simple_report_system()`, `create_csv_report_system()`

- **Hello World Plugin** (`plugins/hello_world/`):
  - Feature-complete reference plugin demonstrating all extension points

- **Critical Fixes**:
  - Fixed bare `except:` clauses in `engine/loader.py`
  - Removed dead code (`PageGeneratorInterface`, `PageGeneratorTemplate`)

- **Plugin System**: Fully modular plugin architecture with SOLID and DRY principles
  - **Focused Registries**: PluginRegistry split into 11 focused registries
  - **Focused Config Classes**: ReportConfig split into 5 focused config classes
  - **Dependency Injection**: No global singletons
  - **Single Responsibility**: Executor split into focused classes

- All v1.0.6 features preserved

---

## Installation

### 1. Extract the Files

Extract the zip file to any location on your machine:
```text
C:\Tools\bobreview\          (Windows)
~/Tools/bobreview/           (macOS/Linux)
```

### 2. Install Python Dependencies

Open a terminal/command prompt and navigate to the extracted folder:

```bash
cd path/to/bobreview

# Install the tool
pip install .
```

This installs BobReview as a global command you can run from anywhere.

### 3. Set Up LLM Provider API Key

BobReview supports multiple LLM providers. Choose one:

**OpenAI (default):**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows Command Prompt
set OPENAI_API_KEY=sk-your-api-key-here

# macOS/Linux
export OPENAI_API_KEY=sk-your-api-key-here
```

**Anthropic Claude:**
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="your-anthropic-key"

# macOS/Linux
export ANTHROPIC_API_KEY=your-anthropic-key
```

**Ollama (Local - No API Key Needed):**
```bash
# Just ensure Ollama is running
ollama serve

# Then use with --llm-provider ollama
bobreview --plugin <plugin-name> --dir . --llm-provider ollama --llm-model llama2
```

> **Tip:** Add the API key to your shell profile for persistence (see [Making It Permanent](#making-api-key-permanent))

### 4. Verify Installation

```bash
bobreview --version
```

You should see: `bobreview 1.0.7`

---

## How to Use

### Required File Format

BobReview analyzes PNG screenshot files with performance data in the filename:

**Format:**
```text
TestCase_tricount_drawcalls_timestamp.png
```

**Example:**
```text
Level1_85000_520_1234567890.png
```

Where:
- `Level1` = Test case/level name
- `85000` = Triangle count (integer)
- `520` = Draw call count (integer)
- `1234567890` = Unix timestamp (integer)

### Basic Usage

1. Navigate to your screenshots folder:
   ```bash
   cd /path/to/your/screenshots
   ```

2. Run BobReview:
   ```bash
   # Plugin is required
   bobreview --plugin <plugin-name> --dir .
   ```

3. Open the generated report:
   ```bash
   # Windows
   start performance_report.html
   
   # macOS
   open performance_report.html
   
   # Linux
   xdg-open performance_report.html
   ```

### Common Commands

```bash
# Custom report title and location (using plugin)
bobreview --plugin <plugin-name> --dir . --title "Forest Level" --location "Dark Forest"

# Custom output filename
bobreview --plugin <plugin-name> --dir . --output forest_analysis.html

# Create standalone HTML with embedded images
bobreview --plugin <plugin-name> --dir .

# Test without calling OpenAI API (no cost)
bobreview --plugin <plugin-name> --dir . --dry-run

# Process only 20 random samples (for quick testing)
bobreview --plugin <plugin-name> --dir . --sample 20

# Use light theme
bobreview --plugin <plugin-name> --dir . --theme light

# Use Anthropic Claude instead of OpenAI
bobreview --plugin <plugin-name> --dir . --llm-provider anthropic --llm-api-key your-anthropic-key

# Use local Ollama
bobreview --plugin <plugin-name> --dir . --llm-provider ollama --llm-model mistral

# List available plugins
bobreview plugins list

# List available report systems
bobreview --list-report-systems

# List available providers
bobreview --list-providers

# See all available options
bobreview --help
```

### Cost-Saving Features

**Caching is enabled by default** - subsequent runs with the same data are instant and free:

```bash
# First run - calls OpenAI API and caches results
bobreview --plugin <plugin-name> --dir .

# Second run - uses cached results (instant, no API cost)
bobreview --plugin <plugin-name> --dir .

# Force fresh analysis (clears cache)
bobreview --plugin <plugin-name> --dir . --clear-cache
```

---

## What to Consider

### System Requirements

- **Python:** Version 3.7 or higher (check with `python --version`)
- **Internet:** Required for OpenAI API calls
- **Disk Space:** ~50MB for installation
- **API Key:** Valid OpenAI API key with available credits

### Important Notes

1. **First Run Takes Time**
   - Initial analysis requires API calls and takes a few minutes
   - Subsequent runs use cache and are nearly instant
   - Use `--dry-run` to test configuration without API costs

2. **API Costs**
   - BobReview is optimized to send data tables instead of images (~90% cost reduction)
   - Typical analysis costs $0.10 - $0.50 depending on dataset size
   - Always use caching to avoid repeated costs
   - Test with `--sample 10` before processing large datasets

3. **File Naming is Critical**
   - Files must follow the exact format: `Name_triangles_draws_timestamp.png`
   - All numeric values must be integers
   - Invalid files are automatically skipped with warnings

4. **Performance Thresholds**
   - Thresholds are defined in report system JSON files (part of plugins)
   - For custom thresholds, create your own report system JSON or modify plugin configs
   - See plugin documentation for threshold customization options

5. **Standalone HTML Reports**
   - Creates a single HTML file with all images embedded (base64 encoding)
   - Perfect for sharing via email or messaging apps (no separate image folder needed)
   - Use `--no-embed-images` flag for external image files
   - Note: Embedded images increase file size but eliminate external dependencies

6. **Data Privacy**
   - Only filename data is sent to OpenAI (not the images themselves)
   - Cache is stored locally in `.bobreview_cache/` folder
   - No data is uploaded or stored externally

### Troubleshooting

**"Command not found" error:**
```bash
# Ensure Python Scripts is in PATH, or use:
python -m bobreview.cli --plugin <plugin-name> --dir .
```

**"No PNG files found" error:**
- Check that files follow the naming format
- Verify you're in the correct directory
- Use `--verbose` to see which files are being processed

**"API key not found" error:**
- Verify environment variable is set: `echo $OPENAI_API_KEY` (Linux/macOS) or `echo %OPENAI_API_KEY%` (Windows)
- Or provide key via command line: `bobreview --plugin <plugin-name> --dir . --llm-api-key sk-your-key`
- Or use Ollama for local inference: `bobreview --plugin <plugin-name> --dir . --llm-provider ollama`

**Slow performance:**
- First run is slow (normal - API calls take time)
- Use `--sample N` to test with fewer files
- Subsequent runs use cache (instant)

---

## Making API Key Permanent

To avoid setting the API key every time:

**Windows (PowerShell):**
```powershell
# Add to PowerShell profile
Add-Content $PROFILE "`n`$env:OPENAI_API_KEY='sk-your-api-key-here'"
```

**Windows (System):**
1. Open System Properties → Environment Variables
2. Add new User variable: `OPENAI_API_KEY` = `sk-your-api-key-here`

**macOS/Linux:**
```bash
# Add to shell profile
echo 'export OPENAI_API_KEY=sk-your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

---

## Quick Reference

```bash
# Basic usage - plugin is required
bobreview --plugin PLUGIN_NAME --dir /path/to/screenshots

# Plugin and Report System options
--plugin PLUGIN_NAME      # Plugin to use (e.g., "my-plugin")
--report-system SYSTEM    # Report system ID (optional, uses plugin default)
--list-report-systems     # List all available report systems

# Common options
--title "TEXT"           # Custom report title
--location "TEXT"        # Level/scene name
--output FILE            # Output filename
--dry-run                # Test without API calls
--sample N               # Process N random samples
--verbose                # Show detailed output
--clear-cache            # Force fresh analysis
--no-embed-images        # Use external image files instead of embedding
--linked-css             # Use external CSS file (styles.css)
--theme THEME            # 7 themes: dark, light, high_contrast, ocean, purple, terminal, sunset
--disable-page ID        # Disable a page (home, metrics, zones, visuals, optimization, stats)

# LLM Provider Configuration
--llm-provider PROVIDER  # Provider: openai (default), anthropic, ollama
--llm-api-key KEY        # API key for selected provider
--llm-model MODEL        # Model name (default depends on provider)
--llm-temperature N      # Temperature 0-2 (default: 0.7)
--llm-max-tokens N       # Maximum tokens for LLM responses (default: 2000)
--llm-chunk-size N       # Samples per LLM call (default: 10)
--list-providers         # List available LLM providers

# Help and version
--help                   # Show all options
bobreview --version      # Check version

# Test installation
python -c "from bobreview.core import ReportConfig; print('OK')"
```

---

---

## Support

- **Full Documentation:** See `README.md` in the installation folder
- **Quick Start:** See `QUICKSTART.md` for more examples
- **Detailed Install Guide:** See `INSTALL.md` for advanced setup
- **Release Notes:** See `docs/V1.0.7_RELEASE_NOTES.md` for v1.0.7 details

---

**BobReview v1.0.7** - Extensible report generation framework  
MIT License | Focused Architecture - SOLID & DRY Principles

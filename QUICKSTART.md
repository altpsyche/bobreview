# BobReview Quick Start Guide

Get started with BobReview in 5 minutes.

---

## Installation

```bash
# Clone repository
git clone https://github.com/DiggingNebula8/bobreview.git
cd bobreview

# Install
pip install .
```

The `bobreview` command is now available globally.

---

## Configuration

Set your LLM provider API key:

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-your-api-key-here

# Or Anthropic Claude
export ANTHROPIC_API_KEY=your-anthropic-key

# Or Ollama (no API key needed - runs locally)
# Just ensure Ollama is running: ollama serve
```

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
# Or for Anthropic:
$env:ANTHROPIC_API_KEY="your-anthropic-key"
```

**For persistence:**
- Linux/macOS: Add to `~/.bashrc` or `~/.zshrc`
- Windows: See [INSTALL.md](INSTALL.md) for permanent setup instructions

---

## File Format

BobReview expects PNG files with this naming format:

```
TestCase_tricount_drawcalls_timestamp.png
```

**Example:**
```
Level1_85000_520_1234567890.png
```

Where:
- `Level1` - Test case name
- `85000` - Triangle count
- `520` - Draw calls
- `1234567890` - Unix timestamp

---

## Basic Usage

Navigate to your screenshots folder and run:

```bash
cd /path/to/screenshots

# Plugin is required
bobreview --plugin <plugin-name> --dir .
```

Output: `performance_report.html` in current directory

View report:
```bash
# macOS
open performance_report.html

# Windows
start performance_report.html

# Linux
xdg-open performance_report.html
```

---

## Common Operations

### Test Without API Calls
```bash
bobreview --plugin <plugin-name> --dir ./screenshots --dry-run
```

### Process Subset
```bash
bobreview --plugin <plugin-name> --dir ./screenshots --sample 20
```

### Custom Report
```bash
bobreview --plugin <plugin-name> --dir ./screenshots \
  --title "Forest Level Performance" \
  --location "Dark Forest" \
  --output forest_report.html
```

### Verbose Output
```bash
bobreview --plugin <plugin-name> --dir ./screenshots --verbose
```

### Using Different Plugins
```bash
# Example: Performance analysis plugin
bobreview --plugin <plugin-name> --dir ./screenshots

# Example: Different plugin for different data types
bobreview --plugin <plugin-name> --dir ./game_data
```

### Standalone HTML (Embedded Images)
```bash
bobreview --plugin <plugin-name> --dir ./screenshots
```

Creates a single HTML file with all images embedded (no separate image folder needed).

---

## Caching

Cache is enabled by default to save costs:

```bash
# First run - calls LLM and caches
bobreview --plugin <plugin-name> --dir ./screenshots

# Second run - uses cache (instant)
bobreview --plugin <plugin-name> --dir ./screenshots

# Clear cache
bobreview --plugin <plugin-name> --dir ./screenshots --clear-cache
```

---

## Workflow Example

```bash
# Navigate to project (Linux/macOS)
cd ~/MyGame/PerformanceCaptures/Level_Forest

# Navigate to project (Windows)
cd C:\Users\YourName\MyGame\PerformanceCaptures\Level_Forest

# Run BobReview
bobreview --plugin <plugin-name> --dir . --title "Forest Level" --location "Dark Forest Section"

# Review report
open performance_report.html     # macOS
start performance_report.html    # Windows
xdg-open performance_report.html # Linux

# Regenerate uses cache (instant)
bobreview --plugin <plugin-name> --dir .

# Fresh analysis (clears cache)
bobreview --plugin <plugin-name> --dir . --clear-cache
```

---

## Tips

### Set Default API Key

**Linux/macOS:**
Add to `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`:
```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

**Windows PowerShell:**
Add to your PowerShell profile:
```powershell
Add-Content $PROFILE "`n`$env:OPENAI_API_KEY='sk-your-api-key-here'"
```

**Windows Command Prompt:**
Set via System Properties → Environment Variables

### Create Aliases

**Linux/macOS:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias bob="bobreview --plugin <plugin-name> --verbose"
alias bobtest="bobreview --plugin <plugin-name> --dry-run --verbose"
alias bobquick="bobreview --plugin <plugin-name> --sample 10"
```

**Windows PowerShell:**
Add to your PowerShell profile:
```powershell
function bob { bobreview --plugin <plugin-name> --verbose @args }
function bobtest { bobreview --plugin <plugin-name> --dry-run --verbose @args }
function bobquick { bobreview --plugin <plugin-name> --sample 10 @args }
```

**Windows Command Prompt:**
Create batch files in a directory in your PATH:
```cmd
@echo off
:: bob.bat
bobreview --plugin <plugin-name> --verbose %*
```

Usage (all platforms):
```bash
bob --dir ./screenshots
bobtest --dir ./screenshots
bobquick --dir ./screenshots
```

### Batch Processing

**Linux/macOS:**
```bash
for dir in Level_*; do
  bobreview --plugin <plugin-name> --dir "$dir" --output "${dir}_report.html" --location "$dir"
done
```

**Windows PowerShell:**
```powershell
Get-ChildItem -Directory Level_* | ForEach-Object {
  bobreview --plugin <plugin-name> --dir $_.Name --output "$($_.Name)_report.html" --location $_.Name
}
```

**Windows Command Prompt:**
```cmd
for /D %d in (Level_*) do bobreview --plugin <plugin-name> --dir "%d" --output "%d_report.html" --location "%d"
```

---

## Troubleshooting

### Command Not Found
```bash
# Reinstall
pip install .

# Or use module syntax
python -m bobreview.cli --plugin <plugin-name> --dir ./screenshots
```

### API Key Not Found
```bash
# Linux/macOS
export OPENAI_API_KEY=sk-your-api-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Windows Command Prompt
set OPENAI_API_KEY=sk-your-api-key-here
```

### No PNG Files Found
Check filename format: `TestCase_tricount_drawcalls_timestamp.png`

Example: `Level1_85000_520_1234567890.png`

### Slow First Run
This is normal. LLM API calls take time. Subsequent runs use cache.

---

## Getting Help

```bash
# Show all options
bobreview --help

# Show version
bobreview --version

# Test installation
python -c "from bobreview.core.config import Config; print('Installation verified')"
```

---

## Command Reference

```bash
# Basic (recommended: use plugin)
bobreview --plugin PLUGIN_NAME --dir PATH

# Legacy (backward compatible - plugin required)
bobreview --plugin <plugin-name> --dir PATH

# With options
bobreview --plugin PLUGIN_NAME --dir PATH [OPTIONS]

# Plugin and Report System:
--plugin PLUGIN_NAME        # Plugin to use (e.g., "my-plugin")
--report-system SYSTEM      # Report system ID (optional, uses plugin default)
--list-report-systems       # List all available report systems

# Common options:
--output FILE              # Output filename
--title "TITLE"            # Report title
--location "LOCATION"      # Level/scene name
--dry-run                  # Skip LLM API calls
--sample N                 # Process N random samples
--verbose                  # Detailed output
--quiet                    # Errors only
--clear-cache              # Clear LLM cache
--no-embed-images          # Use external image files
--linked-css               # Use external CSS file
--disable-page ID          # Disable a page (home, metrics, zones, visuals, optimization, stats)
--llm-provider PROVIDER    # LLM: openai, anthropic, ollama (default: openai)
--llm-api-key KEY          # API key for selected provider
--llm-model MODEL          # Model name (default depends on provider)
--list-providers           # List available providers
```

---

## Creating Your Own Plugin

Use the scaffolding command to generate a new plugin:

```bash
# Create a full-featured plugin with D&D demo
bobreview plugins create my-plugin

# Specify output directory
bobreview plugins create my-plugin --output-dir ./my-plugins
```

This generates a demo plugin with D&D-themed sample data:
- `manifest.json` - Plugin metadata
- `plugin.py` - Main plugin class
- `parsers/csv_parser.py` - Data parser
- `chart_generator.py` - Chart.js charts
- `theme.py` - 5 themes (Midnight, Aurora, Sunset, Frost, Dungeon)
- `sample_data/sample.csv` - Character roster with stats, classes, races, spells

---

## Next Steps

- Read [README.md](README.md) for complete documentation
- Check [INSTALL.md](INSTALL.md) for advanced installation
- Review [ROADMAP.md](ROADMAP.md) for upcoming features
- See [CHANGELOG.md](CHANGELOG.md) for v1.0.8 changes
- Try different configurations and explore options

---

**BobReview v1.0.8** - Plugin-First Architecture  
Extensible report generation framework.


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
bobreview --dir .
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
bobreview --dir ./screenshots --dry-run
```

### Process Subset
```bash
bobreview --dir ./screenshots --sample 20
```

### Custom Report
```bash
bobreview --dir ./screenshots \
  --title "Forest Level Performance" \
  --location "Dark Forest" \
  --output forest_report.html
```

### Verbose Output
```bash
bobreview --dir ./screenshots --verbose
```

### Custom Thresholds
```bash
bobreview --dir ./screenshots \
  --draw-hard-cap 700 \
  --tri-hard-cap 150000
```

### Change Theme
```bash
bobreview --dir ./screenshots --theme light
# Options: dark (default), light, high_contrast
```

### Standalone HTML (Embedded Images)
```bash
bobreview --dir ./screenshots
```

Creates a single HTML file with all images embedded (no separate image folder needed).

---

## Caching

Cache is enabled by default to save costs:

```bash
# First run - calls LLM and caches
bobreview --dir ./screenshots

# Second run - uses cache (instant)
bobreview --dir ./screenshots

# Clear cache
bobreview --dir ./screenshots --clear-cache
```

---

## Workflow Example

```bash
# Navigate to project (Linux/macOS)
cd ~/MyGame/PerformanceCaptures/Level_Forest

# Navigate to project (Windows)
cd C:\Users\YourName\MyGame\PerformanceCaptures\Level_Forest

# Run BobReview
bobreview --dir . --title "Forest Level" --location "Dark Forest Section"

# Review report
open performance_report.html     # macOS
start performance_report.html    # Windows
xdg-open performance_report.html # Linux

# Regenerate uses cache (instant)
bobreview --dir .

# Fresh analysis (clears cache)
bobreview --dir . --clear-cache
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
alias bob="bobreview --verbose"
alias bobtest="bobreview --dry-run --verbose"
alias bobquick="bobreview --sample 10"
```

**Windows PowerShell:**
Add to your PowerShell profile:
```powershell
function bob { bobreview --verbose @args }
function bobtest { bobreview --dry-run --verbose @args }
function bobquick { bobreview --sample 10 @args }
```

**Windows Command Prompt:**
Create batch files in a directory in your PATH:
```cmd
@echo off
:: bob.bat
bobreview --verbose %*
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
  bobreview --dir "$dir" --output "${dir}_report.html" --location "$dir"
done
```

**Windows PowerShell:**
```powershell
Get-ChildItem -Directory Level_* | ForEach-Object {
  bobreview --dir $_.Name --output "$($_.Name)_report.html" --location $_.Name
}
```

**Windows Command Prompt:**
```cmd
for /D %d in (Level_*) do bobreview --dir "%d" --output "%d_report.html" --location "%d"
```

---

## Troubleshooting

### Command Not Found
```bash
# Reinstall
pip install .

# Or use module syntax
python -m bobreview.cli --dir ./screenshots
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
python -c "from bobreview.core import ReportConfig; print('Installation verified')"
```

---

## Command Reference

```bash
# Basic
bobreview --dir PATH

# With options
bobreview --dir PATH [OPTIONS]

# Common options:
--output FILE              # Output filename
--title "TITLE"            # Report title
--location "LOCATION"      # Level/scene name
--draw-hard-cap N          # Draw call limit
--tri-hard-cap N           # Triangle limit
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

## Next Steps

- Read [README.md](README.md) for complete documentation
- Check [INSTALL.md](INSTALL.md) for advanced installation
- Review [ROADMAP.md](ROADMAP.md) for upcoming features
- Try different configurations and explore options

---

BobReview - Performance analysis and review tool.

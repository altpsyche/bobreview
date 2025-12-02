# BobReview Quick Start Guide

Get started with BobReview in 5 minutes.

---

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/bobreview.git
cd bobreview

# Install
pip install .
```

The `bobreview` command is now available globally.

---

## Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

For persistence, add to your shell profile (`~/.bashrc` or `~/.zshrc`).

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
# Navigate to project
cd ~/MyGame/PerformanceCaptures/Level_Forest

# Run BobReview
bobreview --dir . --title "Forest Level" --location "Dark Forest Section"

# Review report
open performance_report.html

# Regenerate uses cache (instant)
bobreview --dir .

# Fresh analysis (clears cache)
bobreview --dir . --clear-cache
```

---

## Tips

### Set Default API Key
Add to `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

### Create Aliases
```bash
alias bob="bobreview --verbose"
alias bobtest="bobreview --dry-run --verbose"
alias bobquick="bobreview --sample 10"
```

Usage:
```bash
bob --dir ./screenshots
bobtest --dir ./screenshots
bobquick --dir ./screenshots
```

### Batch Processing
```bash
for dir in Level_*; do
  bobreview --dir "$dir" --output "${dir}_report.html" --location "$dir"
done
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
export OPENAI_API_KEY=sk-your-api-key-here
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
python -c "from bobreview import ReportConfig; print('Installation verified')"
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
--openai-key KEY           # OpenAI API key
```

---

## Next Steps

- Read [README.md](README.md) for complete documentation
- Check [INSTALL.md](INSTALL.md) for advanced installation
- Review [ROADMAP.md](ROADMAP.md) for upcoming features
- Try different configurations and explore options

---

BobReview - Performance analysis and review tool.

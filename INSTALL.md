# BobReview Installation Guide

Complete installation instructions for BobReview.

---

## Table of Contents

- [Quick Install](#quick-install)
- [Development Install](#development-install)
- [Manual Install](#manual-install)
- [Verification](#verification)
- [Platform-Specific](#platform-specific)
- [Virtual Environment](#virtual-environment)
- [Uninstalling](#uninstalling)
- [Troubleshooting](#troubleshooting)

---

## Quick Install

Standard installation for most users:

```bash
# Clone repository
git clone https://github.com/DiggingNebula8/bobreview.git
cd bobreview

# Install
pip install .

# Verify
bobreview --version
```

Configure API key:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
```

Test:

```bash
cd /path/to/screenshots
# Plugin is required
bobreview --plugin mayhem --dir .
```

---

## Development Install

For developers modifying BobReview:

```bash
# Clone repository
git clone https://github.com/DiggingNebula8/bobreview.git
cd bobreview

# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"

# Verify
bobreview --version
```

**Benefits:**
- Changes to source code take effect immediately
- No need to reinstall after modifications
- Includes development tools (pytest, black, flake8, mypy)

---

## Manual Install

Run without installing the package:

```bash
# Install dependencies only
pip install -r requirements.txt

# Run from source directory
python bobreview.py --dir /path/to/screenshots
```

**Important:** When using `bobreview.py` directly:
- Must run from BobReview source directory
- The `bobreview` command is not available
- All features work normally

**Example:**
```bash
# Must be in source directory
cd /path/to/bobreview-source

# Run from here
python bobreview.py --dir /path/to/screenshots

# Won't work from other directories
cd /some/other/directory
python bobreview.py --dir .  # Error: file not found
```

---

## Verification

### Check Version
```bash
bobreview --version
```

### Check Help
```bash
bobreview --help
```

### Test Import
```bash
python -c "from bobreview import ReportConfig; print('Installation successful')"
```

### Dry Run Test
```bash
mkdir test_screenshots
cd test_screenshots
bobreview --dir . --dry-run
```

---

## Platform-Specific

### Windows

```powershell
# Install
pip install .

# Run
bobreview --dir screenshots
```

Python Scripts directory location: `C:\Python3X\Scripts\`

### macOS

```bash
# Install
pip3 install .

# Run
bobreview --dir screenshots
```

### Linux

```bash
# Install
pip3 install .

# Run
bobreview --dir screenshots
```

---

## Virtual Environment

Using a virtual environment is recommended:

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install
pip install .

# Use
bobreview --dir screenshots

# Deactivate
deactivate
```

### Using conda

```bash
# Create environment
conda create -n bobreview python=3.10

# Activate
conda activate bobreview

# Install
pip install .

# Use
bobreview --dir screenshots

# Deactivate
conda deactivate
```

---

## API Key Configuration

### Environment Variable (Recommended)

**Linux/macOS:**
```bash
# Temporary (current session)
export OPENAI_API_KEY=sk-your-api-key-here

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENAI_API_KEY=sk-your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

**Windows PowerShell:**
```powershell
# Temporary
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Permanent (add to $PROFILE)
Add-Content $PROFILE "`n`$env:OPENAI_API_KEY='sk-your-api-key-here'"
```

**Windows Command Prompt:**
```cmd
# Temporary
set OPENAI_API_KEY=sk-your-api-key-here

# Permanent (System Properties > Environment Variables)
```

### Command Line

```bash
# OpenAI (default)
bobreview --dir screenshots --llm-api-key sk-your-api-key-here

# Or specify provider
bobreview --dir screenshots --llm-provider anthropic --llm-api-key your-key

# Local Ollama (no API key needed)
bobreview --dir screenshots --llm-provider ollama --llm-model llama2
```

---

## Requirements

### Python Version
- Python 3.7 or higher
- Tested on 3.8, 3.9, 3.10, 3.11, 3.12

### Dependencies

**Required:**
- `openai>=1.0.0,<2.0.0`

**Optional (Recommended):**
- `tqdm>=4.65.0,<5.0.0` - Progress bars
- `colorama>=0.4.6,<1.0.0` - Colored output

**Development:**
- `pytest>=7.4.0` - Testing
- `pytest-cov>=4.1.0` - Coverage
- `black>=23.0.0` - Formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.0.0` - Type checking

### System
- Internet connection for API calls (except Ollama which runs locally)
- LLM API key (OpenAI or Anthropic) or local Ollama installation
- Approximately 50MB disk space

---

## Installation Options

### Standard
```bash
pip install .
```

### Editable (Development)
```bash
pip install -e .
```

### With Development Tools
```bash
pip install -e ".[dev]"
```

### Minimal (Manual)
```bash
pip install --no-deps .
pip install openai
```

---

## Uninstalling

### Remove Package
```bash
pip uninstall bobreview
```

### Remove Cache
```bash
# Remove cache directory
rm -rf .bobreview_cache

# Windows
rmdir /s .bobreview_cache
```

---

## Troubleshooting

### Command Not Found

**Cause:** BobReview not installed or not in PATH

**Solutions:**

```bash
# Solution 1: Ensure Python Scripts in PATH
python -m site --user-base

# Add to PATH (Linux/macOS)
export PATH="$PATH:$HOME/.local/bin"

# Add to PATH (Windows PowerShell - temporary)
$env:PATH += ";$env:APPDATA\Python\Python3X\Scripts"

# Add to PATH (Windows - permanent)
# Use System Properties > Environment Variables to add Python Scripts directory

# Solution 2: Use Python module syntax
python -m bobreview.cli --dir screenshots

# Solution 3: Reinstall
pip uninstall bobreview
pip install .
```

### Module Not Found

**Cause:** Package not installed

**Solution:**

```bash
pip install .
```

Or run from source:

```bash
python bobreview.py --dir screenshots
```

### Import Error

**Cause:** Missing dependencies

**Solution:**

```bash
pip install --upgrade -r requirements.txt
```

### Permission Errors

**Cause:** Insufficient permissions

**Solution:**

```bash
# Install for current user
pip install --user .
```

### Slow Installation

**Solution:**

```bash
# Use cache directory (Linux/macOS)
pip install --cache-dir ~/.pip_cache .

# Use cache directory (Windows)
pip install --cache-dir %TEMP%\pip_cache .
```

---

## Upgrading

### From Source

```bash
cd /path/to/bobreview-source
git pull
pip install --upgrade .
```

### Reinstall

```bash
pip uninstall bobreview
pip install .
```

### Upgrade Dependencies

```bash
pip install --upgrade -r requirements.txt
```

---

## Testing Installation

### Basic Test

```bash
bobreview --version
bobreview --help
```

### Full Test

```bash
# Navigate to test directory
cd /path/to/test/screenshots

# Dry run
bobreview --dir . --dry-run --verbose

# With API (if configured)
bobreview --dir . --sample 5
```

### Python API Test

```python
# test_bobreview.py
from bobreview import ReportConfig
from bobreview.plugins.mayhem.parsers import parse_filename  # MayhemAutomation-specific
from pathlib import Path

# Test import
print("Imports successful")

# Test parsing
try:
    data = parse_filename("Level1_85000_520_1234567890.png", pattern="{testcase}_{tris}_{draws}_{timestamp}.png")
    print("Parsing works")
except Exception as e:
    print(f"Parsing failed: {e}")

# Test config
config = ReportConfig(title="Test")
print("Config works")

print("\nInstallation verified")
```

Run:

```bash
python test_bobreview.py
```

---

## Cache Management

Default cache directory: `.bobreview_cache/`

### Set Custom Cache Directory

```bash
bobreview --dir screenshots --cache-dir /path/to/cache
```

### Clear Cache

```bash
bobreview --dir screenshots --clear-cache
```

### Disable Cache

```bash
bobreview --dir screenshots --no-cache
```

---

## Support

If installation issues persist:

1. Check this guide
2. Review troubleshooting section
3. Verify Python version: `python --version`
4. Verify pip version: `pip --version`
5. Check GitHub issues
6. Create new issue with error details

---

BobReview - Performance analysis and review tool.

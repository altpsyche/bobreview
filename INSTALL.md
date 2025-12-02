# Installation Guide

Quick guide to get the Performance Report Automation tool running.

## Prerequisites

- **Python 3.7 or higher**
- **OpenAI API key** (get one at [OpenAI API Keys](https://platform.openai.com/api-keys))

## Quick Install

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```


### 2. Set API Key

#### Option A: Environment variable (recommended)

```bash
# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-key-here
```

#### Option B: Command-line flag

```bash
python generate_performance_report.py --openai-key sk-your-key-here --dir ./data
```

### 3. Test Installation

```bash
# Show version
python generate_performance_report.py --version

# Test with dry run (no API calls)
python generate_performance_report.py --dir ./your_data_dir --dry-run
```

## Verify Your Setup

Run this test to ensure everything works:

```bash
# 1. Check Python version
python --version
# Should be 3.7 or higher

# 2. Check dependencies
python -c "import openai; print('OpenAI:', openai.__version__)"
python -c "try:
    import tqdm
    print('tqdm: installed')
except ImportError:
    print('tqdm: not installed (optional)')"
python -c "try:
    import colorama
    print('colorama: installed')
except ImportError:
    print('colorama: not installed (optional)')"

# 3. Check API key (without revealing it)
python -c "import os; print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"
```bash
pip install openai
```

### "No module named 'tqdm'" or "No module named 'colorama'"
These are optional dependencies. Either install them:
```bash
pip install tqdm colorama
```
Or ignore - the tool will work without them (just without progress bars/colors).

### "API key not found"
Make sure you've set the `OPENAI_API_KEY` environment variable or use `--openai-key` flag.

### "Command not found: python"
Try `python3` instead:
```bash
python3 generate_performance_report.py --version
```

## Optional: Add to PATH

### Linux/Mac
```bash
# Make executable
chmod +x generate_performance_report.py

# Add to your shell profile (~/.bashrc or ~/.zshrc)
alias perf-report='python /path/to/generate_performance_report.py'
```

### Windows
Add the script directory to your PATH environment variable.

## Next Steps

1. Prepare your PNG files with the correct naming format
2. Run your first report: see [README.md](README.md) for usage examples

## Getting Help

- Check [README.md](README.md) for full documentation
- Run `python generate_performance_report.py --help` for all options


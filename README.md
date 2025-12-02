# Performance Report Automation

Generate comprehensive HTML performance reports from game engine performance capture screenshots using LLM-powered analysis.

## Overview

This tool analyzes performance data extracted from PNG screenshot files and generates a detailed HTML report with statistical analysis, performance hotspots identification, and optimization recommendations. The analysis is powered by OpenAI's GPT models, which process structured data tables to provide insights and actionable recommendations.

## Features

- **Automated Data Extraction**: Parses performance metrics from PNG filenames
- **Statistical Analysis**: Calculates mean, median, quartiles, outliers, and standard deviation
- **Hotspot Identification**: Automatically identifies high-load and low-load performance zones
- **LLM-Powered Insights**: Uses OpenAI GPT models to generate contextual analysis and recommendations
- **Data-Driven Approach**: Sends structured data tables instead of images for efficient token usage
- **Professional HTML Reports**: Generates beautifully styled, presentation-ready reports
- **Chunked Processing**: Processes large datasets in configurable chunks for optimal performance

## Requirements

- Python 3.7+
- OpenAI Python library: `pip install openai`
- OpenAI API key (required)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install openai
   ```

3. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY=sk-your-api-key-here
   ```
   Or pass it via command line argument (see Usage below)

## File Format

The script expects PNG files with a specific naming format:

```
TestCase_tricount_drawcalls_timestamp.png
```

**Example:**
```
Level1_85000_520_1234567890.png
```

Where:
- `TestCase`: Test case or level name (e.g., "Level1")
- `tricount`: Triangle count (integer)
- `drawcalls`: Draw call count (integer)
- `timestamp`: Unix timestamp (integer)

## Usage

### Basic Usage

```bash
python generate_performance_report.py --dir ./screenshots --openai-key sk-... --output report.html
```

### With Environment Variable

```bash
export OPENAI_API_KEY=sk-...
python generate_performance_report.py --dir ./screenshots --output report.html
```

### Custom Configuration

```bash
python generate_performance_report.py \
  --dir ./screenshots \
  --openai-key sk-... \
  --output report.html \
  --title "City District Performance Analysis" \
  --location "City District" \
  --draw-hard-cap 700 \
  --tri-hard-cap 150000 \
  --image-chunk-size 15
```

## Command Line Arguments

### Required Arguments

- `--openai-key`: OpenAI API key (or set `OPENAI_API_KEY` environment variable)

### Optional Arguments

#### Input/Output
- `--dir`: Directory containing PNG files (default: current directory)
- `--output`: Output HTML file path (default: `performance_report.html`)
- `--images-dir`: Relative path to images directory from output (auto-detected if not specified)

#### Report Configuration
- `--title`: Report title (default: "Performance Analysis Report")
- `--location`: Location/level name (default: "Unknown Location")

#### Performance Thresholds
- `--draw-soft-cap`: Soft cap for draw calls (default: 550)
- `--draw-hard-cap`: Hard cap for draw calls (default: 600)
- `--tri-soft-cap`: Soft cap for triangles (default: 100000)
- `--tri-hard-cap`: Hard cap for triangles (default: 120000)
- `--high-load-draws`: High-load threshold for draw calls (default: same as draw-hard-cap)
- `--high-load-tris`: High-load threshold for triangles (default: same as tri-hard-cap)
- `--low-load-draws`: Low-load threshold for draw calls (default: 400)
- `--low-load-tris`: Low-load threshold for triangles (default: 50000)
- `--outlier-sigma`: Sigma multiplier for outlier detection (default: 2.0)

#### LLM Configuration
- `--openai-model`: OpenAI model to use (default: `gpt-4o`)
- `--llm-temperature`: LLM temperature for generation (default: 0.7)

#### Report Options
- `--no-recommendations`: Disable system-level recommendations section

## Report Sections

The generated HTML report includes:

1. **Executive Summary**: High-level overview with key metrics and performance health assessment
2. **Metric Deep Dive**: Detailed statistical analysis of draw calls and triangle counts
3. **Performance Zones and Hotspots**: Identification of high-load and low-load frames
4. **Optimization Checklist**: Actionable recommendations for critical hotspots
5. **System-Level Recommendations**: Broader optimization strategies (optional)
6. **Statistical Summary**: Complete statistical breakdown
7. **Full Sample Table**: Complete capture list with thumbnails

## How It Works

1. **Data Extraction**: The script scans the specified directory for PNG files matching the naming format
2. **Parsing**: Extracts performance metrics (draw calls, triangles, timestamps) from filenames
3. **Statistical Analysis**: Calculates comprehensive statistics including outliers and performance zones
4. **Data Table Generation**: Formats relevant data points as markdown tables
5. **LLM Processing**: Sends data tables to OpenAI API in configurable chunks for analysis
6. **Report Generation**: Combines LLM-generated content with statistics into a styled HTML report

## Performance Considerations

- **Token Efficiency**: The script sends structured data tables instead of images, significantly reducing token usage
- **Chunked Processing**: Large datasets are processed in chunks (default: 10 samples per call) to manage API limits
- **Error Handling**: The script raises clear errors if the API key is missing or LLM calls fail

## Example Output

The generated report includes:
- Color-coded performance indicators (OK/Warning/Danger)
- Interactive tables with thumbnails
- Professional dark-themed styling
- Mobile-responsive design
- Navigation links between sections

## Troubleshooting

### "OpenAI API key not found"
- Set the `OPENAI_API_KEY` environment variable, or
- Use the `--openai-key` command line argument

### "No PNG files found"
- Ensure PNG files are in the specified directory
- Verify filenames match the required format: `TestCase_tricount_drawcalls_timestamp.png`

### "Invalid filename format"
- Check that filenames follow the exact format: `TestCase_tricount_drawcalls_timestamp.png`
- Ensure all components are present and numeric values are valid integers

## License

This project is provided as-is for performance analysis automation.

## Contributing

Feel free to submit issues or pull requests for improvements.


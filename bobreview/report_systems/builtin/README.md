# Built-in Report Systems

This directory contains built-in report system definitions for BobReview.

## Available Systems

### png_data_points

**File:** `png_data_points.json`  
**Version:** 1.0.0  
**Description:** Game performance analysis from PNG filename metadata

Extracts triangle counts, draw calls, and timestamps from filename patterns.

**Filename Pattern:**
```
{testcase}_{tris}_{draws}_{timestamp}.png
```

**Examples:**
- `Level1_85000_520_1234567890.png`
- `Dark_Forest_95000_580_1234567891.png`

**Features:**
- Automatic data extraction from filenames
- Comprehensive statistical analysis
- 7 LLM-powered analysis sections
- 6 interactive HTML pages
- Performance zone identification
- Trend detection and outlier analysis

**Usage:**
```bash
# Use explicitly
bobreview --report-system png_data_points --dir ./screenshots

# Use implicitly (default)
bobreview --dir ./screenshots
```

## Creating Custom Report Systems

To create your own report system:

1. Copy `png_data_points.json` as a template
2. Modify the sections you need
3. Save to `~/.bobreview/report_systems/my_system.json`
4. Use with `bobreview --report-system my_system --dir ./data`

See `REPORT_SYSTEMS_GUIDE.md` in the project root for detailed documentation.


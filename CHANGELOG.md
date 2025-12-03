# Changelog

All notable changes to BobReview will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2025-12-03

### Added
- **Base64 Image Embedding**: Images are now embedded directly in HTML as base64-encoded data URIs by default
  - Enables single-file sharing without external image dependencies
  - Automatically detects image MIME types (PNG, JPG, GIF, BMP, WebP, SVG)
  - **Enabled by default** for convenience (creates standalone HTML files)
  - Use `--no-embed-images` flag to use external image files instead
  - Adds `embed_images` configuration option in `ReportConfig` (defaults to `True`)
  - New utility function `image_to_base64()` for image encoding

### Fixed
- Fixed syntax error in `llm_provider.py` where f-string expression contained a backslash (`\n`) in the `call_llm_chunked` function
- Resolved Python syntax error preventing the tool from running

### Changed
- **Default behavior**: Reports now embed images by default
  - Creates standalone HTML files that can be shared without image directories
  - Use `--no-embed-images` flag to use external image files instead

### Technical Details
- Extracted the `join` operation into a separate variable before using it in the f-string to avoid backslash in expression
- Error occurred at line 185 in `bobreview/llm_provider.py`
- Added helper function `_get_image_src()` in `report_generator.py` to handle both base64 and file path image sources
- Pre-encodes all unique images during report generation when `embed_images=True`
- Default value of `embed_images` in `ReportConfig` changed from `False` to `True`

---

## [1.0.0] - 2025-12-03

### Added
- Initial stable release
- Modular architecture with 9 focused modules
- Global CLI command installation via `pip install .`
- LLM response caching system (JSON-based, disk storage)
- Progress bars for file parsing and LLM calls (tqdm)
- Verbose logging mode (`--verbose`) and quiet mode (`--quiet`)
- Dry-run mode (`--dry-run`) for testing without API costs
- Sample mode (`--sample N`) for processing subsets of data
- Color-coded console output (colorama)
- Version flag (`--version`)
- Comprehensive error handling and validation
- Input validation for all CLI arguments
- Configurable cache directory (`--cache-dir`)
- Cache clearing functionality (`--clear-cache`)

### Features
- **Data Extraction**: Parse performance metrics from PNG filenames
- **Statistical Analysis**: Calculate comprehensive statistics (mean, median, quartiles, standard deviation, outliers)
- **Hotspot Identification**: Automatically find high-load and low-load performance zones
- **LLM-Powered Insights**: Generate contextual analysis using OpenAI GPT models
- **Professional Reports**: Generate presentation-ready HTML reports with:
  - Executive Summary
  - Metric Deep Dive (draw calls, triangles, temporal analysis, correlation)
  - Performance Zones and Hotspots
  - Optimization Checklist
  - System-Level Recommendations
  - Statistical Summary
  - Full Sample Table with thumbnails
- **Token Efficiency**: Sends structured data tables instead of images (~90% cost reduction)
- **Intelligent Caching**: Cache LLM responses to reduce costs on repeated runs

### Architecture
- Single Responsibility principle for each module
- Dependency Injection for testability
- No circular dependencies
- Clean import hierarchy
- Public API exports for library usage
- Single source of truth for dependencies (requirements.txt)

### Documentation
- Comprehensive README.md
- Quick Start guide (QUICKSTART.md)
- Installation guide (INSTALL.md)
- Development roadmap (ROADMAP.md)
- Release guide for end users (RELEASE_GUIDE.md)

### Dependencies
- `openai>=1.0.0,<2.0.0` (required)
- `tqdm>=4.65.0,<5.0.0` (optional, recommended)
- `colorama>=0.4.6,<1.0.0` (optional, recommended)

### Requirements
- Python 3.7 or higher
- OpenAI API key
- Internet connection for LLM API calls

---

## Release Notes

### Version History
- **1.0.1** - Feature release: Base64 image embedding + bug fix (syntax error in llm_provider.py)
- **1.0.0** - Initial stable release with comprehensive features and documentation

### Upgrade Instructions

#### From 1.0.0 to 1.0.1
```bash
cd /path/to/bobreview
git pull origin main
pip install --upgrade .
```

No breaking changes. Existing cache and configuration remain compatible.

---

[1.0.1]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/DiggingNebula8/bobreview/releases/tag/v1.0.0


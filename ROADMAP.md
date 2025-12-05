# BobReview Development Roadmap

Future development plans for BobReview.

---

## Vision

Evolve BobReview into a comprehensive performance analysis suite with:
- Multi-format data ingestion
- Interactive visualizations
- Automated regression detection
- Team collaboration features
- CI/CD integration

---

## Completed Features

### Foundation & Stability
- **COMPLETE** - Input validation for all CLI arguments
- **COMPLETE** - Graceful error handling and recovery
- **COMPLETE** - Actionable error messages
- **COMPLETE** - Edge case handling (empty directories, malformed files)

### Caching System
- **COMPLETE** - LLM response caching to disk (JSON format)
- **COMPLETE** - Configurable cache directory (`--cache-dir`)
- **COMPLETE** - Cache validation and invalidation (`--clear-cache`)
- **COMPLETE** - Automatic cache key generation (hash of data + config + prompt)

### Progress & Logging
- **COMPLETE** - Progress bars for file parsing (tqdm)
- **COMPLETE** - Progress bars for LLM calls with ETA
- **COMPLETE** - Verbose logging mode (`--verbose`)
- **COMPLETE** - Quiet operation mode (`--quiet`)
- **COMPLETE** - Elapsed time reporting

### Core Features
- **COMPLETE** - Version flag (`--version`)
- **COMPLETE** - Dry-run mode (`--dry-run`)
- **COMPLETE** - Sample mode (`--sample N`)
- **COMPLETE** - Color-coded console output (colorama)
- **COMPLETE** - Summary statistics display
- **COMPLETE** - Base64 image embedding (default enabled) for standalone HTML sharing

### Architecture
- **COMPLETE** - Modular architecture (9 focused modules)
- **COMPLETE** - Package structure (bobreview/)
- **COMPLETE** - Global CLI command installation
- **COMPLETE** - Single source of truth for dependencies (requirements.txt)
- **COMPLETE** - Clean import hierarchy
- **COMPLETE** - Public API exports
- **COMPLETE** - Comprehensive documentation

### Visual Charts & Graphs
- **COMPLETE** - Chart.js library integration
- **COMPLETE** - Timeline charts (draw calls over time)
- **COMPLETE** - Timeline charts (triangles over time)
- **COMPLETE** - Scatter plots (draws vs triangles)
- **COMPLETE** - Distribution histograms (draw calls, triangles)
- **COMPLETE** - Performance zone heatmaps (color-coded data points)
- **COMPLETE** - Interactive charts (zoom, pan, hover tooltips)

### Statistical Enhancements
- **COMPLETE** - Percentile analysis (P50, P90, P95, P99)
- **COMPLETE** - Confidence intervals (accurate t-distribution with scipy)
- **COMPLETE** - Trend detection (improving/degrading/stable classification)
- **COMPLETE** - Frame time calculation from timestamps with anomaly detection
- **COMPLETE** - Variance and coefficient of variation
- **COMPLETE** - Multiple outlier detection algorithms (IQR, MAD, Z-score)
- **COMPLETE** - Input validation for statistical functions

### Report Theming System
- **COMPLETE** - Theme registry system (`theme_registry.py`)
- **COMPLETE** - Three built-in themes (dark, light, high_contrast)
- **COMPLETE** - `ReportTheme` dataclass with 18+ customizable properties
- **COMPLETE** - Theme selection via CLI (`--theme`)
- **COMPLETE** - Theme selection via config (`theme_id` parameter)
- **COMPLETE** - CSS variable generation (`get_theme_css_variables()`)
- **COMPLETE** - Chart colors integrated with themes
- **COMPLETE** - Custom theme registration API

### Chart Configuration System
- **COMPLETE** - Chart registry system (`chart_registry.py`)
- **COMPLETE** - `ChartDataset` dataclass for dataset styling
- **COMPLETE** - `ChartConfig` dataclass for chart configuration
- **COMPLETE** - Pre-registered standard datasets (draws, tris, histograms)
- **COMPLETE** - Pre-registered standard charts (timelines, scatter, histograms)
- **COMPLETE** - Chart.js defaults generation from themes
- **COMPLETE** - Scale options generation from themes
- **COMPLETE** - Custom dataset/chart registration API

### LLM Generator System
- **COMPLETE** - LLM generator registry (`llm_registry.py`)
- **COMPLETE** - `LLMGeneratorDefinition` dataclass
- **COMPLETE** - `PromptCategory` system for structured prompts
- **COMPLETE** - 7 registered generators with categories
- **COMPLETE** - Self-registration pattern for modularity
- **COMPLETE** - Category-based prompt building

### Page Management System
- **COMPLETE** - Page registry with `PageDefinition` dataclass
- **COMPLETE** - Dynamic navigation generation from registry
- **COMPLETE** - Page disabling functionality (`--disable-page`)
- **COMPLETE** - Homepage cards auto-generated from page registry
- **COMPLETE** - Card icons and descriptions for navigation
- **COMPLETE** - Special badges for zones page (high/low load counts)

### CSS and Styling Options
- **COMPLETE** - External CSS file support (`--linked-css`)
- **COMPLETE** - CSS copying with error handling
- **COMPLETE** - Embedded CSS (default) for standalone reports
- **COMPLETE** - Theme-based CSS variable generation

---

## Planned Features

### Data Sources
- Design unified data schema (JSON/dataclass)
- CSV input support with header detection
- JSON input support
- Input format flag (`--input-format`)
- Data schema documentation
- Sample data files

### File Format Enhancements
- Filename pattern regex matching (`--filename-pattern`)
- JSON sidecar file support
- PNG EXIF/metadata reading
- Fallback chain: sidecar → EXIF → filename
- Enhanced data validation

### Visual Enhancements
- Chart export as PNG from browser
- Additional chart types (radar charts, box plots)
- Chart customization options

### Configuration Files
- PyYAML dependency
- YAML configuration file schema
- Config file argument (`--config`)
- Preset profiles (console, mobile, pc, vr)
- CLI argument overrides
- Config export functionality (`--save-config`)
- Configuration documentation

### Alternative LLM Support (HIGH PRIORITY)
- Abstract LLM interface
- Anthropic Claude provider
- Google Gemini provider
- Ollama (local) provider
- Provider selection flag (`--llm-provider`)
- Provider-specific configuration
- Cost comparison documentation
- Provider fallback system

### Export Options
- **COMPLETE** - External CSS export (`--linked-css`)
- PDF export (weasyprint or pdfkit)
- Markdown export
- JSON data export (raw + analyzed)
- JIRA issue template export
- GitHub issue template export
- Slack message format export
- Multiple export format support (`--export-format`)

### Batch Processing
- Batch mode for multiple directories (`--batch`)
- Comparison reports (side-by-side)
- Report diff functionality (`--compare`)
- Historical tracking database (SQLite)
- Trend charts across multiple captures
- Baseline reference setting (`--baseline`)

### Regression Detection
- Define regression criteria (configurable thresholds)
- Automatic baseline comparison
- Error exit code on regression
- Regression summary generation
- CI mode for CI/CD integration (`--ci-mode`)
- GitHub Action examples
- GitLab CI examples
- Jenkins integration documentation

### Template System (Jinja2-based)
- Jinja2 dependency
- Convert HTML to Jinja2 templates
- Template directory structure
- Template selection flag (`--template`)
- Additional template designs:
  - Classic (current design)
  - Minimal (lightweight)
  - Corporate (formal presentation)
- Logo customization support

### GPU Metrics
- GPU metrics schema design
- VRAM usage parsing
- GPU utilization metrics
- Memory bandwidth data
- GPU-specific analysis
- GPU vs CPU bound detection
- GPU metric visualizations

### Image Analysis (Optional)
- Enable image analysis flag (`--enable-image-analysis`)
- Screenshot analysis with multimodal LLM
- Visual issue detection (clipping, z-fighting)
- Overdraw pattern identification
- Scene composition analysis
- Cost analysis and warnings
- Opt-in requirement

### Testing & Quality
- pytest framework setup
- Data parsing tests
- Statistical analysis tests
- Mock LLM responses for testing
- Test data generators
- Caching logic tests
- Error handling tests
- Configuration loading tests
- 80%+ code coverage target
- CI/CD automated testing

### Documentation Improvements
- API documentation (Sphinx)
- Developer guide
- Architecture diagrams
- Contributing guidelines
- Code of conduct
- Example directory with sample data
- Video tutorials

### Web Dashboard
- Framework selection (FastAPI)
- REST API endpoints design
- Web frontend (React or Vue)
- Upload interface for files
- Real-time report generation
- Multi-user support with authentication
- Report history and management
- Team sharing and comments
- Webhooks for CI/CD integration
- Docker containerization
- Cloud deployment guides (AWS/Azure/GCP)

---

## Priority

### High Priority
1. Alternative LLM Support
2. Configuration Files
3. Multiple Data Sources

### Medium Priority
4. Export Options
5. Batch Processing
6. Regression Detection

### Low Priority
7. Template System
8. GPU Metrics
9. Testing & Quality
10. Web Dashboard
11. Image Analysis

---

## Dependencies Added

**For Statistics:**
- scipy>=1.11.0,<2.0.0 (accurate t-distribution for confidence intervals)

**For Registry Systems:**
- No new external dependencies (pure Python dataclasses)

## Dependencies to Add

**For Data Sources:**
- pandas (CSV/data manipulation)

**For Configuration:**
- PyYAML (config files)
- anthropic (Claude API)
- google-generativeai (Gemini API)

**For Export:**
- weasyprint or pdfkit (PDF export)
- sqlite3 (built-in, historical tracking)

**For Templates:**
- Jinja2 (template engine)
- Pillow (image analysis, optional)

**For Testing:**
- pytest (testing framework)
- pytest-cov (code coverage)
- pytest-mock (mocking utilities)

**For Web Dashboard:**
- fastapi (web framework)
- uvicorn (ASGI server)
- sqlalchemy (ORM)
- pydantic (data validation)
- React or Vue (frontend framework)

---

## Success Metrics

**Code Quality:**
- 80%+ test coverage
- Zero critical linter warnings
- 90%+ documentation coverage

**Performance:**
- <10s for 100 samples (with cache)
- <30s for 100 samples (no cache)
- Support 1000+ samples

**User Experience:**
- <5 min onboarding for new users
- Interactive charts in all reports
- Clear progress feedback

**Flexibility:**
- 3+ data input formats
- 3+ LLM providers
- 3+ export formats
- 4+ preset profiles

---

## Release Strategy

**v1.0 - Foundation Release (Current)**
- v1.0.0 - Initial stable release
- v1.0.1 - Base64 image embedding + bug fix (syntax error in llm_provider.py)
- v1.0.2 - Statistical enhancements + interactive charts
- v1.0.3 - Registry-based modularization (LLM, charts, themes)
- Core refactoring complete
- Caching implemented
- Modular architecture with registry patterns
- Comprehensive documentation
- Standalone HTML reports with embedded images
- Interactive Chart.js visualizations
- Advanced statistical analysis (percentiles, confidence intervals, outlier detection)
- Theme system with 3 built-in themes
- Chart configuration registry
- LLM generator registry with prompt categories
- Page management system with dynamic navigation

**v2.0 - Enterprise Release**
- Alternative LLM support
- Configuration files
- Export options
- Batch processing
- CI/CD integration

**v3.0 - Suite Release**
- GPU metrics support
- Template system
- Full test coverage
- Regression detection

**v4.0 - Platform Release**
- Web dashboard
- Multi-user support
- Cloud deployment
- Real-time analysis

---

## Contributing

Contributions are welcome. Consider:
- MIT License (see [LICENSE.md](LICENSE.md))
- Contributor guidelines
- Issue templates
- Pull request templates
- Community channels
- Feature voting system

---

## Notes

- Maintain backward compatibility through major versions
- Document breaking changes clearly
- Provide migration guides for each version
- Maintain changelog (CHANGELOG.md)
- Use semantic versioning for releases

---

Last updated: December 5, 2025
Current version: 1.0.3
Next milestone: v2.0 - Enterprise Release (Alternative LLM Support, Configuration Files, Batch Processing)

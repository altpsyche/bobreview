# BobReview Development Roadmap

Future development plans for BobReview.

---

## Vision

Evolve BobReview into a comprehensive plugin-based report generation framework with:
- Multi-format data ingestion via plugins
- Interactive visualizations
- Plugin marketplace
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
- **COMPLETE** (v1.0.7) - SOLID principles implementation
  - Single Responsibility Principle (SRP)
  - Open/Closed Principle (OCP)
  - Liskov Substitution Principle (LSP)
  - Interface Segregation Principle (ISP) - Focused registries and configs
  - Dependency Inversion Principle (DIP) - Dependency injection
- **COMPLETE** (v1.0.7) - DRY principle implementation
  - Extracted common utilities (plugin_utils, config_utils)
  - No code duplication
- **COMPLETE** (v1.0.7) - Focused architecture
  - 11 focused registries (themes, generators, parsers, etc.)
  - 5 focused config classes (thresholds, LLM, execution, output, cache)
  - Focused responsibility classes (ConfigMerger, ServiceValidator, PluginLifecycleManager)
- **COMPLETE** (v1.0.7) - Plugin infrastructure relocation
  - Moved plugin infrastructure to `bobreview/core/plugin_system/`
  - Clear separation: infrastructure in `core/plugin_system/`, implementations in `plugins/`
  - Removed lazy imports - all imports at module top-level
  - No backward compatibility for old `bobreview.plugins` infrastructure imports
- **COMPLETE** (v1.0.7) - Extension point abstraction
  - `IExtensionPoint` interface for accessing plugin implementations
  - `IPluginManager` interface for plugin lifecycle
  - Core code depends on abstractions, not concrete registry/loader
- **COMPLETE** (v1.0.7) - PluginHelper facade class
  - Simplified registration API for plugins
  - Methods: add_data_parser, add_theme, add_templates, add_report_system
  - setup_complete_report_system() for one-call registration
- **COMPLETE** (v1.0.7) - Plugin scaffolder CLI
  - `bobreview plugins create <name>` command
  - --template minimal|full for different complexity
  - --theme for theme selection
  - Generates complete plugin structure with all components
- **COMPLETE** (v1.0.7) - PageRenderer class extraction
  - ~300 lines extracted from executor.py
  - Better modularity and testability
- **COMPLETE** (v1.0.7) - Preset factory functions
  - create_simple_report_system()
  - create_csv_report_system()
  - create_multi_page_report_system()
- **COMPLETE** (v1.0.7) - Dynamic font loading
  - font_url property on ReportTheme
  - All built-in themes include Google Fonts URLs
  - Jinja2 templates dynamically load fonts
- **COMPLETE** (v1.0.7) - Theme naming consistency
  - Renamed font_sans to font_family
  - Python and CSS naming aligned
- **COMPLETE** (v1.0.7) - CLI theme override
  - --theme accepts any theme ID (built-in or plugin)
- **COMPLETE** (v1.0.7) - P0 Critical fixes
  - Fixed bare except: clauses in engine/loader.py
  - Removed dead code (PageGeneratorInterface, PageGeneratorTemplate)
  - HTML sanitizer now supports markdown tables

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
- **COMPLETE** - Theme registry system (`core/plugin_system/registries/theme_registry.py`)
- **COMPLETE** - 7 built-in themes: dark, light, high_contrast, ocean, purple, terminal, sunset
- **COMPLETE** - `ReportTheme` dataclass with 18+ customizable properties
- **COMPLETE** - Theme selection via CLI (`--theme`) overrides JSON preset
- **COMPLETE** - Theme selection via JSON (`"theme": {"preset": "ocean"}`)
- **COMPLETE** - CSS variable generation (`get_theme_css_variables()`)
- **COMPLETE** - Runtime theme.css generation for `--linked-css` mode
- **COMPLETE** - Chart colors integrated with themes
- **COMPLETE** - Custom theme registration API (`helper.add_theme()`, `helper.add_builtin_themes()`)

### CSS Architecture (v1.0.7)
- **COMPLETE** - Core CSS minimized (67 lines - theme tokens only)
- **COMPLETE** - Plugin-specific CSS isolation (`templates/static/plugin.css`)
- **COMPLETE** - Plugin base layout CSS (`templates/static/base.css`)
- **COMPLETE** - Jinja2 include for CSS loading
- **COMPLETE** - Aligned theme variable naming across all plugins
- **COMPLETE** - Dynamic theme injection via Jinja templating
- **COMPLETE** - Core free of all plugin-specific styles

### Chart Configuration System
- **COMPLETE** - Chart registry system (`core/plugin_system/registries/chart_type_registry.py`)
- **COMPLETE** - `ChartDataset` dataclass for dataset styling
- **COMPLETE** - `ChartConfig` dataclass for chart configuration
- **COMPLETE** - Pre-registered standard datasets (draws, tris, histograms)
- **COMPLETE** - Pre-registered standard charts (timelines, scatter, histograms)
- **COMPLETE** - Chart.js defaults generation from themes
- **COMPLETE** - Scale options generation from themes
- **COMPLETE** - Custom dataset/chart registration API

### LLM Generator System
- **COMPLETE** - LLM generator registry (`core/plugin_system/registries/llm_generator_registry.py`)
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

### JSON Report Systems Framework
- **COMPLETE** - Report system JSON schema with 15+ dataclasses
- **COMPLETE** - Report system loader with discovery and caching
- **COMPLETE** - Abstract interfaces (DataParser, LLMGenerator, PageGenerator)
- **COMPLETE** - Report system executor for pipeline orchestration
- **COMPLETE** - Template variable substitution in prompts
- **COMPLETE** - Data sampling strategies (all, random, sequential, mixed)
- **COMPLETE** - Built-in png_data_points system (350+ lines)
- **COMPLETE** - CLI flags (`--report-system`, `--list-report-systems`)
- **COMPLETE** (v1.0.7) - --theme CLI accepts any registered theme ID
- **COMPLETE** - Complete CLI override support
- **COMPLETE** - User custom systems directory (~/.bobreview/report_systems/)
- **COMPLETE** - Comprehensive documentation (REPORT_SYSTEMS_GUIDE.md)
- **COMPLETE** - FilenamePatternParser implementation
- **COMPLETE** - Backward compatibility with v1.0.3

### v1.0.4 Architecture Refactoring
- **COMPLETE** - `core/` package (config, cache, utils, analysis)
- **COMPLETE** - `registry/` package (themes, charts, pages unified)
- **COMPLETE** - `llm/` package (client + 7 generators)
- **COMPLETE** - `pages/` package (renamed from report_generator)
- **COMPLETE** - Split llm_provider.py (814 lines) → 9 small modules
- **COMPLETE** - Unified registries (4 files → 1 package)
- **COMPLETE** - Max 200 lines per file guideline

---

## Planned Features

### Data Sources
- **COMPLETE** - Design unified data schema (JSON/dataclass)
- **COMPLETE** - Input format configuration in JSON
- **COMPLETE** - Data schema documentation
- CSV parser implementation (schema ready)
- JSON file parser implementation (schema ready)
- API data source implementation (schema ready)
- Sample data files for each parser type

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

### Alternative LLM Support (v1.0.5 - COMPLETE)
- **COMPLETE** - Abstract LLM interface (`BaseLLMProvider`)
- **COMPLETE** - OpenAI provider (full implementation)
- **COMPLETE** - Anthropic Claude provider (full implementation)
- **COMPLETE** - Ollama (local) provider (full implementation)
- **COMPLETE** - Provider selection flag (`--llm-provider`)
- **COMPLETE** - Provider-specific configuration
- **COMPLETE** - Unified API key (`--llm-api-key`)
- **COMPLETE** - Provider factory pattern

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

### Template System (v1.0.6 - COMPLETE)
- **COMPLETE** - Jinja2 dependency
- **COMPLETE** - Convert HTML to Jinja2 templates
- **COMPLETE** - Template directory structure
- **COMPLETE** - CMS-style labels from JSON
- **COMPLETE** - Template engine with multi-source loading
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

**For Report Systems Framework (v1.0.4):**
- No new external dependencies (pure Python with built-in json module)

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
- v1.0.1 - Base64 image embedding + bug fix
- v1.0.2 - Statistical enhancements + interactive charts
- v1.0.3 - Registry-based modularization (LLM, charts, themes)
- v1.0.4 - Clean architecture refactoring + JSON report systems
  - New packages: core/, registry/, llm/, pages/
  - Split 814-line llm_provider.py → 9 focused modules
  - Unified registries into single package
  - Max 200 lines per file
- v1.0.5 - Plug-and-play LLM Provider System
  - Multi-provider support (OpenAI, Anthropic, Ollama)
  - Unified CLI arguments (`--llm-provider`, `--llm-api-key`)
  - Provider factory pattern for extensibility
- v1.0.6 - CMS-style Jinja2 Template System
  - All UI text configurable via JSON labels
  - Multi-source template loading
- v1.0.7 - Plugin System
  - PluginHelper API for simplified registration
  - Plugin scaffolder CLI (`bobreview plugins create`)
  - Dynamic font loading with font_url
  - CLI --theme accepts any theme (built-in or plugin)
  - No bundled plugins - create with scaffolder
- Core architecture complete
- Modular architecture with registry patterns
- JSON-based report system definitions

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

Last updated: December 12, 2025
Current version: 1.0.7
Next milestone: v2.0 - Enterprise Release

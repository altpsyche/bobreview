# Changelog

All notable changes to BobReview will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.7] - 2024-12-11

### Plugin Developer Experience

BobReview v1.0.7 introduces plugin development experience with new helper classes, CLI scaffolding, modular architecture refinements, and a refined theme system.

### Theme System Improvements

- **Theme Creation API**:
  - `create_theme(id, name, base='dark', **overrides)` - Quick theme creation with inheritance
  - `ReportTheme` dataclass - Full control over all 20+ theme properties
  - `hex_to_rgba(hex_color, alpha)` - Public utility for generating soft color variants

- **Theme Inheritance Fix**: `resolve_theme()` now correctly inherits parent values
  - Child themes only override explicitly specified properties
  - Parent theme values are preserved for unspecified properties

- **CLI Theme Fix**: `--theme` argument respects JSON `preset` unless explicitly overridden

- **Test Suite** (`tests/unit/core/`):
  - `test_themes.py` - 45+ tests for ReportTheme, CSS generation, inheritance
  - `test_theme_system.py` - 35+ tests for ThemeSystem facade
  - Behavior-focused tests (not implementation-specific)

### Added

- **PluginHelper Facade** (`core/plugin_system/plugin_helper.py`):
  - Simplified registration API for plugins
  - Methods: `add_data_parser()`, `add_theme()`, `add_templates()`, `add_report_system()`
  - Convenience methods: `add_context_builder()`, `add_chart_generator()`, `add_llm_generator()`
  - `setup_complete_report_system()` for one-call registration

- **Plugin Scaffolding CLI** (P1 - Plugin Developer Experience):
  - `bobreview plugins create <name>` - Generate complete plugin skeleton
  - `--template minimal|full` - Choose template complexity
  - `--theme dark|ocean|purple|terminal|sunset` - Choose color theme
  - `--output-dir` - Custom output directory
  - Generates: manifest.json, plugin.py, parsers, templates, report_systems, sample_data

- **Consolidated Theme System** (`core/themes.py`):
  - 7 built-in themes using `ReportTheme` dataclass: dark, light, high_contrast, ocean, purple, terminal, sunset
  - `get_theme_by_id()` - Lookup theme by ID
  - `get_available_themes()` - List all theme IDs
  - `theme_to_dict()` - Convert theme to template context
  - Plugins can create custom themes and register via `helper.add_theme()`

- **PageRenderer Class** (`engine/page_renderer.py`):
  - Extracted ~300 lines from executor.py for better modularity
  - Methods: `render_all_pages()`, `_render_page()`, `_generate_charts()`
  - Handles context building, image encoding, template rendering
  - Injects theme colors from JSON config into template context

- **Preset Factory Functions** (`engine/presets.py`):
  - `create_simple_report_system()` - Single-page reports with defaults
  - `create_csv_report_system()` - CSV-based reports
  - `create_multi_page_report_system()` - Multi-page reports

- **Hello World Plugin** (`plugins/hello_world/`):
  - Feature-complete reference plugin demonstrating all extension points
  - CSV data parser, context builder, chart generator
  - Custom "Cyberpunk Neon" theme with pink/cyan accents
  - Jinja2 templates (home, rankings pages)
  - Report system JSON definition

### Fixed

- **Bare `except:` Clauses** (P0 Critical Fix):
  - Replaced bare `except:` with `except Exception as e:` in `engine/loader.py` lines 95, 198
  - Errors now logged with `logger.debug()` for debuggability

### Removed

- **Dead Code** (P0 Critical Fix):
  - Deleted `engine/page_generator_base.py` (unused `PageGeneratorTemplate`)
  - Removed `PageGeneratorInterface` from `core/api.py` (replaced by template-based rendering)

### Engine & Core Purification

The engine and core directories are now completely plugin-agnostic:

- **Removed from Core**: `analyze_data`, `calculate_metric_stats`, `_calculate_frame_times` moved to plugin
- **Removed from Engine Schema**: `MetricConfig`, `StatisticsConfig`, `DerivedMetricConfig` moved to plugin
- **Removed from Engine Schema**: `performance_zones` field from `ChartConfig`
- **Added to Engine Schema**: `extensions: Dict[str, Any]` field for plugin-specific configuration
- **Updated Parsing**: All parsing functions updated to handle new schema structure
- **No Backward Compatibility**: Removed deprecated stubs and imports

### CSS Architecture Overhaul

Plugins are now fully self-contained with their own styles:

- **Core CSS Minimized**: `core/static/styles.css` now only 67 lines (was 380+)
  - Contains only theme token reference and minimal reset
  - No plugin-specific components
  
- **Plugin CSS Separation**:
  - Each plugin defines its own `templates/static/plugin.css`
  - Each plugin defines its own `templates/static/base.css` (layout)
  - Loaded via `{% include "static/plugin.css" %}` in templates
  
- **Theme Variable Alignment**: All plugins now use consistent variable names:
  - `--bg`, `--bg-elevated`, `--bg-soft`
  - `--accent`, `--accent-soft`, `--accent-strong`
  - `--text-main`, `--text-soft`
  - `--ok`, `--warn`, `--danger` (+ `-soft` variants)
  - `--border-subtle`, `--radius-lg`, `--radius-md`
  - `--shadow-soft`, `--sans`, `--mono`
  
- **Dynamic Theme Support**: Themes work with both embedded and external CSS:
  - Embedded CSS: Uses Jinja templating `{{ theme.accent if theme else '#4ea1ff' }}`
  - External CSS (`--linked-css`): Runtime-generated `static/theme.css` in output directory
  - `generate_theme_css()` - Creates CSS :root block from ReportTheme
  - CLI `--theme` overrides JSON `preset` for runtime switching



### Added

- **Focused Registry System** (`bobreview/core/plugin_system/registries/`):
  - `ThemeRegistry`, `WidgetRegistry`, `DataParserRegistry`, `LLMGeneratorRegistry`
  - `ChartTypeRegistry`, `PageRegistry`, `ServiceRegistry`, `ReportSystemRegistry`
  - `ChartGeneratorRegistry`, `ContextBuilderRegistry`, `TemplatePathRegistry`
  - `AnalyzerRegistry` - Plugins register their data analyzers here (v1.0.7)
  - Each registry has a single, focused responsibility

- **Focused Config Classes** (`bobreview/core/config_classes.py`):
  - `ThresholdConfig` - All threshold values
  - `LLMConfig` - All LLM provider settings
  - `ExecutionConfig` - Execution behavior (dry_run, verbose, etc.)
  - `OutputConfig` - Output settings (embed_images, theme_id, etc.)
  - `CacheConfig` - Cache settings

- **Responsibility Classes** (`bobreview/report_systems/`):
  - `ConfigMerger` - Handles configuration merging
  - `ServiceValidator` - Validates required services
  - `PluginLifecycleManager` - Manages plugin lifecycle hooks

- **Utility Functions** (`bobreview/core/`):
  - `plugin_utils.py` - `safe_plugin_call()`, `call_plugin_lifecycle_hooks()`
  - `config_utils.py` - `merge_config()`, `merge_nested_config()`

### Changed

- Plugin Registry API (v1.0.7):
  ```python
  # Focused interfaces
  registry.themes.register(theme)
  theme = registry.themes.get('dark')
  ```

- ReportConfig API (v1.0.7):
  ```python
  # Focused config classes
  config.thresholds.draw_soft_cap = 600
  config.llm.provider = 'openai'
  config.execution.dry_run = True
  ```

- CLI API (v1.0.7):
  ```bash
  # Plugin is required (no backward compatibility)
  bobreview --plugin <plugin-name> --dir ./screenshots
  
  # Report system selection:
  # - If plugin has 1 system: auto-selected
  # - If plugin has multiple: --report-system required
  ```

- ReportSystemExecutor:
  - Now accepts dependencies via constructor (dependency injection)
  - Uses focused responsibility classes internally
  - Better testability and maintainability

- Plugin System:
  - Plugin infrastructure moved to `bobreview.core.plugin_system`
  - All plugins use focused registry interfaces
  - Cleaner, more predictable API

- **Extension Point Abstraction** (`interface.py`):
  - New `IExtensionPoint` interface - abstract access to plugin-provided implementations
  - New `IPluginManager` interface - abstract plugin lifecycle management
  - Core code now depends on interfaces, not concrete registry/loader
  - Enables dependency injection and easier testing
  - Usage:
    ```python
    from bobreview.core.plugin_system import get_extension_point, get_plugin_manager
    
    # Access implementations
    extension_point = get_extension_point()
    theme = extension_point.get_theme('dark')
    
    # Manage plugins
    plugin_manager = get_plugin_manager()
    plugin_manager.discover()
    ```

### Removed

- **Backward Compatibility**:
  - Removed delegation methods from PluginRegistry (use focused registries directly)
  - Removed property delegations from ReportConfig (use focused configs directly)
  - All code updated to use focused interfaces
  - Cleaner, more predictable system

### Technical Details

New Files:
- `bobreview/core/plugin_system/registries/` - 11 focused registry classes
- `bobreview/core/plugin_system/` - Plugin infrastructure (base.py, loader.py, registry.py, manifest.py)
- `bobreview/core/plugin_system/interface.py` - Extension point abstraction layer
- `bobreview/core/config_classes.py` - Focused config classes
- `bobreview/report_systems/config_merger.py` - Config merging responsibility
- `bobreview/report_systems/service_validator.py` - Service validation responsibility
- `bobreview/report_systems/plugin_lifecycle.py` - Plugin lifecycle responsibility
- `bobreview/core/plugin_utils.py` - Plugin utility functions
- `bobreview/core/config_utils.py` - Config utility functions

Modified Files:
- `bobreview/core/plugin_system/registry.py` - Composes focused registries
- `bobreview/core/config.py` - Now uses focused config classes
- `bobreview/report_systems/executor.py` - Uses dependency injection and responsibility classes
- All plugin files - Updated to use focused registries
- All service files - Updated to use focused configs

Architecture Improvements:
- Follows SOLID principles (SRP, OCP, LSP, ISP, DIP)
- Follows DRY principle (no code duplication)
- Better testability (dependency injection)
- Better maintainability (focused responsibilities)
- More predictable (no hidden delegation layers)

### Benefits

- Follows SOLID principles
- Dependency injection enables better unit testing
- Focused interfaces make code purpose clear
- Type inference works better with focused classes
- Single responsibility makes changes safer

---

## [1.0.6] - 2025-12-05

### CMS-Style Jinja2 Template System

This release introduces a fully data-driven template system where all UI text labels come from JSON configuration - no hardcoded strings in templates.

#### New Template Package
```
bobreview/templates/
├── base.html.j2              # Base layout with blocks
├── components/
│   └── macros.html.j2        # Reusable components (stat_card, pill, etc.)
└── pages/
    ├── homepage.html.j2
    ├── metrics.html.j2
    ├── zones.html.j2
    ├── visuals.html.j2
    ├── optimization.html.j2
    └── stats.html.j2
```

### Added

- **CMS-Style Labels**: All UI text configurable via JSON
  ```json
  {
    "labels": {
      "draw_calls": "GPU Draw Calls",
      "triangles": "Vertex Count",
      "executive_summary": "Performance Overview"
    }
  }
  ```

- **Template Engine** (`core/template_engine.py`):
  - Multi-source loading: `~/.bobreview/templates/` → package built-ins
  - Custom filters: `format_number`, `sanitize`, `trend_icon`
  - Label injection into all templates

- **LabelConfig** with 40+ configurable labels:
  - Metric labels, section headers, status labels
  - Trend labels, table headers, navigation
  - Custom labels via `labels.custom` dict

- **Jinja2 Templates**: All 6 pages converted from Python f-strings to Jinja2

### Changed

- **Executor**: Now uses Jinja2-first rendering with Python fallback
- **Dependencies**: Added `jinja2>=3.1.0`

---

## [1.0.5] - 2025-12-05

### Plug-and-Play LLM Provider System

This release introduces a modular LLM provider architecture, allowing users to switch between different AI providers without modifying code.

#### New LLM Provider Package
```
bobreview/llm/providers/
├── __init__.py   # Package exports
├── base.py       # BaseLLMProvider abstract class
├── factory.py    # Provider registry & factory
├── openai.py     # OpenAI GPT implementation
├── anthropic.py  # Anthropic Claude implementation
└── ollama.py     # Ollama local models implementation
```

### Added

- **Multi-Provider Support**: Switch between LLM providers via CLI or JSON config
  - **OpenAI**: GPT-4o, GPT-4-turbo, GPT-3.5-turbo (default)
  - **Anthropic**: Claude 3 Opus, Sonnet, Haiku
  - **Ollama**: Any local model (Llama 2, Mistral, CodeLlama, etc.)

- **New CLI Arguments**:
  - `--llm-provider {openai,anthropic,ollama}`: Select LLM provider
  - `--llm-api-key KEY`: Unified API key argument
  - `--llm-api-base URL`: Custom API endpoint (e.g., for Ollama)
  - `--llm-model MODEL`: Model name (provider-specific defaults)
  - `--list-providers`: List available providers and their defaults

- **JSON Configuration**: Provider selection in report system JSON
  ```json
  {
    "llm_config": {
      "provider": "anthropic",
      "model": "claude-3-sonnet-20240229"
    }
  }
  ```

- **Provider Factory**: Extensible registry pattern for adding custom providers
  - `get_provider(name)`: Get provider instance
  - `register_provider(name, class)`: Register custom provider
  - `list_providers()`: List available providers

### Changed

- **ReportConfig**: Replaced OpenAI-specific fields with unified LLM fields
  - `openai_api_key` → `llm_api_key`
  - `openai_model` → `llm_model`
  - Added: `llm_provider`, `llm_api_base`

- **CLI**: Removed deprecated `--openai-key` and `--openai-model` arguments
  - Use `--llm-api-key` and `--llm-model` instead

- **client.py**: Refactored to use provider factory instead of hardcoded OpenAI

### Technical Details
- **New files**: 6 files in `bobreview/llm/providers/`
- **Modified files**: `client.py`, `config.py`, `cli.py`, `schema.py`
- **New dependencies**: 
  - `anthropic>=0.18.0` (optional, for Anthropic provider)
  - `httpx>=0.27.0` (optional, for Ollama provider)

---

## [1.0.4] - 2025-12-05

### Architecture Refactoring

This release introduces a major codebase restructuring for better modularity and maintainability.

#### New Package Structure
```
bobreview/
├── core/           # Foundational utilities
│   ├── config.py   # ReportConfig dataclass
│   ├── cache.py    # LLM response caching
│   ├── utils.py    # Logging, formatting
│   └── analysis.py # Statistics calculation
│
├── registry/       # Unified registries
│   ├── themes.py   # Visual themes
│   ├── charts.py   # Chart.js configs
│   └── pages.py    # Page definitions
│
├── llm/            # LLM abstraction
│   ├── client.py   # call_llm, call_llm_chunked
│   └── generators/ # One file per content type
│       ├── executive.py
│       ├── metrics.py
│       ├── zones.py
│       ├── optimization.py
│       ├── recommendations.py
│       ├── visuals.py
│       └── stats.py
│
├── pages/          # HTML page renderers (renamed from report_generator)
│   ├── base.py, homepage.py, metrics.py, etc.
│   └── styles.css
│
└── report_systems/ # JSON config (unchanged)
```

#### Key Changes
- **Split `llm_provider.py`** (814 lines) → 9 focused modules (~60-100 lines each)
- **Unified registries** (4 files → `registry/` package)
- **Renamed `report_generator/`** → `pages/` for clarity
- **Deleted 8 legacy files** that were superseded by new packages

### Added

#### JSON-Based Report Systems Framework
- **Report System Definitions**: Complete JSON schema for defining custom analysis pipelines
  - Configurable data source parsing (filename patterns, CSV support planned)
  - Custom metrics and statistics configuration
  - LLM generator definitions with prompt templates
  - Page layout and chart configuration
  - Theme and output settings
  
- **New CLI Flags**:
  - `--plugin PLUGIN_NAME`: Plugin to use (required, e.g., "my-plugin")
  - `--report-system SYSTEM`: Report system ID (optional, required if plugin has multiple systems)
  - `--list-report-systems`: List all available report systems
  - `bobreview plugins list`: List all available plugins

- **Plugin-Based Architecture**: Report systems are provided by plugins (e.g., a plugin provides report systems which encapsulate analysis workflows)

- **User Custom Systems Directory**: `~/.bobreview/report_systems/` for custom JSON definitions

### Fixed

#### CSS Gradient Issues
- **Stat Card Gradients**: Fixed invisible gradients in stat cards and UI elements
  - Solution: Use colored tints matching border colors (accent-soft, danger-soft, warn-soft, ok-soft)
  
- **New CSS Variables**: Added soft color variants for status colors
  - `--danger-soft: rgba(255, 92, 92, 0.15)`
  - `--warn-soft: rgba(230, 179, 92, 0.15)`
  - `--ok-soft: rgba(79, 209, 139, 0.15)`

### Changed
- **Unified Execution Path**: All report generation now uses the Report Systems framework
- **Architecture**: Clean modular packages with max 200 lines per file
- **Backward Compatibility**: 100% compatible - existing CLI commands unchanged

### Technical Details
- **Files created**: 25+ modular files in new package structure
- **Files deleted**: 8 legacy files (config.py, cache.py, utils.py, analysis.py, llm_provider.py, llm_registry.py, theme_registry.py, chart_registry.py, report_generator/)
- **Net effect**: Same functionality, cleaner organization, smaller files
- No breaking changes - all v1.0.3 CLI commands work identically

---

## [1.0.3] - 2025-12-05

### Added

#### Registry-Based Modularization
- **LLM Generator Registry** (`llm_registry.py`): Self-registration pattern for LLM content generators
  - `LLMGeneratorDefinition` dataclass with section_name, generator_func, description, and categories
  - `PromptCategory` dataclass for configurable prompt sections (id, title, focus, priority)
  - Functions: `register_llm_generator()`, `get_llm_generator()`, `get_generator_categories()`
  - All 7 LLM generators now self-register with configurable categories
  
- **Chart Configuration Registry** (`chart_registry.py`): Centralized Chart.js configuration
  - `ChartDataset` dataclass for dataset colors and point styles
  - `ChartConfig` dataclass for chart type, axis labels, and aspect ratios
  - Pre-registered: 4 datasets (draws, tris, histograms), 5 chart configs
  - Helper functions: `get_chart_defaults_js()`, `get_dataset()`, `get_chart()`
  - Chart colors pulled directly from `ReportTheme`

- **Report Theme Registry** (`theme_registry.py`): Centralized HTML report styling
  - `ReportTheme` dataclass with 18 properties (colors, fonts, borders, chart_grid_opacity)
  - 3 pre-registered themes: dark (default), light, high_contrast
  - `get_theme_css_variables()` generates CSS :root block for theme switching
  - Charts read colors directly from active report theme

- **Dynamic Homepage Navigation**: Homepage cards now generated from page registry
  - Extended `PageDefinition` with `card_icon` and `card_description` fields
  - `_generate_feature_cards()` helper dynamically builds navigation cards
  - Special pill badges for zones page showing high/low load counts

- **Config-Based Thresholds**: Moved hardcoded values to `ReportConfig`
  - `mad_threshold: float = 3.5` for MAD outlier detection
  - `llm_max_tokens: int = 2000` for LLM response limits
  - `theme_id: str = 'dark'` for centralized theme selection

- **New CLI Flags**: Enhanced control over report generation
  - `--theme THEME`: Choose report theme (dark, light, high_contrast)
    - Example: `bobreview --plugin <plugin-name> --dir . --theme light`
  - `--linked-css`: Use external CSS file instead of embedding
    - Creates `styles.css` in output directory for better maintainability
    - Reduces HTML file size, enables shared CSS across multiple reports
    - Example: `bobreview --plugin <plugin-name> --dir . --linked-css`
  - `--disable-page PAGE_ID`: Exclude specific pages from report
    - Can be used multiple times to disable multiple pages
    - Valid IDs: home, metrics, zones, visuals, optimization, stats
    - Example: `bobreview --plugin <plugin-name> --dir . --disable-page stats --disable-page visuals`

- **CSS Handling Improvements**:
  - External CSS file support via `linked_css` config option
  - `copy_css_to_output()` function with comprehensive error handling
  - Graceful degradation if CSS copy fails (warns but continues)
  - Catches FileNotFoundError, PermissionError, OSError with descriptive messages

### Fixed
- **Missing Type Import**: Added `Path` import in `base.py` to fix type annotation errors
  - `get_css_source_path()` and `copy_css_to_output()` now have proper type hints
- **CSS Copy Error Handling**: Added comprehensive exception handling for CSS file operations
  - Catches FileNotFoundError, PermissionError, OSError
  - Provides descriptive error messages with file paths
  - Report generation continues with warning if CSS copy fails
- **Dead Code Removal**: Removed unused navigation functions from `base.py`
  - Deleted unused `NAV_PAGES` constant
  - Deleted unused `get_nav_items()` function
  - Navigation now centralized in `registry.py`

### Changed
- **LLM Prompt Categories**: All 7 generators now use configurable `PromptCategory` lists
  - Executive Summary: 5 categories (health, concerns, hotspot, variance, frametime)
  - Metric Deep Dive: 5 categories (distribution, variability, trend, outliers, thresholds)
  - Zones & Hotspots: 3 categories (critical, highload, lowload)
  - Visual Analysis: 3 categories (shape, peaks, outliers)
  - Statistical Interpretation: 4 categories (consistency, trajectory, frametime, detection)
  - Optimization Checklist: 4 categories (geometry, drawcalls, lighting, verification)
  - System Recommendations: 5 categories (lod, occlusion, lighting, materials, regression)

- **Chart.js Defaults**: Moved from hardcoded in metrics.py/visuals.py to chart registry
  - Chart colors/fonts read directly from report theme
  - `chart_grid_opacity` property on ReportTheme (0.0-1.0)

### Technical Details
- **New files**: `bobreview/llm_registry.py`, `bobreview/chart_registry.py`, `bobreview/theme_registry.py`
- **Modified files**: 
  - `llm_provider.py` - LLM generator registrations
  - `report_generator/__init__.py` - Registry integration, CSS error handling
  - `metrics.py`, `visuals.py` - Chart registry integration
  - `homepage.py` - Dynamic card generation from page registry
  - `base.py` - CSS handling improvements, removed unused navigation functions
  - `config.py` - New validation rules for `mad_threshold` and `llm_max_tokens`
  - `cli.py` - New CLI flags for theme, linked CSS, and page disabling
- **Code Quality Improvements**:
  - Added `Path` type import in `base.py` (fixes missing type hint)
  - Removed unused `NAV_PAGES` constant and `get_nav_items()` function from `base.py`
  - Enhanced error handling in `copy_css_to_output()` with specific exception types
  - Updated `get_html_template()` to use `Optional[str]` for `theme_id` parameter
- **Validation Enhancements**:
  - `validate_config()` now checks `mad_threshold > 0`
  - `validate_config()` now checks `llm_max_tokens > 0`
- No breaking changes - all registrations happen at module import time
- Backward compatible with existing configurations

---

## [1.0.2] - 2025-12-03

### Added

#### Interactive Visual Charts
- **Chart.js Integration**: Added Chart.js 4.5.1 for interactive data visualizations
  - Timeline charts for draw calls with color-coded performance zones (red/yellow/green)
  - Timeline charts for triangles with color-coded performance zones
  - Scatter plots showing draw calls vs triangles correlation
  - Distribution histograms for both draw calls and triangles (20 bins)
  - Interactive features: zoom, pan, and hover tooltips on all charts
  - Dark theme styling matching report design
  - Responsive chart sizing (2.5:1 aspect ratio)

#### Statistical Enhancements
- **Percentile Analysis**: P50 (median), P90, P95, and P99 calculations
  - Uses `statistics.quantiles(data, n=100)` for accurate percentile computation
  - Included for both draw calls and triangles
- **Accurate Confidence Intervals**: Replaced linear t-distribution approximation with scipy
  - Now uses `scipy.stats.t.ppf()` for precise critical values
  - Properly utilizes the `confidence` parameter (was previously unused)
  - Dramatically improved accuracy for small samples:
    - n=2: t-value now 12.706 (was incorrectly 2.84, error of 9.87)
    - n=5: t-value now 2.776 (was incorrectly 2.75)
    - n=10: t-value now 2.262 (was incorrectly 2.60)
- **Trend Detection**: Automatic classification of performance trends
  - Linear regression analysis on temporal data
  - Classifies trends as: improving, stable, or degrading
  - Normalized slope calculations relative to data variability
- **Frame Time Analysis**: Enhanced timestamp analysis with anomaly detection
  - Calculates frame deltas from consecutive timestamps
  - Detects anomalies (frame times >3x median) as potential hitches
  - Returns detailed tuples: (frame_index, delta_time, timestamp)
  - Preserves original frame indices for accurate correlation
- **Variance & Coefficient of Variation**: Additional statistical metrics
  - Variance calculation using `statistics.variance()`
  - Coefficient of Variation (CV): (stdev / mean) × 100
  - Helps assess relative data spread
- **Multiple Outlier Detection Methods**: Three complementary approaches
  - **IQR Method**: Interquartile Range (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
  - **MAD Method**: Median Absolute Deviation with modified z-scores
  - **Z-Score Method**: Standard deviation based (existing)
  - Input validation ensures values and indices match length
  - Uses `zip()` for safe paired iteration

### Fixed

#### Critical Fixes
- **Frame Index Preservation**: Fixed timestamp sorting bug in `_calculate_frame_times()`
  - **Impact**: Anomaly detection now correctly identifies which specific frames experienced hitches
  - Previously, sorting broke the association between indices and original data
- **Chart Initialization**: Fixed canvas error handling in JavaScript (5 locations)
  - Changed `return;` to `throw new Error('Canvas not found');`
  - **Impact**: All charts now initialize even if one fails
  - Previously, a missing canvas would exit the entire event handler, blocking subsequent charts
- **Histogram Edge Case**: Fixed inconsistent return key when all values are identical
  - Now returns `'labels'` key instead of `'bins'` key
  - **Impact**: Prevents Chart.js errors in edge cases

#### Code Quality Fixes
- **Simplified Percentile Code**: Removed redundant conditionals
  - `statistics.quantiles(data, n=100)` always returns exactly 99 elements
  - Cleaner, more readable code
- **Removed Unused Import**: Removed unused `math` import from report_generator.py
- **Corrected Comment**: Fixed misleading comment about performance zone logic
  - Changed "both must be high for red" to "either draws or tris high = red"
  - Now accurately describes OR logic

### Changed
- **Dependencies**: Added scipy for statistical accuracy
  - `scipy>=1.11.0,<2.0.0` added to requirements.txt
  - Used for accurate t-distribution in confidence interval calculations
  - ~54 MB installation size increase

### Technical Details
- Chart.js loaded via CDN: `https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js`
- All statistical improvements in `bobreview/analysis.py`
- All chart implementations in `bobreview/report_generator.py`
- Input validation added to `_detect_outliers_iqr()` and `_detect_outliers_mad()`
- Frame time anomaly format changed from `(index, delta)` to `(index, delta, timestamp)`

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
- **1.0.3** - Feature release: Registry-based modularization (LLM generators, charts, homepage)
- **1.0.2** - Feature release: Interactive visual charts + statistical enhancements
- **1.0.1** - Feature release: Base64 image embedding + bug fix (syntax error in llm_provider.py)
- **1.0.0** - Initial stable release with comprehensive features and documentation

### Upgrade Instructions

#### From 1.0.2 to 1.0.3
```bash
cd /path/to/bobreview
git pull origin main
pip install --upgrade .
```

**No breaking changes.** Existing cache and configuration remain fully compatible.

**New Files Added:**
- `bobreview/llm_registry.py` - LLM generator registry
- `bobreview/chart_registry.py` - Chart configuration registry  
- `bobreview/theme_registry.py` - Report theme registry

**New ReportConfig Fields** (with backward-compatible defaults):
- `mad_threshold: float = 3.5` - MAD outlier detection threshold (configurable, previously hardcoded)
- `llm_max_tokens: int = 2000` - Maximum tokens for LLM responses (configurable, previously hardcoded)
- `linked_css: bool = False` - Use external CSS file instead of embedding (default: embedded)
- `theme_id: str = 'dark'` - Report theme selection (options: 'dark', 'light', 'high_contrast')
- `disabled_pages: List[str] = []` - List of page IDs to exclude from report

**New CLI Flags:**
- `--theme {dark,light,high_contrast}` - Choose report theme
- `--linked-css` - Use external CSS file (creates styles.css in output directory)
- `--disable-page PAGE_ID` - Disable specific pages (can be used multiple times)

**Configuration Updates:**
- Existing config files/code do NOT need updates
- All new fields have sensible defaults
- New validations added for `mad_threshold` and `llm_max_tokens` (must be > 0)
- If using ReportConfig programmatically, you can optionally use new fields for more control

#### From 1.0.1 to 1.0.2
```bash
cd /path/to/bobreview
git pull origin main
pip install --upgrade .
```

**New dependency**: scipy>=1.11.0 will be installed automatically.

No breaking changes. Existing cache and configuration remain compatible.
Reports now include interactive charts and enhanced statistical analysis.

#### From 1.0.0 to 1.0.1
```bash
cd /path/to/bobreview
git pull origin main
pip install --upgrade .
```

No breaking changes. Existing cache and configuration remain compatible.

---

[1.0.7]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/DiggingNebula8/bobreview/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/DiggingNebula8/bobreview/releases/tag/v1.0.0


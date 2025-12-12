# BobReview Core & Systems API Guide

> **Scope**: This guide covers only the **core framework** and **system modules**. Plugin implementations are excluded.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Module (`core/`)](#core-module)
  - [Interfaces (`api.py`)](#interfaces)
  - [Configuration (`config.py`, `config_classes.py`)](#configuration)
  - [Themes](#themes)
  - [Template Engine](#template-engine)
  - [HTML Utilities](#html-utilities)
  - [Analysis Utilities](#analysis-utilities)
  - [Caching](#caching)
  - [Utilities](#utilities)
- [Plugin System (`core/plugin_system/`)](#plugin-system)
  - [BasePlugin](#baseplugin)
  - [PluginHelper](#pluginhelper)
  - [PluginRegistry](#pluginregistry)
  - [PluginLoader](#pluginloader)
  - [Scaffolder](#scaffolder)
  - [Registries](#registries)
- [Services (`services/`)](#services)
  - [BaseService](#baseservice)
  - [ServiceContainer](#servicecontainer)
  - [DataService](#dataservice)
  - [AnalyticsService](#analyticsservice)
  - [ChartService](#chartservice)
  - [LLMService](#llmservice)
  - [ReportPipeline](#reportpipeline)
  - [Service Exceptions](#service-exceptions)
- [Engine (`engine/`)](#engine)
  - [ReportSystemExecutor](#reportsystemexecutor)
  - [PageRenderer](#pagerenderer)
  - [Preset Factories](#preset-factories)
  - [Report System Loader](#report-system-loader)
  - [Base Classes](#base-classes)
  - [Schema Dataclasses](#schema-dataclasses)


---

## Architecture Overview

```text
bobreview/
├── core/                    # Foundational utilities and interfaces
│   ├── api.py               # Plugin interfaces (DataParserInterface, etc.)
│   ├── config.py            # ReportConfig composition
│   ├── config_classes.py    # ThresholdConfig, LLMConfig, etc.
│   ├── analysis.py          # Statistics calculations
│   ├── cache.py             # LLMCache
│   ├── utils.py             # Logging, formatting
│   ├── template_engine.py   # Jinja2 template loading
│   └── plugin_system/       # Plugin infrastructure
│       ├── base.py          # BasePlugin ABC
│       ├── registry.py      # PluginRegistry composition
│       ├── loader.py        # PluginLoader discovery
│       └── registries/      # 12 focused registries
│
├── services/                # Pluggable services
│   ├── container.py         # ServiceContainer (DI)
│   ├── data_service.py      # DataService
│   ├── analytics_service.py # AnalyticsService
│   ├── chart_service.py     # ChartService
│   └── llm_service.py       # LLMService
│
└── engine/                  # Report execution
    ├── executor.py          # ReportSystemExecutor
    ├── schema.py            # JSON schema dataclasses
    ├── loader.py            # Report system loader
    └── parser_factory.py    # Data parser factory
```

**Design Principles**:
- SOLID (especially Interface Segregation, Dependency Inversion)
- Dependency Injection (no global singletons)
- Plugin-First (all domain logic via plugins)
- Registry Pattern (self-registration for extension points)

---

## Core Module

### Interfaces

Located in `core/api.py`. Plugins implement these ABCs:

#### `DataParserInterface`
```python
class DataParserInterface(ABC):
    def __init__(self, config: DataSourceConfig): ...
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]: ...
    
    @abstractmethod
    def discover_files(self, directory: Path) -> List[Path]: ...
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]: ...
```

#### `LLMGeneratorInterface`
```python
class LLMGeneratorInterface(ABC):
    @abstractmethod
    def generate(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: ReportConfig,
        context: Dict[str, Any]
    ) -> Dict[str, Any]: ...
```

#### `ChartGeneratorInterface`
```python
class ChartGeneratorInterface(ABC):
    @abstractmethod
    def generate_chart(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: ReportConfig,
        chart_config: Dict[str, Any]
    ) -> str: ...
```

#### `PageGeneratorInterface`
```python
class PageGeneratorInterface(ABC):
    @abstractmethod
    def render(
        self,
        stats: Dict[str, Any],
        llm_content: Dict[str, Any],
        config: ReportConfig,
        context: Dict[str, Any]
    ) -> str: ...
```

#### `ContextBuilderInterface`
```python
class ContextBuilderInterface(ABC):
    @abstractmethod
    def build_context(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        config: ReportConfig,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]: ...
```

---

### Configuration

Located in `core/config_classes.py`.

#### `ThresholdConfig`
```python
class ThresholdConfig(dict):
    """Generic threshold storage. No hardcoded fields."""
    def __init__(self, **kwargs): ...
    # Access: config.thresholds['outlier_sigma']
```

#### `LLMConfig`
```python
@dataclass
class LLMConfig:
    provider: str = "openai"      # 'openai', 'anthropic', 'ollama'
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000
    chunk_size: int = 10
    combine_warning_threshold: int = 100000
    enable_cache: bool = True
```

#### `CacheConfig`
```python
@dataclass
class CacheConfig:
    cache_dir: Path = Path(".bobreview_cache")
    use_cache: bool = True
    clear_cache: bool = False
```

#### `ExecutionConfig`
```python
@dataclass
class ExecutionConfig:
    dry_run: bool = False
    sample_size: Optional[int] = None
    verbose: bool = False
    quiet: bool = False
    enable_recommendations: bool = True
```

#### `OutputConfig`
```python
@dataclass
class OutputConfig:
    embed_images: bool = True
    linked_css: bool = False
    theme_id: str = 'dark'
    disabled_pages: Optional[List[str]] = None
```

#### `ReportConfig`
```python
@dataclass
class ReportConfig:
    title: Optional[str] = None
    thresholds: ThresholdConfig = None  # Auto-initialized
    llm: LLMConfig = None               # Auto-initialized
    cache: CacheConfig = None           # Auto-initialized
    execution: ExecutionConfig = None   # Auto-initialized
    output: OutputConfig = None         # Auto-initialized
```

---

### Themes

Located in `core/themes.py`.

```python
@dataclass
class ReportTheme:
    id: str                           # Unique identifier ('dark', 'light')
    name: str                         # Display name
    
    # Backgrounds
    bg: str = '#070b10'               # Main background
    bg_elevated: str = '#0e141b'      # Elevated surfaces
    bg_soft: str = '#151c26'          # Subtle background
    
    # Accents
    accent: str = '#4ea1ff'           # Primary accent
    accent_soft: str = 'rgba(...)'    # Soft accent
    accent_strong: str = '#ffb347'    # Strong accent
    
    # Text
    text_main: str = '#f5f7fb'        # Primary text
    text_soft: str = '#a8b3c5'        # Muted text
    
    # Status
    danger: str = '#ff5c5c'           # Error/critical
    warn: str = '#e6b35c'             # Warning
    ok: str = '#4fd18b'               # Success
    
    # Borders/Effects
    border_subtle: str = '#1e2835'
    shadow_soft: str = '0 18px 45px rgba(...)'
    radius_lg: str = '12px'
    radius_md: str = '8px'
    
    # Fonts
    font_mono: str = '"SF Mono", Menlo, ...'
    font_family: str = 'system-ui, ...'
    font_url: str = ''  # Google Fonts URL for dynamic loading

# Built-in themes
DARK_THEME: ReportTheme
LIGHT_THEME: ReportTheme
HIGH_CONTRAST_THEME: ReportTheme
BUILTIN_THEMES: List[ReportTheme]

# CSS generation
def get_theme_css_variables(theme: ReportTheme) -> str: ...
```

---

### Template Engine

Located in `core/template_engine.py`.

```python
class TemplateEngine:
    """Jinja2 template engine with multi-source loading."""
    
    def __init__(self, custom_paths: Optional[list] = None): ...
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        labels: Optional[LabelConfig] = None
    ) -> str: ...
    
    def render_string(
        self,
        template_string: str,
        context: Dict[str, Any],
        labels: Optional[LabelConfig] = None
    ) -> str: ...
    
    def template_exists(self, template_name: str) -> bool: ...

# Global access
def get_template_engine(custom_paths: list = None, force_refresh: bool = False) -> TemplateEngine: ...
def reset_template_engine(): ...
```

**Template Load Order** (first match wins):
1. User templates: `~/.bobreview/templates/`
2. Custom paths (if provided)
3. Plugin-registered templates (via `registry.template_paths`)

---

### HTML Utilities

Located in `core/html_utils.py`.

```python
def markdown_to_html(content: str) -> str: ...
def sanitize_llm_html(content: str) -> str: ...  # XSS-safe
def get_shared_css() -> str: ...                  # Core CSS content
def get_trend_icon(trend: str) -> str: ...        # 'improving'/'stable'/'degrading'
```

---

### Analysis Utilities

Located in `core/analysis.py`.

```python
def _calculate_confidence_interval(values: List[float], confidence: float = 0.95) -> Tuple[float, float]
def _calculate_linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]
def _detect_outliers_iqr(values: List[float], indices: List[int]) -> List[Tuple[int, float]]
def _detect_outliers_mad(values: List[float], indices: List[int], threshold: float = 3.5) -> List[Tuple[int, float]]
def _classify_trend(slope: float, stdev: float, mean: float) -> str
def format_data_table(data_points, max_rows=None, fields=None, field_labels=None) -> str
```

---

### Caching

Located in `core/cache.py`.

```python
class LLMCache:
    def __init__(self, cache_dir: Path, enabled: bool = True, config: ReportConfig = None): ...
    def get(self, prompt, data_table, model, temperature, max_tokens, provider="", api_base="") -> Optional[str]: ...
    def set(self, prompt, data_table, model, temperature, max_tokens, response, provider="", api_base=""): ...
    def clear(self): ...

# Global access
def get_cache() -> Optional[LLMCache]: ...
def init_cache(config: ReportConfig): ...
```

---

### Utilities

Located in `core/utils.py`.

```python
def log_info(message: str, config: ReportConfig = None): ...
def log_success(message: str, config: ReportConfig = None): ...
def log_warning(message: str, config: ReportConfig = None): ...
def log_error(message: str): ...
def log_verbose(message: str, config: ReportConfig = None): ...
def format_number(n, decimals=1) -> str: ...
def image_to_base64(image_path: Path) -> Optional[str]: ...
```

### Additional Utilities

#### Config Utilities (`config_utils.py`)
```python
def merge_config(target: Any, source: Dict[str, Any]): ...
def merge_nested_config(target: Any, source: Dict[str, Any]): ...
```

#### Plugin Utilities (`plugin_utils.py`)
```python
def safe_plugin_call(plugin, method_name, *args, config=None, **kwargs) -> Optional[Any]: ...
def call_plugin_lifecycle_hooks(plugins, hook_name, context, config=None): ...
```

#### Theme Utilities (`theme_utils.py`)
```python
def get_theme(theme_id: Optional[str] = None) -> Optional[ReportTheme]: ...
def get_theme_css_variables(theme_id: Optional[str] = None) -> str: ...
```

---

## Plugin System

### BasePlugin

Located in `core/plugin_system/base.py`.

```python
class BasePlugin(ABC):
    # Required metadata
    name: str = ""
    version: str = "0.0.0"
    author: str = "Unknown"
    description: str = ""
    dependencies: ClassVar[List[str]] = []
    
    def get_config(self) -> dict: ...
    def set_config(self, config: dict): ...
    
    @abstractmethod
    def on_load(self, registry: PluginRegistry) -> None: ...
    
    def on_unload(self) -> None: ...
    def on_report_start(self, context: dict) -> None: ...
    def on_report_complete(self, result: dict) -> None: ...
    def get_info(self, loaded: bool = False) -> PluginInfo: ...

@dataclass
class PluginInfo:
    name: str
    version: str
    author: str
    description: str
    enabled: bool = True
    loaded: bool = False
    path: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    provides: dict = field(default_factory=dict)
```

---

### PluginHelper

Located in `core/plugin_system/plugin_helper.py`. Simplified registration facade for plugin development.

```python
class PluginHelper:
    def __init__(self, registry: PluginRegistry, plugin_name: str): ...
    
    # Data Parsing
    def add_data_parser(self, parser_id: str, parser_class: Type): ...
    
    # Themes
    def add_theme(self, theme: ReportTheme): ...
    
    # Templates
    def add_templates(self, template_dir: Union[str, Path]): ...
    
    # Report Systems
    def add_report_system(self, system_id: str, system_def: Dict[str, Any]): ...
    def add_report_systems_from_dir(self, dir: Path) -> List[str]: ...
    
    # Context & Charts
    def add_context_builder(self, system_id: str, builder_class: Type): ...
    def add_chart_generator(self, system_id: str, generator_class: Type): ...
    
    # LLM Generators
    def add_llm_generator(self, generator_id: str, generator_class: Type): ...
    
    # Analysis
    def add_analyzer(self, analyzer_id: str, analyzer_func: Callable): ...
    
    # Services
    def register_default_services(self, container=None): ...
    
    # Convenience
    def setup_complete_report_system(
        self, system_id, system_def, parser_class=None,
        context_builder_class=None, chart_generator_class=None,
        template_dir=None
    ): ...
```

**Usage in plugins:**
```python
class MyPlugin(BasePlugin):
    def on_load(self, registry):
        helper = PluginHelper(registry, self.name)
        helper.add_data_parser("my_csv", MyCsvParser)
        helper.add_theme(my_theme)
        helper.add_templates(Path(__file__).parent / "templates")
        helper.add_report_systems_from_dir(Path(__file__).parent / "report_systems")
```

---

### Scaffolder

Located in `core/plugin_system/scaffolder.py`. CLI-based plugin skeleton generator.

```python
def create_plugin(
    name: str,
    output_dir: Path,
    template: Literal['minimal', 'full'] = 'full'
) -> Path: ...
```

**CLI Usage:**
```bash
# Create a full-featured plugin
bobreview plugins create my-plugin

# Create a minimal plugin
bobreview plugins create my-plugin --template minimal

# Specify output directory
bobreview plugins create my-plugin --output-dir ./plugins
```

**Generated structure (full template):**
```
my_plugin/
├── manifest.json
├── __init__.py
├── plugin.py
├── parsers/
│   ├── __init__.py
│   └── csv_parser.py
├── context_builder.py
├── chart_generator.py
├── report_systems/
│   └── my_plugin.json
├── templates/my_plugin/pages/
│   ├── base.html.j2
│   └── home.html.j2
└── sample_data/
    └── sample.csv
```

---

### PluginRegistry

Located in `core/plugin_system/registry.py`.

```python
class PluginRegistry:
    # Focused registries (ISP)
    themes: ThemeRegistry
    widgets: WidgetRegistry
    data_parsers: DataParserRegistry
    llm_generators: LLMGeneratorRegistry
    chart_types: ChartTypeRegistry
    pages: PageRegistry
    services: ServiceRegistry
    report_systems: ReportSystemRegistry
    chart_generators: ChartGeneratorRegistry
    context_builders: ContextBuilderRegistry
    template_paths: TemplatePathRegistry
    
    def get_component_owner(self, component_key: str) -> str: ...
    def unregister_plugin_components(self, plugin_name: str) -> int: ...
    def get_stats(self) -> Dict[str, int]: ...

# Global access
def get_registry() -> PluginRegistry: ...
def reset_registry() -> None: ...
```

---

### PluginLoader

Located in `core/plugin_system/loader.py`.

```python
class PluginLoader:
    def __init__(self, plugin_dirs: List[Path] = None, registry: PluginRegistry = None): ...
    
    def add_plugin_dir(self, directory: Path): ...
    def discover(self) -> List[PluginManifest]: ...
    def load(self, plugin_name: str, resolve_deps: bool = True) -> BasePlugin: ...
    def unload(self, plugin_name: str): ...
    def reload(self, plugin_name: str) -> BasePlugin: ...
    def load_all_enabled(self, enabled: List[str] = None, disabled: List[str] = None) -> List[BasePlugin]: ...
    def unload_all(self): ...
    def get_loaded_plugins(self) -> List[PluginInfo]: ...
    def get_discovered_plugins(self) -> List[PluginInfo]: ...

# Global access
def get_loader() -> PluginLoader: ...
def init_loader(plugin_dirs: List[Path]): ...

# Exceptions
class PluginLoadError(Exception): ...
class PluginDependencyError(PluginLoadError): ...
```

---

### Registries

Located in `core/plugin_system/registries/`.

| Registry | Purpose | Key Methods |
|----------|---------|-------------|
| `BaseRegistry` | Base class for all registries | `_register_component()`, `get_component_owner()`, `unregister_plugin_components()` |
| `ThemeRegistry` | Report themes | `register()`, `get()`, `get_all()` |
| `WidgetRegistry` | UI widgets | `register()`, `get()`, `get_all()` |
| `DataParserRegistry` | Data parsers | `register()`, `get()`, `get_all()` |
| `LLMGeneratorRegistry` | LLM generators | `register()`, `get()`, `get_all()` |
| `ChartTypeRegistry` | Chart types | `register()`, `get()`, `get_all()` |
| `PageRegistry` | Page definitions | `register()`, `get()`, `get_all()` |
| `ServiceRegistry` | Services | `register()`, `get()`, `get_all()` |
| `ReportSystemRegistry` | Report systems | `register()`, `get()`, `get_all()` |
| `ChartGeneratorRegistry` | Chart generators | `register()`, `get()`, `get_all()` |
| `ContextBuilderRegistry` | Context builders | `register()`, `get()`, `get_all()` |
| `TemplatePathRegistry` | Template paths | `register()`, `get_paths()` |
| `AnalyzerRegistry` | Analysis functions | `register()`, `get()`, `get_all()` |

---

## Services

### BaseService

Located in `services/base.py`.

```python
class BaseService(ABC):
    """Abstract base for all services."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None): ...
    def configure(self, config: Dict[str, Any]): ...
    def get_config(self, key: str, default: Any = None) -> Any: ...
```

---

### ServiceContainer

Located in `services/container.py`.

```python
class ServiceContainer:
    def register(self, name: str, service: Any, singleton: bool = True): ...
    def register_factory(self, name: str, factory: Callable[[], Any], singleton: bool = True): ...
    def register_class(self, name: str, cls: Type, singleton: bool = True): ...
    
    def get(self, name: str) -> Any: ...
    def get_optional(self, name: str) -> Optional[Any]: ...
    def has(self, name: str) -> bool: ...
    
    def replace(self, name: str, service: Any): ...
    def unregister(self, name: str) -> bool: ...
    def list_services(self) -> Dict[str, str]: ...
    def clear(self): ...

# Global access
def get_container() -> ServiceContainer: ...
def reset_container() -> None: ...
```

---

### DataService

Located in `services/data_service.py`.

```python
class DataService(BaseService):
    def __init__(self, config: Dict[str, Any] = None): ...
    
    def parse(
        self,
        input_dir: Path,
        data_source_config: DataSourceConfig,
        sample_size: Optional[int] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...
    
    def validate(
        self,
        data_points: List[Dict[str, Any]],
        required_fields: List[str]
    ) -> Dict[str, Any]: ...  # {'valid': bool, 'errors': List, 'warnings': List}
    
    def discover_files(
        self,
        directory: Path,
        data_source_config: DataSourceConfig
    ) -> List[Path]: ...
```

---

### AnalyticsService

Located in `services/analytics_service.py`.

```python
class AnalyticsService(BaseService):
    def analyze(
        self,
        data_points: List[Dict[str, Any]],
        metrics: List[str],
        metrics_config: Any,
        report_config: Any = None,
        thresholds: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]: ...
    
    def calculate_percentiles(
        self,
        values: List[float],
        percentiles: List[int] = None  # Default: [25, 50, 75, 90, 95, 99]
    ) -> Dict[str, float]: ...
    
    def detect_outliers(
        self,
        values: List[float],
        method: str = 'iqr',  # 'iqr', 'zscore', 'mad'
        threshold: float = 1.5
    ) -> Dict[str, Any]: ...  # {'indices', 'values', 'count', 'bounds'}
    
    def classify_performance_zones(
        self,
        data_points: List[Dict[str, Any]],
        metric: str,
        high_threshold: float,
        low_threshold: float
    ) -> Dict[str, List]: ...
```

---

### ChartService

Located in `services/chart_service.py`.

```python
class ChartService(BaseService):
    def __init__(self, config: Dict[str, Any] = None): ...
    
    @property
    def theme(self) -> ReportTheme: ...
    def set_theme(self, theme: ReportTheme): ...
    
    def hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str: ...
    def get_theme_colors(self) -> Dict[str, str]: ...
    def get_point_color(self, value, high_threshold, low_threshold) -> str: ...
    
    def generate_timeline_chart(
        self, data_points, value_field, high_threshold, low_threshold,
        chart_id, label='Value', x_label='Frame Index', y_label='Value'
    ) -> str: ...
    
    def generate_histogram_chart(
        self, values, chart_id, high_threshold=None, low_threshold=None,
        num_bins=15, label='Value', x_label='Value', y_label='Frequency'
    ) -> str: ...
    
    def generate_scatter_chart(
        self, data_points, x_field, y_field, chart_id,
        x_high, y_high, x_low, y_low, x_label='X', y_label='Y'
    ) -> str: ...
```

---

### LLMService

Located in `services/llm_service.py`.

```python
class LLMService(BaseService):
    def __init__(self, config: Dict[str, Any] = None): ...
    
    @property
    def client(self): ...  # LLM client (lazy-loaded)
    
    @property
    def cache(self) -> Optional[LLMCache]: ...
    
    def generate(
        self,
        generator_config: LLMGeneratorConfig,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        context: Dict[str, Any],
        dry_run: bool = False,
        report_config: ReportConfig = None
    ) -> str: ...
    
    def generate_all(
        self,
        generators: List[LLMGeneratorConfig],
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        context: Dict[str, Any],
        dry_run: bool = False,
        report_config: ReportConfig = None
    ) -> Dict[str, str]: ...
```

---

### ReportPipeline

Located in `services/pipeline.py`.

```python
class ReportPipeline:
    """Orchestrates report generation using pluggable services."""
    
    def __init__(self, container: Optional[ServiceContainer] = None): ...
    
    def execute(
        self,
        system_def: ReportSystemDefinition,
        input_dir: Path,
        output_path: Path,
        config: ReportConfig
    ) -> Dict[str, Any]: ...  # {'success', 'pages', 'stats', ...}

# Factory
def create_default_pipeline() -> ReportPipeline: ...
```

---

### Service Exceptions

Located in `services/base.py`.

```python
class ServiceError(Exception): ...           # Base
class DataServiceError(ServiceError): ...    # Parsing/validation
class AnalyticsServiceError(ServiceError): ...  # Statistics
class ChartServiceError(ServiceError): ...   # Chart generation
class LLMServiceError(ServiceError): ...     # LLM content
class RenderServiceError(ServiceError): ...  # Page rendering
```

---

## Engine

### ReportSystemExecutor

Located in `engine/executor.py`.

```python
class ReportSystemExecutor:
    def __init__(
        self,
        system_def: ReportSystemDefinition,
        config: ReportConfig,
        container: ServiceContainer = None,
        registry: PluginRegistry = None,
        template_engine: TemplateEngine = None,
        plugin_loader: PluginLoader = None
    ): ...
    
    def execute(self, input_dir: Path, output_path: Path) -> bool: ...
    def parse_data(self, input_dir: Path) -> List[Dict[str, Any]]: ...
    def analyze_data(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]: ...
    def generate_llm_content(self, data_points, stats) -> Dict[str, str]: ...
    def generate_pages(self, data_points, stats, llm_results, input_dir, output_path): ...
```

**Pipeline Steps**:
1. Parse data using `DataService`
2. Calculate statistics using `AnalyticsService`
3. Generate LLM content using `LLMService`
4. Render pages using `TemplateEngine`

---

### Report System Loader

Located in `engine/loader.py`.

```python
def load_report_system(name_or_path: str) -> ReportSystemDefinition: ...
def list_available_systems() -> List[Dict[str, Any]]: ...
def discover_report_systems() -> List[Dict[str, Any]]: ...
def find_report_system_path(name: str) -> Optional[Path]: ...
def clear_cache(): ...
def ensure_user_directory() -> Path: ...
def get_builtin_report_systems_dir() -> Path: ...
def get_user_report_systems_dir() -> Path: ...
```

---

### Base Classes

Located in `engine/`.

#### `DataParser` (`data_parser_base.py`)
```python
class DataParser(DataParserInterface):
    """Base class for data parsers."""
    
    def __init__(self, config: DataSourceConfig): ...
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Dict[str, Any]: ...
    
    @abstractmethod
    def discover_files(self, directory: Path) -> List[Path]: ...
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]: ...
    def _validate_data(self, data: Dict[str, Any]) -> bool: ...

class FilenamePatternParser(DataParser):
    """Parser for filename-encoded data (e.g. {field}_{value}.ext)."""
    pass
```

#### `LLMGeneratorTemplate` (`llm_generator_base.py`)
```python
class LLMGeneratorTemplate:
    """Template-based LLM content generator for JSON configs."""
    
    def __init__(self, config: LLMGeneratorConfig): ...
    def build_prompt(self, stats, data_points, context) -> str: ...
    def select_data_samples(self, data_points, stats) -> List[Dict]: ...
    def format_data_table(self, data_points) -> str: ...
```

#### `ParserFactory` (`parser_factory.py`)
```python
class ParserFactory:
    @staticmethod
    def create(config: DataSourceConfig) -> DataParser: ...
```

---

### Schema Dataclasses

Located in `engine/schema.py`.

| Dataclass | Purpose |
|-----------|---------|
| `FieldConfig` | Data field definition (type, required, min, max, pattern) |
| `ValidationConfig` | Parsing validation rules |
| `DataSourceConfig` | Data source configuration (type, format, pattern, fields) |
| `LLMConfig` | LLM provider settings |
| `PromptCategoryConfig` | Prompt category (id, title, focus, priority) |
| `DataTableConfig` | Data table for LLM prompts (columns, sample_strategy) |
| `LLMGeneratorConfig` | LLM generator definition |
| `ChartConfig` | Chart configuration (type, title, x_field, y_field) |
| `TemplateConfig` | Page template reference |
| `DataRequirements` | What data a page needs |
| `PageConfig` | Page definition (id, filename, nav_label, template) |
| `ThemeConfig` | Theme settings |
| `OutputConfig` | Output settings |
| `Labels` | CMS-style label storage |
| `ReportSystemDefinition` | Complete report system definition |

---

## Usage Examples

### Basic Report Generation
```python
from bobreview import ReportConfig
from bobreview.engine import load_report_system, ReportSystemExecutor
from pathlib import Path

config = ReportConfig(title="My Report")
config.llm.provider = "openai"

system_def = load_report_system("my_system")
executor = ReportSystemExecutor(system_def, config)
executor.execute(Path("./data"), Path("report.html"))
```

### Creating a Plugin
```python
from bobreview.core.plugin_system import BasePlugin

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def on_load(self, registry):
        # Register components
        registry.themes.register(my_theme, plugin_name=self.name)
        registry.data_parsers.register("my_parser", MyParser, plugin_name=self.name)
```

### Replacing a Service
```python
from bobreview.services import get_container

container = get_container()
container.replace('analytics', MyCustomAnalyticsService())
```

---

## Known Issues & Anti-Patterns

### ~~Bare `except:` Clauses~~ (Fixed in v1.0.7)

**Location**: `engine/loader.py` (lines 95, 198)

**Status**: ✅ Fixed. Now uses `except Exception as e:` with logging.

```python
# Fixed implementation
try:
    plugin_manager.discover()
except Exception as e:
    logger.debug(f"Plugin discovery failed: {e}")
```

### Module-Level Singletons

**Locations**: `core/cache.py`, `core/template_engine.py`

**Status**: Acceptable with reset functions.

Both modules provide `reset_*()` functions for testing and reinitialization:
- `reset_template_engine()`
- `init_cache()` / `get_cache()`

### Design Verifications ✓

| Check | Status |
|-------|--------|
| No plugin imports in core/ | ✅ Pure |
| No plugin imports in services/ | ✅ Pure |
| No plugin imports in engine/ | ✅ Pure |
| No hardcoded plugin names | ✅ All generic |
| No TODO/FIXME/HACK comments | ✅ None found |
| No mutable default arguments | ✅ None found |
| No `type: ignore` overrides | ✅ None found |

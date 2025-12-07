# BobReview GUI-Ready Report Architecture with Plugin System

> **Version**: 1.0.0  
> **Last Updated**: December 2025  
> **Status**: Planning Phase

## Table of Contents

1. [Goal](#goal)
2. [Current State Analysis](#current-state-analysis)
3. [Plugin Architecture](#plugin-architecture)
4. [Widget Registry Pattern](#widget-registry-pattern)
5. [Service Layer](#service-layer-decomposed-executor)
6. [AvaloniaUI Integration](#avaloniaui-integration)
7. [Implementation Phases](#implementation-phases)
8. [Security Considerations](#security-considerations)
9. [Configuration](#configuration)

---

## Goal

Restructure BobReview for visual report building (AvaloniaUI) with a plugin architecture, enabling:

- **Drag-and-drop report creation** without writing code
- **Third-party extensions** without modifying core code
- **Custom widgets, themes, charts, and analytics** via plugins
- **Live preview** of report changes in the GUI

---

## Current State Analysis

### ✅ What Works Well

| Pattern | Location | GUI-Ready? | Plugin-Ready? |
|---------|----------|------------|---------------|
| **JSON Schema** | `schema.py` dataclasses | ✅ | ✅ Serializable config |
| **Content Blocks** | `content_blocks` in JSON | ✅ | ✅ Dynamic content |
| **Registry Pattern** | `registry/` package | ✅ | ✅ **Already extensible!** |
| **Labels System** | `Labels` class | ✅ | ✅ Override-friendly |
| **Data-Driven Templates** | `{key}` placeholders + `\|interpolate` | ✅ | ✅ GUI can manipulate |

### ❌ Anti-Patterns to Fix

| Issue | Location | Impact |
|-------|----------|--------|
| **Monolithic Executor** | `executor.py` (947 lines) | Can't inject custom logic |
| **Hardcoded Chart Gen** | `_generate_charts()` | Can't add chart types |
| **No Widget Registry** | Scattered HTML patterns | Can't add custom widgets |
| **No Plugin Lifecycle** | N/A | Can't load/unload plugins |

---

## Plugin Architecture

### Core Concept

Plugins extend BobReview without modifying core code. Each plugin is a Python package that registers components at load time.

```
bobreview/
  plugins/                    # Plugin infrastructure
    __init__.py               # PluginRegistry
    base.py                   # BasePlugin ABC
    loader.py                 # Discovery & loading
    manifest.py               # Plugin metadata schema
  
~/.bobreview/plugins/         # User plugins (external)
  my_custom_plugin/
    __init__.py
    plugin.py                 # Entry point
    manifest.json             # Metadata
    widgets/                  # Custom widgets
    templates/                # Custom templates
```

### Extension Points

| Extension Point | What It Provides | Example Use |
|-----------------|------------------|-------------|
| **Widgets** | Custom UI components | `NetworkDiagramWidget` |
| **Data Parsers** | New file format support | CSV, Perfetto trace |
| **LLM Generators** | Custom AI prompts | Specialized analysis |
| **Themes** | Visual styling | Dark mode, brand colors |
| **Charts** | New chart types | Radar, Sankey diagrams |
| **Pages** | Custom report sections | Security audit page |
| **Services** | Processing pipelines | Custom analytics |

### Plugin Base Class

```python
# bobreview/plugins/base.py
from abc import ABC, abstractmethod
from typing import List

class BasePlugin(ABC):
    """Base class for all BobReview plugins."""
    
    # Metadata (required)
    name: str                          # "My Custom Plugin"
    version: str                       # "1.0.0"
    author: str                        # "Developer Name"
    description: str                   # Short description
    
    # Optional
    dependencies: List[str] = []       # Other required plugins
    
    # Lifecycle hooks
    @abstractmethod
    def on_load(self, registry: 'PluginRegistry') -> None:
        """Called when plugin is loaded. Register components here."""
        ...
    
    def on_unload(self) -> None:
        """Called when plugin is unloaded. Cleanup resources."""
        pass
    
    def on_report_start(self, context: 'ReportContext') -> None:
        """Called when report generation begins."""
        pass
    
    def on_report_complete(self, result: 'ReportResult') -> None:
        """Called when report generation completes."""
        pass
```

### Central Plugin Registry

```python
# bobreview/plugins/__init__.py
from typing import Type, List, Dict, Any

class PluginRegistry:
    """Central registry for all plugin components."""
    
    # Registration methods
    def register_widget(self, widget_cls: Type['BaseWidget']) -> None: ...
    def register_data_parser(self, parser_cls: Type['BaseDataParser']) -> None: ...
    def register_llm_generator(self, gen_cls: Type['BaseLLMGenerator']) -> None: ...
    def register_theme(self, theme: 'ReportTheme') -> None: ...
    def register_chart_type(self, chart: 'ChartConfig') -> None: ...
    def register_page(self, page: 'PageDefinition') -> None: ...
    def register_service(self, name: str, service: Any) -> None: ...
    
    # Discovery methods
    def get_all_widgets(self) -> List[Type['BaseWidget']]: ...
    def get_widget_schema(self, widget_type: str) -> Dict[str, Any]: ...
    def get_all_themes(self) -> List['ReportTheme']: ...
    def get_all_chart_types(self) -> List[str]: ...
```

### Plugin Loader

```python
# bobreview/plugins/loader.py
from pathlib import Path
from typing import List, Dict

class PluginLoader:
    """Discovers and loads plugins from configured directories."""
    
    def __init__(self, plugin_dirs: List[Path]):
        self.plugin_dirs = plugin_dirs
        self._loaded: Dict[str, BasePlugin] = {}
    
    def discover(self) -> List['PluginManifest']:
        """Find all plugins in plugin directories."""
        ...
    
    def load(self, plugin_name: str) -> 'BasePlugin':
        """Load a plugin by name, resolving dependencies first."""
        ...
    
    def unload(self, plugin_name: str) -> None:
        """Unload a plugin and cleanup resources."""
        ...
    
    def reload(self, plugin_name: str) -> 'BasePlugin':
        """Hot-reload a plugin for development."""
        ...
    
    def load_all_enabled(self) -> List['BasePlugin']:
        """Load all enabled plugins from config."""
        ...
```

### Plugin Manifest Schema

```json
{
  "name": "network-diagram-plugin",
  "version": "1.0.0",
  "author": "Developer Name",
  "description": "Adds network diagram widget and Sankey charts",
  "entry_point": "plugin:NetworkDiagramPlugin",
  "dependencies": [],
  "provides": {
    "widgets": ["network_diagram"],
    "charts": ["sankey"]
  },
  "config_schema": {
    "api_key": {
      "type": "string",
      "required": false,
      "description": "Optional API key for external service"
    }
  },
  "min_bobreview_version": "1.0.0"
}
```

### Example Plugin Implementation

```python
# ~/.bobreview/plugins/network_diagram/plugin.py
from bobreview.plugins import BasePlugin, PluginRegistry
from .widgets import NetworkDiagramWidget

class NetworkDiagramPlugin(BasePlugin):
    name = "Network Diagram"
    version = "1.0.0"
    author = "Developer"
    description = "Adds network visualization widget"
    
    def on_load(self, registry: PluginRegistry) -> None:
        # Register our custom widget
        registry.register_widget(NetworkDiagramWidget)
        
        # Register a custom chart type
        registry.register_chart_type(SankeyChart)
    
    def on_unload(self) -> None:
        # Cleanup if needed
        pass
```

---

## Widget Registry Pattern

### Widget Base Class

```python
# bobreview/widgets/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseWidget(ABC):
    """Base class for all report widgets."""
    
    # Metadata
    widget_type: str                   # Unique identifier: 'stat_card'
    display_name: str                  # Human name: 'Statistic Card'
    category: str                      # For GUI grouping: 'Data Display'
    icon: str                          # Material icon name: 'bar_chart'
    
    @classmethod
    @abstractmethod
    def get_props_schema(cls) -> Dict[str, Any]:
        """JSON Schema for widget properties (for GUI editor)."""
        ...
    
    @abstractmethod
    def render(self, props: Dict, context: 'DataContext') -> str:
        """Render widget to HTML string."""
        ...
    
    @classmethod
    def get_default_props(cls) -> Dict[str, Any]:
        """Default property values for new widget instances."""
        return {}
    
    @classmethod
    def get_preview_html(cls) -> str:
        """Static preview HTML for GUI drag-and-drop palette."""
        ...
```

### Example Widget: StatCard

```python
# bobreview/widgets/stat_card.py
from .base import BaseWidget

class StatCardWidget(BaseWidget):
    widget_type = "stat_card"
    display_name = "Statistic Card"
    category = "Data Display"
    icon = "analytics"
    
    @classmethod
    def get_props_schema(cls) -> dict:
        return {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Card title"},
                "value": {"type": "string", "description": "Value with {key} placeholders"},
                "sub": {"type": "string", "description": "Subtitle"},
                "variant": {
                    "type": "string",
                    "enum": ["ok", "warning", "danger", "neutral"],
                    "default": "neutral"
                },
                "icon": {"type": "string", "description": "Material icon name"}
            },
            "required": ["label", "value"]
        }
    
    def render(self, props: dict, context: 'DataContext') -> str:
        value = context.interpolate(props.get('value', ''))
        sub = context.interpolate(props.get('sub', ''))
        variant = props.get('variant', 'neutral')
        
        return f'''
        <div class="stat-card stat-card--{variant}">
            <div class="stat-card__label">{props['label']}</div>
            <div class="stat-card__value">{value}</div>
            <div class="stat-card__sub">{sub}</div>
        </div>
        '''
```

### Widget Directory Structure

```
bobreview/
  widgets/
    __init__.py                # Registry: register_widget(), get_widget()
    base.py                    # BaseWidget ABC
    
    # Built-in widgets
    stat_card.py               # StatCardWidget
    chart.py                   # ChartWidget  
    table.py                   # TableWidget
    callout.py                 # CalloutWidget
    image.py                   # ImageWidget
    text.py                    # TextWidget (markdown)
    metric_table.py            # MetricTableWidget
    grid.py                    # GridLayoutWidget
```

---

## Service Layer (Decomposed Executor)

### Why Decompose?

The current `executor.py` (947 lines) is a monolith that:
- Makes it impossible to reuse individual processing steps
- Prevents plugins from injecting custom behavior
- Makes testing difficult
- Creates tight coupling between unrelated concerns

### Service Container

```python
# bobreview/services/__init__.py
from typing import Dict, Any, Optional

class ServiceContainer:
    """Dependency injection container for services."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
    
    def register(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service
    
    def register_factory(self, name: str, factory: callable) -> None:
        """Register a lazy factory for a service."""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get a service by name."""
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            self._services[name] = self._factories[name]()
            return self._services[name]
        raise KeyError(f"Service not found: {name}")
    
    def replace(self, name: str, service: Any) -> None:
        """Replace a service (for plugins to override core services)."""
        self._services[name] = service
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services or name in self._factories
```

### Core Services

| Service | Responsibility | Plugin Can Override? |
|---------|----------------|---------------------|
| `DataService` | Parse input files, validate data | ✅ Add new parsers |
| `AnalyticsService` | Calculate statistics, outliers | ✅ Add custom analyzers |
| `LLMService` | Generate AI content | ✅ Add generators |
| `ChartService` | Render Chart.js configs | ✅ Add chart types |
| `WidgetService` | Render widgets to HTML | ✅ Add widgets |
| `RenderService` | Orchestrate page rendering | ✅ Add page templates |
| `ThemeService` | Apply CSS variables and styling | ✅ Add themes |

### Service Interface Examples

```python
# bobreview/services/data_service.py
from abc import ABC, abstractmethod

class DataService(ABC):
    """Service for parsing and validating input data."""
    
    @abstractmethod
    def parse(self, file_path: Path, config: DataSourceConfig) -> List[Dict]:
        """Parse input file and return data points."""
        ...
    
    @abstractmethod
    def validate(self, data: List[Dict], schema: MetricsConfig) -> ValidationResult:
        """Validate data against expected schema."""
        ...


# bobreview/services/analytics_service.py
class AnalyticsService(ABC):
    """Service for statistical analysis."""
    
    @abstractmethod
    def calculate_stats(self, data: List[Dict], metrics: List[str]) -> Dict[str, MetricStats]:
        """Calculate statistics for each metric."""
        ...
    
    @abstractmethod
    def detect_outliers(self, data: List[Dict], method: str = 'iqr') -> List[int]:
        """Detect outlier indices in data."""
        ...
```

### Report Pipeline

```python
# bobreview/services/pipeline.py
from pathlib import Path
from .container import ServiceContainer

class ReportPipeline:
    """Orchestrates report generation using pluggable services."""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
    
    async def execute(
        self, 
        definition: ReportSystemDefinition, 
        input_file: Path
    ) -> ReportResult:
        """Execute the full report generation pipeline."""
        
        # 1. Parse data
        data_service = self.container.get('data')
        data = await data_service.parse(input_file, definition.data_source)
        
        # 2. Validate
        validation = await data_service.validate(data, definition.metrics)
        if not validation.is_valid:
            raise ValidationError(validation.errors)
        
        # 3. Analyze
        analytics = self.container.get('analytics')
        stats = await analytics.calculate_stats(data, definition.metrics.keys())
        
        # 4. Generate LLM content (if configured)
        llm_content = {}
        if definition.llm_config.enabled:
            llm = self.container.get('llm')
            llm_content = await llm.generate_all(stats, definition.llm_generators)
        
        # 5. Build context
        context = DataContext(
            data=data,
            stats=stats,
            llm=llm_content,
            config=definition.config,
            labels=definition.labels,
            content=definition.content_blocks
        )
        
        # 6. Generate charts
        charts = self.container.get('charts')
        chart_data = await charts.generate_all(definition.charts, context)
        context.charts = chart_data
        
        # 7. Render pages
        render = self.container.get('render')
        pages = await render.render_all(definition.pages, context)
        
        return ReportResult(
            pages=pages,
            stats=stats,
            charts=chart_data,
            output_dir=definition.output.directory
        )
```

---

## AvaloniaUI Integration

### Communication Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AvaloniaUI GUI                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ Widget  │  │  Page   │  │ Preview │             │
│  │ Palette │  │ Canvas  │  │  Panel  │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
│       │            │            │                   │
└───────┼────────────┼────────────┼───────────────────┘
        │ JSON-RPC   │ JSON-RPC   │ HTTP
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────┐
│              Python Plugin Host                      │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────────┐ │
│  │   Widget    │ │   Report    │ │    Preview     │ │
│  │   Schema    │ │   Editor    │ │    Renderer    │ │
│  │   Endpoint  │ │   Endpoint  │ │    Endpoint    │ │
│  └─────────────┘ └─────────────┘ └────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### GUI Bridge API

```python
# bobreview/gui/bridge.py
from typing import List, Dict, Any, Optional

class GUIBridge:
    """API for AvaloniaUI communication via JSON-RPC."""
    
    def __init__(self, registry: PluginRegistry, container: ServiceContainer):
        self.registry = registry
        self.container = container
    
    # ─────────────────────────────────────────────────
    # Widget Discovery
    # ─────────────────────────────────────────────────
    
    def get_widget_catalog(self) -> List[WidgetInfo]:
        """Get all available widgets for the palette."""
        return [
            WidgetInfo(
                type=w.widget_type,
                name=w.display_name,
                category=w.category,
                icon=w.icon,
                preview_html=w.get_preview_html()
            )
            for w in self.registry.get_all_widgets()
        ]
    
    def get_widget_schema(self, widget_type: str) -> Dict[str, Any]:
        """Get JSON Schema for a widget's properties."""
        widget = self.registry.get_widget(widget_type)
        return widget.get_props_schema()
    
    # ─────────────────────────────────────────────────
    # Report Definition CRUD
    # ─────────────────────────────────────────────────
    
    def get_report_definition(self, report_id: str) -> Dict:
        """Load a report system definition."""
        ...
    
    def save_report_definition(self, report_id: str, data: Dict) -> None:
        """Save a report system definition."""
        ...
    
    def create_report(self, name: str, template: Optional[str] = None) -> str:
        """Create a new report, optionally from a template."""
        ...
    
    # ─────────────────────────────────────────────────
    # Component Editing
    # ─────────────────────────────────────────────────
    
    def add_component(self, page_id: str, component: Dict) -> str:
        """Add a component to a page. Returns component ID."""
        ...
    
    def update_component(self, comp_id: str, props: Dict) -> None:
        """Update component properties."""
        ...
    
    def delete_component(self, comp_id: str) -> None:
        """Delete a component."""
        ...
    
    def move_component(self, comp_id: str, new_position: int) -> None:
        """Reorder a component within its page."""
        ...
    
    # ─────────────────────────────────────────────────
    # Live Preview
    # ─────────────────────────────────────────────────
    
    def render_page_preview(self, page_id: str, sample_data: Dict) -> str:
        """Render a page preview with sample data."""
        ...
    
    def render_widget_preview(self, widget_type: str, props: Dict) -> str:
        """Render a single widget preview."""
        ...
    
    # ─────────────────────────────────────────────────
    # Plugin Management
    # ─────────────────────────────────────────────────
    
    def get_installed_plugins(self) -> List[PluginInfo]:
        """List all installed plugins."""
        ...
    
    def install_plugin(self, path: str) -> None:
        """Install a plugin from a path."""
        ...
    
    def uninstall_plugin(self, name: str) -> None:
        """Uninstall a plugin."""
        ...
    
    def get_plugin_config(self, name: str) -> Dict:
        """Get plugin configuration."""
        ...
    
    def set_plugin_config(self, name: str, config: Dict) -> None:
        """Update plugin configuration."""
        ...
```

### JSON-RPC Server

```python
# bobreview/gui/server.py
from jsonrpcserver import method, serve

class GUIServer:
    """JSON-RPC server for AvaloniaUI communication."""
    
    def __init__(self, bridge: GUIBridge, port: int = 8765):
        self.bridge = bridge
        self.port = port
    
    def start(self):
        """Start the JSON-RPC server."""
        serve(self.port)
    
    @method
    def widget_catalog(self) -> list:
        return self.bridge.get_widget_catalog()
    
    @method
    def widget_schema(self, widget_type: str) -> dict:
        return self.bridge.get_widget_schema(widget_type)
    
    @method
    def add_component(self, page_id: str, component: dict) -> str:
        return self.bridge.add_component(page_id, component)
    
    # ... more methods
```

---

## Implementation Phases

### Phase 1: Plugin Foundation ⬅️ **Start Here**

**Goal**: Establish the plugin infrastructure that enables all future extensibility.

**Tasks**:
- [ ] Create `bobreview/plugins/` package structure
- [ ] Implement `BasePlugin` abstract base class
- [ ] Implement `PluginRegistry` with registration methods
- [ ] Implement `PluginLoader` with directory discovery
- [ ] Add `manifest.json` schema and validation
- [ ] Wire plugin loading into CLI startup (`cli.py`)
- [ ] Add CLI commands: `bob plugins list|install|uninstall|info`
- [ ] Add plugin configuration to `~/.bobreview/config.yaml`

**Deliverables**:
- Working plugin system that can load/unload plugins
- At least one example plugin in `examples/plugins/`
- Documentation for plugin developers

---

### Phase 2: Service Decomposition

**Goal**: Break apart the monolithic executor into pluggable services.

**Tasks**:
- [ ] Create `bobreview/services/` package structure
- [ ] Implement `ServiceContainer` for dependency injection
- [ ] Extract `DataService` from `executor.py`
- [ ] Extract `AnalyticsService` from `executor.py`
- [ ] Extract `ChartService` from `_generate_charts()`
- [ ] Create `ReportPipeline` orchestrator
- [ ] Allow plugins to register/replace services
- [ ] Maintain backward compatibility with existing API

**Deliverables**:
- Services can be individually tested
- Plugins can inject custom services
- Original CLI commands continue to work

---

### Phase 3: Widget System

**Goal**: Create a registry of composable, plugin-extensible widgets.

**Tasks**:
- [ ] Create `bobreview/widgets/` package structure
- [ ] Implement `BaseWidget` abstract base class
- [ ] Implement widget registry with `register_widget()`, `get_widget()`
- [ ] Extract `StatCardWidget` from `macros.html.j2`
- [ ] Extract `ChartWidget` from executor chart logic
- [ ] Extract `TableWidget` from template macros
- [ ] Create `ComponentRenderer` for widget-based pages
- [ ] Add JSON Schema export for all widget properties
- [ ] Update page templates to optionally render from components

**Deliverables**:
- All core UI elements available as widgets
- Widgets can be added via plugins
- JSON Schema available for GUI property editors

---

### Phase 4: GUI Bridge

**Goal**: Enable AvaloniaUI to communicate with the Python backend.

**Tasks**:
- [ ] Create `bobreview/gui/` package structure
- [ ] Implement `GUIBridge` API class
- [ ] Add JSON-RPC server with all endpoints
- [ ] Implement widget catalog endpoint
- [ ] Implement live preview rendering
- [ ] Add report definition CRUD operations
- [ ] Add WebSocket support for real-time updates
- [ ] Create CLI command: `bob gui-server`

**Deliverables**:
- Running JSON-RPC server that AvaloniaUI can connect to
- Full widget catalog with schemas
- Live preview of pages with sample data

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| **Malicious plugins** | Plugin signing, permission model, sandboxed execution in future |
| **Path traversal** | Validate plugin paths, no absolute path escapes, chroot-style isolation |
| **Code injection** | No `eval()` or `exec()`, sanitize all template inputs |
| **Resource exhaustion** | Plugin timeout limits, memory caps, async execution |
| **Dependency confusion** | Pin plugin dependencies, verify checksums |

### Permission Model (Future)

```json
{
  "permissions": {
    "network": false,
    "filesystem": ["read"],
    "execute": false
  }
}
```

---

## Configuration

### Plugin Configuration

```yaml
# ~/.bobreview/config.yaml
plugins:
  # Directories to search for plugins
  directories:
    - ~/.bobreview/plugins
    - ./project_plugins
  
  # Explicitly enabled plugins (others are disabled)
  enabled:
    - network-diagram
    - custom-analytics
  
  # Explicitly disabled plugins
  disabled:
    - experimental-charts
  
  # Per-plugin settings
  settings:
    network-diagram:
      api_key: ${NETWORK_API_KEY}
      timeout: 30

# GUI server configuration
gui:
  port: 8765
  host: localhost
  cors_origins:
    - http://localhost:*
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOBREVIEW_PLUGIN_DIR` | Additional plugin directory | None |
| `BOBREVIEW_GUI_PORT` | GUI server port | 8765 |
| `BOBREVIEW_DEV_MODE` | Enable hot reload | false |

---

## Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Plugin Discovery** | `manifest.json` entry point | Standard pattern, easy validation |
| **Service Override** | `container.replace()` | Plugins can swap core services |
| **Widget Schema** | JSON Schema | AvaloniaUI property editor support |
| **Communication** | JSON-RPC | Simple, cross-platform, debuggable |
| **Hot Reload** | Development mode only | Performance in production |
| **Persistence** | JSON files (for now) | Database-ready interfaces for future |

---

## Next Steps

1. **Review this document** and provide feedback
2. **Approve Phase 1** to begin plugin foundation work
3. **Identify priority widgets** for Phase 3
4. **Define AvaloniaUI requirements** for Phase 4

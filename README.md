# BobReview

**Extensible Report Generation Framework** — Generate professional HTML reports from any data using LLM-powered analysis.

![Version](https://img.shields.io/badge/version-1.0.7-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## What is BobReview?

BobReview is a **plugin-based framework** for generating data-driven reports with AI insights. Instead of hardcoding analysis logic, everything is provided by plugins:

- **Data Parsers** — Parse CSV, JSON, images, or any custom format
- **Report Systems** — Define analysis pipelines in JSON
- **LLM Analysis** — AI-powered insights using OpenAI, Anthropic, or Ollama
- **Templates & Themes** — Beautiful, customizable HTML reports

**Create your own plugin in 30 seconds:**

```bash
pip install .
bobreview plugins create my-plugin
bobreview --plugin my-plugin --dir ~/.bobreview/plugins/my_plugin/sample_data
```

---

## Quick Start

### 1. Install
```bash
git clone https://github.com/DiggingNebula8/bobreview.git
cd bobreview
pip install .
```

### 2. Set API Key
```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-your-key

# Or use Anthropic Claude
export ANTHROPIC_API_KEY=your-key

# Or use local Ollama (no key needed)
ollama serve
```

### 3. Create Your First Plugin
```bash
bobreview plugins create my-analytics
```

This creates a complete plugin in `~/.bobreview/plugins/my_analytics/` with:
- CSV data parser
- Report system JSON
- Jinja2 templates with LLM sections
- Sample data to test with

### 4. Generate a Report
```bash
bobreview --plugin my-analytics --dir ~/.bobreview/plugins/my_analytics/sample_data

# Test without LLM calls
bobreview --plugin my-analytics --dir ~/.bobreview/plugins/my_analytics/sample_data --dry-run
```

### 5. Open the Report
```bash
start report.html   # Windows
open report.html    # macOS
xdg-open report.html # Linux
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Plugin Scaffolding** | `bobreview plugins create` generates a complete plugin structure |
| **PluginHelper API** | Simple facade for registering parsers, themes, templates |
| **Custom CSS Themes** | Separate `theme.css` and `plugin.css` for easy customization |
| **Multi-LLM Support** | OpenAI, Anthropic Claude, local Ollama |
| **JSON Report Systems** | Define analysis pipelines declaratively |
| **Markdown → HTML** | LLM responses rendered with beautiful styling |
| **Intelligent Caching** | Cache LLM responses to save costs |
| **Standalone HTML** | Images embedded as base64 for easy sharing |
| **Extensible Registry** | 13 registries for themes, parsers, generators, etc. |

---

## Creating Plugins

### Scaffold a New Plugin

```bash
# Full plugin with default theme
bobreview plugins create my-plugin

# Choose a color theme
bobreview plugins create my-plugin --theme ocean      # Teal/cyan
bobreview plugins create my-plugin --theme purple     # Purple/violet
bobreview plugins create my-plugin --theme terminal   # Green/black
bobreview plugins create my-plugin --theme sunset     # Orange/warm

# Minimal plugin (parser + templates only)
bobreview plugins create my-plugin --template minimal
```

### Plugin Structure

```text
my_plugin/
├── manifest.json           # Plugin metadata
├── plugin.py               # Main plugin class (on_load registration)
├── parsers/
│   └── csv_parser.py       # Data parser implementation
├── context_builder.py      # Custom template context
├── chart_generator.py      # Chart.js configuration
├── report_systems/
│   └── my_plugin.json      # Report system definition
├── templates/
│   └── my_plugin/
│       ├── pages/
│       │   ├── base.html.j2    # Base template
│       │   └── home.html.j2    # Homepage with LLM content
│       └── static/
│           ├── theme.css       # Color scheme (customize me!)
│           └── plugin.css      # Layout and components
└── sample_data/
    └── sample.csv          # Example data
```

### Plugin Code (plugin.py)

```python
from pathlib import Path
from bobreview.core.plugin_system import BasePlugin, PluginHelper

class MyPlugin(BasePlugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def on_load(self, registry) -> None:
        helper = PluginHelper(registry, self.name)
        
        # Register data parser
        from .parsers.csv_parser import MyCsvParser
        helper.add_data_parser("my_csv", MyCsvParser)
        
        # Register templates
        helper.add_templates(Path(__file__).parent / "templates")
        
        # Register report systems
        helper.add_report_systems_from_dir(Path(__file__).parent / "report_systems")
        
        # Register default services (analytics, charts, data)
        helper.register_default_services()
```

---

## CLI Reference

### Basic Usage

```bash
bobreview --plugin <name> --dir <data-path>
bobreview --plugin <name> --dir ./data --output report.html
bobreview --plugin <name> --dir ./data --title "Q4 Analysis"
```

### Plugin Management

```bash
bobreview plugins list                    # List installed plugins
bobreview plugins create my-plugin        # Create new plugin
bobreview plugins create my-plugin --template minimal
```

### LLM Configuration

```bash
--llm-provider openai|anthropic|ollama   # LLM provider
--llm-model gpt-4o                       # Model name
--llm-api-key sk-...                     # API key
--llm-temperature 0.7                    # Creativity (0-2)
```

### Execution Options

```bash
--dry-run              # Skip LLM calls (for testing)
--sample 20            # Process N random samples
--verbose              # Detailed output
--no-cache             # Disable caching
--clear-cache          # Clear cache before run
```

---

## Customizing Themes

BobReview uses a **unified theme system** with 7 built-in themes. Themes support inheritance and can be customized via JSON or CLI.


### Built-in Themes

| Theme ID | Name | Style |
|----------|------|-------|
| `dark` | Dark (Default) | Blue accent, deep black |
| `light` | Light | Blue accent, white bg |
| `high_contrast` | High Contrast | Cyan/yellow, accessibility |
| `ocean` | Ocean Dark | Teal/cyan, Inter font |
| `purple` | Purple Night | Violet, Dracula-style |
| `terminal` | Terminal Green | Green, JetBrains Mono |
| `sunset` | Sunset Warm | Orange, Outfit font |

### Switching Themes

**Via JSON** (in `report_systems/*.json`):

Edit your `report_systems/<plugin>.json`:

```json
{
  "theme": {
    "preset": "ocean"
  }
}
```

### Creating Custom Plugin Themes

There are two ways to create custom themes:

#### Quick Start: Extend a Built-in Theme

Use `create_theme` to quickly customize an existing theme:

```python
from bobreview.core.themes import create_theme, hex_to_rgba

# Extend dark theme with custom colors
MY_THEME = create_theme(
    'neon', 'Neon Pink',
    base='dark',                              # Inherit all dark theme values
    accent='#ff2d95',                         # Override accent
    accent_soft=hex_to_rgba('#ff2d95', 0.15), # Soft variant
)
```

#### Full Control: Define Every Property

Use `ReportTheme` for complete control over all values:

```python
from bobreview.core.themes import ReportTheme

# Complete theme from scratch
MY_THEME = ReportTheme(
    id='cyberpunk',
    name='Cyberpunk',
    bg='#0a0a0f',
    bg_elevated='#13131a',
    bg_soft='#1a1a24',
    accent='#ff2d95',
    accent_soft='rgba(255, 45, 149, 0.15)',
    accent_strong='#00f0ff',
    text_main='#e4e4f0',
    text_soft='#8888a0',
    ok='#00ff88',
    warn='#ffcc00',
    danger='#ff3366',
    border_subtle='#2a2a3a',
    # ... all 20+ properties available
)
```

#### Register Your Theme

```python
from bobreview.core.plugin_system import BasePlugin, PluginHelper

class MyPlugin(BasePlugin):
    def on_load(self, registry):
        helper = PluginHelper(registry, self.name)
        helper.add_theme(MY_THEME)
```

Then use in JSON: `"theme": { "preset": "neon" }`

**Via CLI** (override at runtime):

```bash
# Use built-in theme
bobreview --plugin my-plugin --dir ./data --theme ocean

# Use your custom plugin theme
bobreview --plugin my-plugin --dir ./data --theme neon
```

### Available Theme Properties

| Property | Purpose |
|----------|---------|
| `bg` | Main background |
| `bg_elevated` | Cards, panels |
| `bg_soft` | Subtle backgrounds |
| `accent` | Primary brand color |
| `accent_soft` | Accent with transparency |
| `accent_strong` | Emphasized accent |
| `text_main` | Primary text |
| `text_soft` | Secondary text |
| `ok` / `warn` / `danger` | Status colors |
| `border_subtle` | Border colors |
| `shadow_soft` | Box shadow |
| `radius_lg` / `radius_md` | Border radius |
| `font_family` / `font_mono` | Typography |

### Available CSS Variables

| Variable | Purpose |
|----------|---------|
| `--bg` | Main page background |
| `--bg-elevated` | Cards, panels |
| `--bg-soft` | Subtle background areas |
| `--bg-hover` | Hover states with alpha |
| `--accent` | Primary brand color |
| `--accent-soft` | Accent with transparency (badges, code) |
| `--accent-strong` | Emphasized accent (gradients) |
| `--text-main` | Primary text color |
| `--text-soft` | Secondary/muted text |
| `--ok` / `--warn` / `--danger` | Status colors |
| `--border` | Border colors |
| `--radius-sm/md/lg/xl` | Border radius sizes |
| `--font-family` | Body text font |
| `--font-mono` | Code font |

### plugin.css — Layout & Components

Customize layout, cards, tables, and LLM content styling:

```css
/* Larger cards */
.card { border-radius: 20px; padding: 2rem 3rem; }

/* Status badges */
.badge-ok { background: var(--ok-soft); color: var(--ok); }

/* LLM bold text */
.llm-content strong { color: var(--accent); }

/* Custom header */
header h1 { font-size: 3rem; text-transform: uppercase; }
```

---

## Report Systems

Report systems are JSON files that define your analysis pipeline:

```json
{
  "schema_version": "1.0",
  "id": "my_report",
  "name": "My Analysis Report",
  
  "data_source": {
    "type": "my_csv",
    "input_format": "csv"
  },
  
  "llm_config": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  
  "llm_generators": [
    {
      "id": "summary",
      "name": "Executive Summary",
      "prompt_template": "Analyze this data and provide insights.",
      "data_table": {
        "columns": ["name", "score"],
        "max_rows": 50
      }
    }
  ],
  
  "pages": [
    {
      "id": "home",
      "filename": "index.html",
      "template": { "type": "jinja2", "name": "my_plugin/pages/home.html.j2" },
      "llm_content": ["summary"]
    }
  ]
}
```

---

## Architecture

```text
bobreview/
├── cli.py                    # Command-line interface
├── core/
│   ├── plugin_system/        # Plugin infrastructure
│   │   ├── loader.py         # Plugin discovery & loading
│   │   ├── registry.py       # Component registration
│   │   ├── plugin_helper.py  # PluginHelper facade
│   │   ├── scaffolder.py     # Plugin scaffolding
│   │   └── registries/       # 13 focused registries
│   ├── template_engine.py    # Jinja2 with custom filters
│   ├── html_utils.py         # Markdown→HTML, sanitization
│   └── config.py             # ReportConfig
├── engine/
│   ├── executor.py           # Report generation orchestration
│   ├── page_renderer.py      # Template rendering
│   └── schema.py             # Report system dataclasses
├── services/
│   ├── llm_service.py        # LLM content generation
│   ├── analytics_service.py  # Statistical analysis
│   └── chart_service.py      # Chart.js generation
└── plugins/                  # (empty - create with scaffolder)
```

**Design Principles:**
- **Plugin-First** — All functionality provided by plugins
- **SOLID** — Single responsibility, interface segregation
- **Registry Pattern** — Self-registration for all extension points
- **Dependency Injection** — Testable, modular components

---

## Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Getting started tutorial |
| [CORE_API.md](CORE_API.md) | Complete API reference |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## Troubleshooting

### Plugin Not Found
```bash
# Check plugin is in a discoverable location
bobreview plugins list

# Plugin locations (in priority order):
# 1. --plugin-dir <path>
# 2. $BOBREVIEW_PLUGIN_DIRS
# 3. ~/.bobreview/plugins/
# 4. ./plugins/
# 5. Bundled plugins
```

### API Key Not Found
```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key

# Or pass via CLI
bobreview --plugin my-plugin --dir ./data --llm-api-key sk-your-key

# Or use local Ollama (no key needed)
bobreview --plugin my-plugin --dir ./data --llm-provider ollama --llm-model llama2
```

### LLM Markdown Not Rendering
Ensure templates use the `| sanitize` filter:
```jinja
{{ llm.summary | sanitize }}
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---



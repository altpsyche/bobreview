"""
Report Builder Service.

Builds reports from user-defined YAML configurations using plugin components.
Converts user config to ReportSystemDefinition and delegates to ReportSystemExecutor.

Data Flow:
    User YAML → ReportBuilder → DataService.parse_dataframe() → DataFrame
                                                                    ↓
                                                        ReportSystemExecutor
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from glob import glob

from .report_config import UserConfig, load_user_config, validate_user_config
from .config import Config, load_config
from .dataframe import DataFrame
from .plugin_system.registry import get_registry
from .plugin_system.loader import get_loader
from ..engine.schema import ReportSystemDefinition, DataSourceConfig, PageConfig as SystemPageConfig, ChartConfig, LLMGeneratorConfig, TemplateConfig, DataTableConfig
from ..engine.executor import ReportSystemExecutor
from .template_engine import get_template_engine

logger = logging.getLogger(__name__)


class ReportBuilder:
    """
    Builds reports from user YAML configuration.
    
    Workflow:
    1. Load user's report_config.yaml
    2. Parse data via DataService.parse_dataframe() → DataFrame
    3. Convert to ReportSystemDefinition
    4. Delegate to ReportSystemExecutor for rendering
    
    Example:
        builder = ReportBuilder()
        result = builder.build("my_report.yaml")
    """
    
    def __init__(self):
        """Initialize the report builder."""
        self.registry = get_registry()
        self.loader = get_loader()
        self._dataframe: Optional[DataFrame] = None  # Parsed data
    
    def build(
        self,
        config_path: str,
        output_dir: Optional[str] = None,
        dry_run: bool = False,
        config: Optional['Config'] = None,
        input_dir: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a report from a user configuration file.
        
        Parameters:
            config_path: Path to report YAML config
            output_dir: Override output directory
            dry_run: If True, validate only without generating
            config: Optional CLI config (Config) for LLM, cache settings
            input_dir: Override data input directory (from --dir)
            output_file: Override output filename (from --output)
            
        Returns:
            Build result with status and output paths
        """
        # Clean up any inline widgets from previous builds
        self.registry.unregister_plugin_components('_inline')
        
        # Load and validate user config
        user_config = load_user_config(config_path)
        errors = validate_user_config(user_config)
        
        if errors:
            return {
                'success': False,
                'errors': errors,
                'config_path': config_path
            }
        
        logger.info(f"Building report: {user_config.name}")
        
        # Load the plugin (required)
        if not user_config.plugin:
            return {
                'success': False,
                'errors': ["Plugin is required. Specify 'plugin' in config."],
                'config_path': config_path
            }
        
        try:
            self.loader.load(user_config.plugin)
            logger.info(f"Loaded plugin: {user_config.plugin}")
            # Force template engine refresh to pick up newly loaded plugin templates
            get_template_engine(force_refresh=True)
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Failed to load plugin '{user_config.plugin}': {e}"],
                'config_path': config_path
            }
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'name': user_config.name,
                'plugin': user_config.plugin,
                'pages': [p.id for p in user_config.pages],
                'components_per_page': {
                    p.id: len(p.components) for p in user_config.pages
                }
            }
        
        # Convert user config to ReportSystemDefinition
        # Note: This may register inline widgets, so we need cleanup in finally
        system_def = self._to_system_definition(user_config)
        
        try:
            # ────────────────────────────────────────────────────────────────────────
            # RESOLVE CONFIGURATION (CLI > YAML > JSON > Defaults)
            # ────────────────────────────────────────────────────────────────────────
            
            # Load JSON config from plugin
            json_config = self._load_json_config(user_config.plugin)
            
            # Build CLI args dict
            cli_args = {}
            if output_dir:
                cli_args['output_dir'] = output_dir
            if output_file:
                cli_args['output_file'] = output_file
            if input_dir:
                cli_args['input_dir'] = input_dir
            if config:
                # Extract CLI settings from flat Config
                if hasattr(config, 'llm_provider'):
                    if config.llm_provider:
                        cli_args['provider'] = config.llm_provider
                    if config.llm_model:
                        cli_args['model'] = config.llm_model
                    if config.llm_temperature:
                        cli_args['temperature'] = config.llm_temperature
                if config.title:
                    cli_args['title'] = config.title
                if hasattr(config, 'theme') and config.theme:
                    cli_args['theme'] = config.theme
            
            # Resolve config with precedence: CLI > passed config > JSON > Defaults
            report_config = load_config(
                cli_args=cli_args if cli_args else None,
                json_data=json_config
            )
            
            # Override with passed config values (from CLI main())
            if config:
                if config.llm_provider:
                    report_config.llm_provider = config.llm_provider
                if config.llm_model:
                    report_config.llm_model = config.llm_model
                if config.llm_api_key:
                    report_config.llm_api_key = config.llm_api_key
                if config.theme:
                    report_config.theme = config.theme
                if config.verbose:
                    report_config.verbose = config.verbose
                if config.dry_run:
                    report_config.dry_run = config.dry_run
            
            logger.info(f"Config resolved: provider={report_config.llm_provider}, theme={report_config.theme}")
            
            # ────────────────────────────────────────────────────────────────────────
            # APPLY RESOLVED CONFIG
            # ────────────────────────────────────────────────────────────────────────
            
            # Output directory
            output = Path(output_dir) if output_dir else Path(report_config.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            
            # Find input data
            if input_dir:
                data_dir = Path(input_dir)
                if not data_dir.exists():
                    return {
                        'success': False,
                        'errors': [f"Input directory not found: {data_dir}"],
                        'config_path': config_path
                    }
            else:
                # Try to find data from user config's data_source pattern
                data_source_pattern = user_config.data_source if hasattr(user_config, 'data_source') else './*.csv'
                data_dir = self._resolve_data_source(data_source_pattern)
                if not data_dir:
                    return {
                        'success': False,
                        'errors': ["No data found. Use --dir to specify input directory."],
                        'config_path': config_path
                    }
            
            # Execute via ReportSystemExecutor
            executor = ReportSystemExecutor(
                system_def=system_def,
                config=report_config
            )
            
            # Determine output path
            if output_file:
                output_path = Path(output_file)
            else:
                output_path = output / "index.html"
            
            success = executor.execute(data_dir, output_path)
            
            return {
                'success': success,
                'config_path': config_path,
                'output_dir': str(output),
                'output_path': str(output_path) if success else None,
            }
        except Exception as e:
            logger.exception(f"Build failed: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'config_path': config_path
            }
        finally:
            # Clean up inline widgets registered during this build
            self.registry.unregister_plugin_components('_inline')
    
    def _to_system_definition(self, user_config: UserConfig) -> ReportSystemDefinition:
        """Convert user YAML config to ReportSystemDefinition."""
        # Collect inline LLM generators defined in YAML
        inline_generators = []
        
        # Build pages from user config
        pages = []
        for page in user_config.pages:
            # Extract charts and LLM content from components
            charts = []
            llm_content = []
            
            for i, comp in enumerate(page.components):
                comp_type = comp.get('type', '')
                
                if comp_type == 'chart':
                    charts.append(ChartConfig(
                        id=comp.get('id', f"chart_{len(charts)}"),
                        type=comp.get('chart', 'bar'),
                        title=comp.get('title', ''),
                        x_field=comp.get('x', ''),
                        y_field=comp.get('y', '')
                    ))
                elif comp_type == 'llm':
                    # Check if it's an inline definition (has 'prompt') or reference (has 'generator')
                    if 'prompt' in comp:
                        # Inline LLM definition - create generator on the fly
                        gen_id = comp.get('id', f"inline_{page.id}_{len(inline_generators)}")
                        prompt = comp['prompt']
                        
                        # Extract data fields from prompt using {{field}} syntax
                        fields = self._extract_field_refs(prompt)
                        
                        # Build DataTableConfig if data_table specified
                        data_table_config = None
                        data_table_data = comp.get('data_table', {
                            'columns': fields if fields else ['name', 'score'],
                            'sample_strategy': 'all',
                            'max_rows': comp.get('max_rows', 50)
                        })
                        if data_table_data:
                            data_table_config = DataTableConfig(
                                columns=data_table_data.get('columns', fields if fields else ['name', 'score']),
                                sample_strategy=data_table_data.get('sample_strategy', 'all'),
                                max_rows=data_table_data.get('max_rows', 50)
                            )
                        
                        inline_generators.append(LLMGeneratorConfig(
                            id=gen_id,
                            name=comp.get('title', gen_id),
                            description=comp.get('description', f'User-defined LLM content for {page.title}'),
                            prompt_template=prompt,
                            data_table=data_table_config,
                            returns='string',
                            enabled=True
                        ))
                        llm_content.append(gen_id)
                    elif 'generator' in comp:
                        # Reference to JSON-defined generator
                        llm_content.append(comp['generator'])
                
                elif comp_type == 'widget':
                    # Widgets can have inline templates
                    if 'template' in comp:
                        # Inline widget with custom template
                        widget_id = comp.get('id', f"widget_{page.id}_{i}")
                        # Register inline widget for this build
                        self._register_inline_widget(widget_id, comp)
            
            # Auto-discover template: plugin-specific → layout-based → generic
            template_name = self._resolve_template(
                user_config.plugin,
                page.id,
                page.layout if hasattr(page, 'layout') else 'default'
            )
            
            pages.append(SystemPageConfig(
                id=page.id,
                filename=f"{page.id}.html",
                nav_label=page.title,
                nav_order=page.nav_order,
                template=TemplateConfig(type='jinja2', name=template_name),
                charts=charts,
                llm_content=llm_content,
                enabled=page.enabled
            ))
        
        # Load capabilities from plugin's JSON file (data_source, theme only)
        # NOTE: LLM generators are defined inline in YAML, NOT in JSON
        data_source_type = f"{user_config.plugin.replace('-', '_')}_csv"  # default
        input_format = "csv"  # default
        description = ""
        author = ""
        
        plugin_path = self._get_plugin_path(user_config.plugin)
        if plugin_path:
            json_file = plugin_path / 'report_systems' / f"{user_config.plugin.replace('-', '_')}.json"
            if json_file.exists():
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    system_data = json.load(f)
                    # Load capabilities from JSON (parser, theme)
                    data_source = system_data.get('data_source', {})
                    data_source_type = data_source.get('type', data_source_type)
                    input_format = data_source.get('input_format', input_format)
                    description = system_data.get('description', '')
                    author = system_data.get('author', '')
        
        return ReportSystemDefinition(
            schema_version="1.0",
            id=user_config.plugin,
            name=user_config.name,
            version=user_config.version,
            description=description or user_config.description,
            author=author or user_config.author,
            data_source=DataSourceConfig(type=data_source_type, input_format=input_format),
            pages=pages,
            llm_generators=inline_generators
        )
    
    def _resolve_data_source(self, pattern: str) -> Optional[Path]:
        """Resolve data source pattern to input directory."""
        matches = glob(pattern)
        if matches:
            # Return parent directory of first match
            return Path(matches[0]).parent
        return None
    
    def _get_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """Get the filesystem path for a plugin."""
        # Normalize plugin name for matching
        plugin_name_normalized = plugin_name.lower().replace('-', '_').replace(' ', '')
        
        for manifest in self.loader.get_discovered_plugins():
            manifest_name_normalized = manifest.name.lower().replace('-', '_').replace(' ', '')
            if manifest.name == plugin_name or manifest_name_normalized == plugin_name_normalized:
                if manifest.path:
                    return Path(manifest.path)
        return None
    
    def _load_json_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Load full JSON config from plugin's report_systems file."""
        plugin_path = self._get_plugin_path(plugin_name)
        if plugin_path:
            safe_name = plugin_name.replace('-', '_')
            json_file = plugin_path / 'report_systems' / f"{safe_name}.json"
            if json_file.exists():
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None
    
    # _load_llm_config_from_json() removed - use _load_json_config() with flat fields
    
    def _resolve_template(self, plugin_name: str, page_id: str, layout: str = 'default') -> str:
        """
        Auto-discover template with fallback chain.
        
        Search order:
        1. Plugin-specific page template: {plugin}/pages/{page_id}.html.j2
        2. Plugin layout template: {plugin}/layouts/{layout}.html.j2
        3. Generic layout template: _layouts/{layout}.html.j2
        4. Fallback: _layouts/default.html.j2
        
        Returns:
            Template name to use
        """
        plugin_path = self._get_plugin_path(plugin_name)
        
        if plugin_path:
            # Normalize plugin name for directory matching
            safe_name = plugin_name.replace('-', '_').replace(' ', '_')
            
            # 1. Plugin-specific page template: templates/{safe_name}/pages/{page_id}.html.j2
            page_template = plugin_path / 'templates' / safe_name / 'pages' / f"{page_id}.html.j2"
            if page_template.exists():
                return f"{safe_name}/pages/{page_id}.html.j2"
            
            # 2. Plugin layout template
            layout_template = plugin_path / 'templates' / 'layouts' / f"{layout}.html.j2"
            if layout_template.exists():
                return f"{plugin_name}/layouts/{layout}.html.j2"
        
        # 3. Generic layout (fallback)
        return f"_layouts/{layout}.html.j2"
    
    def _extract_field_refs(self, prompt: str) -> List[str]:
        """
        Extract data field references from a prompt.
        
        Supports syntax: {{field_name}} or {{ field_name }}
        
        Parameters:
            prompt: The prompt text to parse
            
        Returns:
            List of unique field names referenced in the prompt
        """
        import re
        # Match {{field}} or {{ field }} patterns
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        matches = re.findall(pattern, prompt)
        # Return unique fields in order of appearance
        seen = set()
        fields = []
        for field in matches:
            if field not in seen:
                seen.add(field)
                fields.append(field)
        return fields
    
    def _register_inline_widget(self, widget_id: str, config: Dict[str, Any]) -> None:
        """
        Register an inline widget definition for the current build.
        
        Inline widgets have their template defined directly in YAML:
        ```yaml
        - type: widget
          id: my_card
          title: "Custom Card"
          template: "<div class='card'>{{ title }}: {{ value }}</div>"
          config:
            value: "{{ stats.score.mean }}"
        ```
        
        Parameters:
            widget_id: Unique identifier for the widget
            config: Widget configuration from YAML
        """
        # Store inline widget for rendering
        # The template will be available via the registry for this session
        inline_template = config.get('template', '')
        widget_config = config.get('config', {})
        
        # Create a simple widget class dynamically
        class InlineWidget:
            def render(self, context: Dict[str, Any]) -> str:
                from jinja2 import Template
                tpl = Template(inline_template)
                return tpl.render(**widget_config, **context)
        
        # Register widget temporarily
        self.registry.widgets.register(
            widget_id, 
            InlineWidget, 
            plugin_name='_inline'
        )
    
    def list_available_components(self, plugin_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all available components from plugins.
        
        Parameters:
            plugin_name: Optional plugin to filter by (currently unused)
            
        Returns:
            Dict with component types and their IDs
        """
        widgets = self.registry.widgets.get_all()
        chart_types = self.registry.chart_types.get_all()
        analyzers = self.registry.analyzers.get_all()
        
        # TODO: Implement plugin_name filtering when component ownership tracking is available
        # if plugin_name:
        #     widgets = {k: v for k, v in widgets.items() if ...}
        
        return {
            'widgets': list(widgets.keys()),
            'chart_types': list(chart_types.keys()),
            'analyzers': list(analyzers.keys()),
            'data_parsers': list(self.registry.data_parsers.get_all().keys()),
            'themes': [t.id for t in self.registry.themes.get_all().values()],
        }


def get_report_builder() -> ReportBuilder:
    """Get a ReportBuilder instance."""
    return ReportBuilder()

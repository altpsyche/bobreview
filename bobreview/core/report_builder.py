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

from .report_config import UserReportConfig, load_user_report_config, validate_user_report_config
from .dataframe import DataFrame
from .plugin_system.registry import get_registry
from .plugin_system.loader import get_loader
from ..engine.schema import ReportSystemDefinition, DataSourceConfig, PageConfig as SystemPageConfig, ChartConfig, LLMGeneratorConfig
from ..engine.executor import ReportSystemExecutor
from ..core import ReportConfig as ExecutionConfig

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
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Build a report from a user configuration file.
        
        Parameters:
            config_path: Path to report YAML config
            output_dir: Override output directory
            dry_run: If True, validate only without generating
            
        Returns:
            Build result with status and output paths
        """
        # Load and validate user config
        user_config = load_user_report_config(config_path)
        errors = validate_user_report_config(user_config)
        
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
        system_def = self._to_system_definition(user_config)
        
        # Create execution config
        output = Path(output_dir or user_config.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        # Find input data
        input_dir = self._resolve_data_source(user_config.data_source)
        if not input_dir:
            return {
                'success': False,
                'errors': [f"No data found in: {user_config.data_source}"],
                'config_path': config_path
            }
        
        # Build report config for executor
        report_config = ExecutionConfig(
            title=user_config.name,
        )
        
        # Execute via ReportSystemExecutor
        try:
            executor = ReportSystemExecutor(
                system_def=system_def,
                config=report_config
            )
            
            output_path = output / "index.html"
            success = executor.execute(input_dir, output_path)
            
            return {
                'success': success,
                'config_path': config_path,
                'output_dir': str(output),
                'output_path': str(output_path) if success else None
            }
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'config_path': config_path
            }
    
    def _to_system_definition(self, user_config: UserReportConfig) -> ReportSystemDefinition:
        """Convert user YAML config to ReportSystemDefinition."""
        # Build pages from user config
        pages = []
        for page in user_config.pages:
            # Extract charts from components
            charts = []
            llm_content = []
            
            for comp in page.components:
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
                    llm_content.append(comp.get('generator', ''))
            
            pages.append(SystemPageConfig(
                id=page.id,
                filename=f"{page.id}.html",
                nav_label=page.title,
                nav_order=page.nav_order,
                template={'type': 'jinja2', 'name': f"{user_config.plugin}/{page.id}.html.j2"},
                charts=charts,
                llm_content=llm_content,
                enabled=page.enabled
            ))
        
        # Build LLM generators from referenced IDs
        llm_generators = []
        # Get from plugin's report system if available
        plugin_system = self.registry.report_systems.get(user_config.plugin)
        if plugin_system:
            llm_generators = plugin_system.get('llm_generators', [])
        
        return ReportSystemDefinition(
            schema_version="1.0",
            id=user_config.plugin,
            name=user_config.name,
            version=user_config.version,
            data_source=DataSourceConfig(type=f"{user_config.plugin}_csv"),
            pages=pages,
            llm_generators=llm_generators,
            theme={'preset': user_config.theme}
        )
    
    def _resolve_data_source(self, pattern: str) -> Optional[Path]:
        """Resolve data source pattern to input directory."""
        matches = glob(pattern)
        if matches:
            # Return parent directory of first match
            return Path(matches[0]).parent
        return None
    
    def list_available_components(self, plugin_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all available components from plugins.
        
        Parameters:
            plugin_name: Optional plugin to filter by
            
        Returns:
            Dict with component types and their IDs
        """
        return {
            'widgets': list(self.registry.widgets.get_all().keys()),
            'chart_types': list(self.registry.chart_types.get_all().keys()),
            'analyzers': list(self.registry.analyzers.get_all().keys()),
            'data_parsers': list(self.registry.data_parsers.get_all().keys()),
            'themes': [t.id for t in self.registry.themes.get_all().values()],
        }


def get_report_builder() -> ReportBuilder:
    """Get a ReportBuilder instance."""
    return ReportBuilder()

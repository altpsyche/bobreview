"""
Report pipeline orchestrator.

The ReportPipeline coordinates all services to generate a complete report.
It replaces the monolithic execute() method in ReportSystemExecutor.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from .container import ServiceContainer, get_container
from .base import ServiceError

logger = logging.getLogger(__name__)


class ReportPipeline:
    """
    Orchestrates report generation using pluggable services.
    
    The pipeline coordinates:
    1. Data parsing (DataService)
    2. Statistical analysis (AnalyticsService)
    3. LLM content generation (LLMService)
    4. Chart generation (ChartService)
    5. Page rendering (via template engine)
    
    Example:
        container = get_container()
        container.register('data', DataService())
        container.register('analytics', AnalyticsService())
        
        pipeline = ReportPipeline(container)
        result = pipeline.execute(system_def, input_dir, output_path, config)
    """
    
    def __init__(self, container: Optional[ServiceContainer] = None):
        """
        Initialize pipeline with service container.
        
        Parameters:
            container: ServiceContainer with registered services.
                       If None, uses global container.
        """
        self.container = container or get_container()
    
    def execute(
        self,
        system_def: Any,
        input_dir: Path,
        output_path: Path,
        config: Any
    ) -> Dict[str, Any]:
        """
        Execute the complete report generation pipeline.
        
        Parameters:
            system_def: ReportSystemDefinition from JSON
            input_dir: Directory containing input files
            output_path: Output path for report
            config: Config with settings
            
        Returns:
            Result dictionary with 'success', 'pages', 'stats', etc.
        """
        from ..core import log_info, log_verbose, log_warning
        
        result = {
            'success': False,
            'pages': [],
            'stats': {},
            'llm_content': {},
            'errors': []
        }
        
        try:
            log_info(f"Executing report: {system_def.name}", config)
            
            # Step 1: Parse data
            data_points = self._parse_data(system_def, input_dir, config)
            if not data_points:
                result['errors'].append("No data points found")
                return result
            
            log_info(f"Parsed {len(data_points)} data points", config)
            
            # Step 2: Analyze data
            stats = self._analyze_data(data_points, system_def, config)
            result['stats'] = stats
            log_info("Statistical analysis complete", config)
            
            # Step 3: Generate LLM content
            llm_content = self._generate_llm_content(
                data_points, stats, system_def, config
            )
            result['llm_content'] = llm_content
            log_info("LLM content generation complete", config)
            
            # Step 4: Generate charts (via ChartService if available)
            charts = self._generate_charts(data_points, system_def, config)
            
            # Step 5: Render pages
            # (This still uses the existing template engine)
            pages = self._render_pages(
                data_points, stats, llm_content, charts,
                system_def, input_dir, output_path, config
            )
            result['pages'] = pages
            
            result['success'] = True
            log_info(f"Report generated: {output_path}", config)
            
        except ServiceError as e:
            result['errors'].append(str(e))
            logger.exception(f"Pipeline failed: {e}")
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")
            logger.exception("Pipeline failed with unexpected error")
        
        return result
    
    def _parse_data(
        self,
        system_def: Any,
        input_dir: Path,
        config: Any
    ) -> List[Dict[str, Any]]:
        """Parse data using DataService."""
        # Get metrics from extensions (plugin-provided)
        metrics_ext = system_def.extensions.get('metrics', {})
        sort_by = metrics_ext.get('timestamp_field') if metrics_ext else None
        
        if self.container.has('data'):
            data_service = self.container.get('data')
            return data_service.parse(
                input_dir=input_dir,
                data_source_config=system_def.data_source,
                sample_size=config.sample_size,
                sort_by=sort_by
            )
        else:
            # Fallback to direct parsing using factory
            from ..engine.parser_factory import ParserFactory
            factory = ParserFactory()
            parser = factory.create(system_def.data_source)
            data = parser.parse_directory(input_dir)
            if config.sample_size:
                data = data[:config.sample_size]
            return data
    
    def _analyze_data(
        self,
        data_points: List[Dict[str, Any]],
        system_def: Any,
        config: Any
    ) -> Dict[str, Any]:
        """Analyze data using AnalyticsService."""
        # Get metrics from extensions (plugin-provided)
        metrics_ext = system_def.extensions.get('metrics', {})
        
        if not metrics_ext:
            # No metrics configured - return data as-is for non-analytics reports
            if data_points:
                return data_points[0] if len(data_points) == 1 else {'data': data_points}
            return {}
        
        if self.container.has('analytics'):
            analytics = self.container.get('analytics')
            
            return analytics.analyze(
                data=data_points,  # Service uses 'data' param
                metrics=metrics_ext.get('primary', []),
                metrics_config=metrics_ext,
                report_config=config
            )
        else:
            # No analytics service - return raw data
            # Plugins should register an analytics service for analysis
            from ..core import log_warning
            log_warning("No analytics service registered - returning raw data", config)
            return {'data': data_points, 'count': len(data_points)}
    
    def _generate_llm_content(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        system_def: Any,
        config: Any
    ) -> Dict[str, str]:
        """Generate LLM content using LLMService."""
        if config.dry_run:
            return {}
        
        if self.container.has('llm'):
            llm_service = self.container.get('llm')
            
            # system_def.thresholds is already a Dict[str, Any] from the schema
            context = {
                'thresholds': system_def.thresholds if isinstance(system_def.thresholds, dict) else {},
            }
            
            return llm_service.generate_all(
                generators=system_def.llm_generators,
                data=data_points,  # Service uses 'data' param
                stats=stats,
                context=context,
                dry_run=config.dry_run
            )
        else:
            # No LLM service registered
            return {}
    
    def _generate_charts(
        self,
        data_points: List[Dict[str, Any]],
        system_def: Any,
        config: Any
    ) -> Dict[str, str]:
        """Generate charts using ChartService."""
        # ChartService usage is optional - executor handles this for now
        # This is a placeholder for future chart service integration
        return {}
    
    def _render_pages(
        self,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        llm_content: Dict[str, str],
        charts: Dict[str, str],
        system_def: Any,
        input_dir: Path,
        output_path: Path,
        config: Any
    ) -> List[str]:
        """
        Render pages using template engine.
        
        Note: This delegates to the existing executor's generate_pages
        for now. Future versions may use a separate RenderService.
        """
        # For now, we don't implement full rendering here
        # The executor still handles page generation
        return []


def create_default_pipeline() -> ReportPipeline:
    """
    Create a pipeline with default services registered.
    
    Note: This function modifies the global service container by registering
    default services. If you need a fresh container, create a ReportPipeline
    with a custom ServiceContainer instance.
    
    Returns:
        ReportPipeline with DataService and AnalyticsService
    """
    from .data_service import DataService
    from .analytics_service import AnalyticsService
    
    container = get_container()
    
    if not container.has('data'):
        container.register('data', DataService())
    
    if not container.has('analytics'):
        container.register('analytics', AnalyticsService())
    
    return ReportPipeline(container)

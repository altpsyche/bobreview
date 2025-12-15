"""
Core API: Interfaces for plugin components.

This module defines the primary API that plugins implement. All interfaces
should be here, providing a clear contract between core and plugins.

Data Flow:
    Parser → List[Dict] → DataService → DataFrame → Components

Dependency Direction:
- Core defines the contract (this module)
- Plugins implement the contract
- Framework orchestrates using the contract
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..engine.schema import DataSourceConfig
    from .config import Config
    from .dataframe import DataFrame


class DataParserInterface(ABC):
    """
    Core API: Interface for data parsers.
    
    Plugins implement this interface to provide custom data parsing.
    The parser takes a configuration object and parses files into structured data.
    
    Example:
        class MyParser(DataParserInterface):
            def __init__(self, config: DataSourceConfig):
                self.config = config
            
            def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
                # Parse single file
                return {'field1': value1, 'field2': value2}
            
            def discover_files(self, directory: Path) -> List[Path]:
                # Find files to parse
                return list(directory.glob('*.myformat'))
    """
    
    def __init__(self, config: 'DataSourceConfig'):
        """
        Initialize parser with configuration.
        
        Parameters:
            config: DataSourceConfig from report system JSON definition
                   Contains: type, input_format, pattern, fields, validation rules
        """
        self.config = config
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single file and return structured data.
        
        This is the core method that plugins must implement.
        It should extract structured data from a file based on the parser's logic.
        
        Parameters:
            file_path: Path to the file to parse
        
        Returns:
            Dictionary with parsed data fields, or None if parsing fails.
            The dictionary keys should match the field names defined in config.fields.
            Common fields: 'img' (filename), timestamp fields, metric fields
        
        Example:
            # For filename pattern parser
            return {
                'id': 'Item1',
                'metric_a': 85000,
                'metric_b': 520,
                'timestamp': 1234567890,
                'img': 'Item1_85000_520_1234567890.png'
            }
        """
        pass
    
    @abstractmethod
    def discover_files(self, directory: Path) -> List[Path]:
        """
        Discover files in a directory that can be parsed.
        
        This method should return all files that match the parser's criteria.
        Used for batch parsing and file discovery without parsing.
        
        Parameters:
            directory: Directory to scan
        
        Returns:
            List of file paths that match the parser's criteria.
            Should be sorted for consistent ordering.
        
        Example:
            # For PNG files
            return sorted(directory.glob('*.png'))
        """
        pass
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Parse all matching files in a directory.
        
        Default implementation provided by core. Uses discover_files() and parse_file().
        Plugins can override for more efficient batch parsing if needed.
        
        Parameters:
            directory: Directory to scan and parse
        
        Returns:
            List of parsed data dictionaries
        
        Implementation:
            1. Call discover_files() to get list of files
            2. For each file, call parse_file()
            3. Validate data if config.validation.skip_invalid is False
            4. Return list of valid parsed data points
        """
        data_points = []
        files = self.discover_files(directory)
        
        for file_path in files:
            try:
                data = self.parse_file(file_path)
                if data is not None:
                    # Optional validation
                    if not self.config.validation.skip_invalid:
                        if not self._validate_data(data):
                            if self.config.validation.strict_mode:
                                raise ValueError(f"Invalid data in file: {file_path}")
                            continue
                    data_points.append(data)
            except Exception as e:
                if self.config.validation.strict_mode:
                    raise
                continue
        
        return data_points
    
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate parsed data against field configuration.
        
        Core provides validation logic. Plugins can override for custom validation.
        
        Parameters:
            data: Parsed data dictionary
        
        Returns:
            True if data is valid, False otherwise
        
        Validation checks:
            - Required fields are present
            - Field types match (integer, float, string, boolean)
            - Numeric ranges (min/max)
            - String patterns (regex)
        """
        for field_name, field_config in self.config.fields.items():
            if field_config.required and field_name not in data:
                if not self.config.validation.allow_missing_fields:
                    return False
            
            if field_name not in data:
                continue
            
            value = data[field_name]
            
            # Type validation
            if field_config.type == 'integer' and not isinstance(value, int):
                return False
            elif field_config.type == 'float' and not isinstance(value, (int, float)):
                return False
            elif field_config.type == 'string' and not isinstance(value, str):
                return False
            elif field_config.type == 'boolean' and not isinstance(value, bool):
                return False
            
            # Range validation
            if field_config.type in ('integer', 'float'):
                if field_config.min is not None and value < field_config.min:
                    return False
                if field_config.max is not None and value > field_config.max:
                    return False
            
            # Pattern validation
            if field_config.type == 'string' and field_config.pattern:
                import re
                if not re.match(field_config.pattern, value):
                    return False
        
        return True


class LLMGeneratorInterface(ABC):
    """
    Core API: Interface for LLM content generators.
    
    Plugins implement this to provide custom LLM-powered content generation.
    The generator takes data, statistics, and configuration to produce
    AI-generated content (text, structured data, etc.).
    
    Example:
        class MyGenerator(LLMGeneratorInterface):
            def generate(self, data, stats, config, context):
                # Convert to list for internal use
                data_points = list(data)
                # Build prompt from data
                prompt = self._build_prompt(data_points, stats)
                # Call LLM and process response
                return call_llm(prompt, config.llm)
    """
    
    @abstractmethod
    def generate(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        stats: Dict[str, Any],
        config: 'Config',
        context: Dict[str, Any]
    ) -> Any:
        """
        Generate LLM content from data and statistics.
        
        Parameters:
            data: DataFrame or List[Dict] with parsed data points
            stats: Statistical analysis results
            config: Config with LLM settings
            context: Additional context
        
        Returns:
            Generated content. Can be:
            - str: Plain text content
            - dict: Structured content (e.g., {'summary': '...', 'recommendations': [...]})
            - Any: Plugin-specific format
        
        Example:
            # Text generator
            return "Based on the analysis, performance is optimal..."
            
            # Structured generator
            return {
                'summary': 'Performance analysis summary',
                'recommendations': ['Optimize X', 'Reduce Y'],
                'score': 8.5
            }
        """
        pass


class ChartGeneratorInterface(ABC):
    """
    Core API: Interface for chart generators.
    
    Plugins implement this to provide custom chart generation.
    Charts can be HTML, JSON (for Chart.js), SVG, or other formats.
    
    Example:
        class MyChartGenerator(ChartGeneratorInterface):
            def generate_chart(self, data, stats, config, chart_config):
                # Convert to list for internal use
                data_points = list(data)
                # Generate Chart.js JSON
                return json.dumps({
                    'type': 'line',
                    'data': {...},
                    'options': {...}
                })
    """
    
    @abstractmethod
    def generate_chart(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        stats: Dict[str, Any],
        config: 'Config',
        chart_config: Dict[str, Any]
    ) -> str:
        """
        Generate chart from data and statistics.
        
        Parameters:
            data: DataFrame or List[Dict] with parsed data
            stats: Statistical analysis results
            config: Config with settings
            chart_config: Chart configuration
        
        Returns:
            Chart representation as string. Format depends on chart type:
            - JSON string (for Chart.js)
            - HTML string (for embedded charts)
            - SVG string (for vector charts)
            - Base64 encoded image (for static charts)
        
        Example:
            # Chart.js JSON
            return json.dumps({
                'type': 'line',
                'data': {
                    'labels': [p['timestamp'] for p in data_points],
                    'datasets': [{
                        'label': 'Metric B',
                        'data': [p['metric_b'] for p in data_points]
                    }]
                }
            })
        """
        pass

class ContextBuilderInterface(ABC):
    """
    Core API: Interface for context builders.
    
    Plugins implement this to add custom data to template context.
    Context builders enrich the template rendering context with plugin-specific data.
    
    Example:
        class MyContextBuilder(ContextBuilderInterface):
            def build_context(self, data, stats, config, base_context):
                # Convert to list for internal use
                data_points = list(data)
                # Add custom data
                base_context['custom_metric'] = self._calculate_custom(data_points)
                base_context['custom_charts'] = self._generate_charts(stats)
                return base_context
    """
    
    @abstractmethod
    def build_context(
        self,
        data: Union[List[Dict[str, Any]], 'DataFrame'],
        stats: Dict[str, Any],
        config: 'Config',
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build template context from data and statistics.
        
        Parameters:
            data: DataFrame or List[Dict] with parsed data
            stats: Statistical analysis results
            config: Config with settings
            base_context: Base context from framework
        
        Returns:
            Enriched context dictionary. Should merge with base_context.
        
        Example:
            return {
                **base_context,
                'custom_images': self._get_custom_images(data_points),
                'custom_metrics': self._calculate_metrics(stats),
                'plugin_data': self._prepare_plugin_data(config)
            }
        """
        pass


class ComponentInterface(ABC):
    """
    Core API: Interface for reusable UI components.
    
    Plugins implement this to define custom UI components (stat cards, gauges,
    data tables, etc.) that templates can render dynamically.
    
    Components are rendered via the `render_component` template function:
        {{ render_component('stat_card', {'title': 'Total', 'value': 42}) }}
    
    Example:
        class StatCardComponent(ComponentInterface):
            @property
            def component_type(self) -> str:
                return 'stat_card'
            
            def render(self, props: Dict[str, Any], context: Dict[str, Any]) -> str:
                title = props.get('title', '')
                value = props.get('value', 0)
                return f'''
                    <div class="stat-card">
                        <h3>{title}</h3>
                        <span class="value">{value}</span>
                    </div>
                '''
    """
    
    @property
    @abstractmethod
    def component_type(self) -> str:
        """
        Return the component type identifier.
        
        This ID is used to lookup the component in templates:
            {{ render_component('stat_card', props) }}
        
        Returns:
            Unique component type string (e.g., 'stat_card', 'gauge', 'data_table')
        """
        pass
    
    @abstractmethod
    def render(
        self,
        props: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Render the component to an HTML string.
        
        Parameters:
            props: Component properties passed from template
                   (e.g., {'title': 'Score', 'value': 95, 'color': 'green'})
            context: Template context (stats, config, data, etc.)
        
        Returns:
            HTML string for the rendered component
        
        Example:
            def render(self, props, context):
                value = props.get('value', 0)
                threshold = context.get('stats', {}).get('mean', 50)
                color = 'green' if value > threshold else 'red'
                return f'<span style="color: {color}">{value}</span>'
        """
        pass
    
    async def render_async(
        self,
        props: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Async render for components that need to fetch data.
        
        Override this method for components that perform async operations
        (API calls, database queries, etc.). The default implementation
        falls back to the sync render() method.
        
        Parameters:
            props: Component properties passed from template
            context: Template context (stats, config, data, etc.)
        
        Returns:
            HTML string for the rendered component
        
        Example:
            async def render_async(self, props, context):
                data = await fetch_external_data(props.get('source'))
                return self._format_table(data)
        """
        # Default: fall back to sync render
        return self.render(props, context)
    
    @property
    def is_async(self) -> bool:
        """
        Return True if this component requires async rendering.
        
        Override to return True if render_async does actual async work.
        This helps the renderer decide which method to call.
        """
        return False

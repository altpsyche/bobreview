"""
Data service for parsing and validating input data.

This service handles all data ingestion tasks:
- File discovery
- Parsing using configured parsers
- Validation against schema
- Sampling and sorting
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Type
import random
import logging

from .base import BaseService, DataServiceError

logger = logging.getLogger(__name__)


class DataService(BaseService):
    """
    Service for parsing input data files.
    
    Extracted from ReportSystemExecutor.parse_data() to enable:
    - Independent testing
    - Plugin replacement
    - Reuse across different report types
    
    Example:
        service = DataService()
        data_points = service.parse(
            input_dir=Path('./screenshots'),
            data_source_config=system_def.data_source,
            sample_size=100
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize data service."""
        super().__init__(config)
        self._parsers: Dict[str, Type] = {}
        self._register_builtin_parsers()
    
    def _register_builtin_parsers(self) -> None:
        """Register built-in parser types."""
        from ..report_systems.data_parser_base import FilenamePatternParser
        self._parsers['filename_pattern'] = FilenamePatternParser
    
    def register_parser(self, parser_type: str, parser_cls: Type) -> None:
        """
        Register a custom parser type.
        
        Parameters:
            parser_type: Parser type identifier (for data_source.type)
            parser_cls: Parser class that extends DataParser
        """
        self._parsers[parser_type] = parser_cls
        logger.debug(f"Registered parser: {parser_type}")
    
    def get_parser(self, parser_type: str) -> Optional[Type]:
        """Get a parser class by type."""
        return self._parsers.get(parser_type)
    
    def parse(
        self,
        input_dir: Path,
        data_source_config: Any,
        sample_size: Optional[int] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse data from input directory.
        
        Parameters:
            input_dir: Directory containing input files
            data_source_config: DataSourceConfig from report system
            sample_size: Optional limit on number of data points
            sort_by: Optional field to sort by
            
        Returns:
            List of parsed data points
            
        Raises:
            DataServiceError: If parsing fails
        """
        # Get parser class
        parser_type = data_source_config.type
        parser_cls = self._parsers.get(parser_type)
        
        if not parser_cls:
            raise DataServiceError(
                f"Unsupported data source type: {parser_type}. "
                f"Available types: {list(self._parsers.keys())}"
            )
        
        try:
            # Create parser instance
            parser = parser_cls(data_source_config)
            
            # Parse directory
            data_points = parser.parse_directory(input_dir)
            
            if not data_points:
                logger.warning(f"No data points found in {input_dir}")
                return []
            
            logger.info(f"Parsed {len(data_points)} data points from {input_dir}")
            
            # Apply sampling if requested
            if sample_size and sample_size < len(data_points):
                data_points = random.sample(data_points, sample_size)
                logger.debug(f"Sampled down to {sample_size} points")
            
            # Sort if requested
            if sort_by and data_points and sort_by in data_points[0]:
                data_points.sort(key=lambda x: x.get(sort_by, 0))
                logger.debug(f"Sorted by {sort_by}")
            
            return data_points
            
        except Exception as e:
            raise DataServiceError(f"Failed to parse data: {e}") from e
    
    def validate(
        self,
        data_points: List[Dict[str, Any]],
        required_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Validate data points against required fields.
        
        Parameters:
            data_points: Data points to validate
            required_fields: List of required field names
            
        Returns:
            Validation result with 'valid', 'errors', 'warnings'
        """
        if not data_points:
            return {
                'valid': False,
                'errors': ['No data points to validate'],
                'warnings': []
            }
        
        errors = []
        warnings = []
        
        # Check first data point for required fields
        first_point = data_points[0]
        available_fields = set(first_point.keys())
        missing_fields = [f for f in required_fields if f not in available_fields]
        
        if missing_fields:
            errors.append(
                f"Missing required fields: {', '.join(missing_fields)}. "
                f"Available: {', '.join(sorted(available_fields))}"
            )
        
        # Check for empty values in required fields
        empty_counts = {f: 0 for f in required_fields if f in available_fields}
        for point in data_points:
            for field in empty_counts:
                if point.get(field) is None:
                    empty_counts[field] += 1
        
        for field, count in empty_counts.items():
            if count > 0:
                pct = (count / len(data_points)) * 100
                if pct > 50:
                    errors.append(f"Field '{field}' is empty in {pct:.1f}% of data points")
                elif pct > 10:
                    warnings.append(f"Field '{field}' is empty in {pct:.1f}% of data points")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def discover_files(
        self,
        directory: Path,
        data_source_config: Any
    ) -> List[Path]:
        """
        Discover files that can be parsed without actually parsing them.
        
        Parameters:
            directory: Directory to scan
            data_source_config: DataSourceConfig for parser selection
            
        Returns:
            List of file paths that match the parser criteria
        """
        parser_type = data_source_config.type
        parser_cls = self._parsers.get(parser_type)
        
        if not parser_cls:
            return []
        
        parser = parser_cls(data_source_config)
        return parser.discover_files(directory)

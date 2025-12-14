"""
Data service for parsing and validating input data.

This service handles all data ingestion tasks:
- File discovery
- Parsing using configured parsers (via ParserFactory)
- Validation against schema
- Sampling and sorting

Data flows through DataFrame for universal format compatibility.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import random
import logging

from .base import BaseService, DataServiceError
from ..core.dataframe import DataFrame

logger = logging.getLogger(__name__)


class DataService(BaseService):
    """
    Service for parsing input data files.
    
    Uses ParserFactory to create parsers from the plugin registry.
    This ensures all registered parsers (built-in and plugin) are available.
    
    Example:
        service = DataService()
        data_points = service.parse(
            input_dir=Path('./screenshots'),
            data_source_config=system_def.data_source,
            sample_size=100
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data service.
        
        Parameters:
            config: Optional service configuration
        """
        super().__init__(config)
        from ..engine.parser_factory import ParserFactory
        self.factory = ParserFactory()  # Uses global extension point
    
    def parse_dataframe(
        self,
        input_dir: Path,
        data_source_config: Any,
        sample_size: Optional[int] = None,
        sort_by: Optional[str] = None
    ) -> DataFrame:
        """
        Parse data and return as DataFrame (preferred method).
        
        Parameters:
            input_dir: Directory containing input files
            data_source_config: DataSourceConfig from report system
            sample_size: Optional limit on number of data points
            sort_by: Optional field to sort by
            
        Returns:
            DataFrame with parsed data
        """
        try:
            parser = self.factory.create(data_source_config)
            data_points = parser.parse_directory(input_dir)
            
            if not data_points:
                logger.warning(f"No data points found in {input_dir}")
                return DataFrame(source=str(input_dir))
            
            logger.info(f"Parsed {len(data_points)} data points from {input_dir}")
            
            df = DataFrame.from_dicts(
                data_points,
                source=str(input_dir),
                plugin=getattr(data_source_config, 'type', None)
            )
            
            if sample_size and sample_size < len(df):
                df.rows = df.rows[:sample_size]
                logger.debug(f"Sampled down to {sample_size} points")
            
            if sort_by and len(df) > 0 and sort_by in df.column_names:
                df = df.sort_by(sort_by)
                logger.debug(f"Sorted by {sort_by}")
            
            return df
            
        except ValueError as e:
            raise DataServiceError(str(e)) from e
        except Exception as e:
            raise DataServiceError(f"Failed to parse data: {e}") from e
    
    def parse(
        self,
        input_dir: Path,
        data_source_config: Any,
        sample_size: Optional[int] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse data and return as list of dicts.
        
        Returns:
            List of parsed data points
        """
        df = self.parse_dataframe(input_dir, data_source_config, sample_size, sort_by)
        return df.to_dicts()
    
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
        try:
            parser = self.factory.create(data_source_config)
            return parser.discover_files(directory)
        except Exception as e:
            logger.warning(f"Failed to discover files in {directory}: {e}")
            return []

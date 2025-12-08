"""
Abstract base class for data parsers.

Data parsers are responsible for reading input files and converting them
into structured data points that can be analyzed.

Streamlined design:
- Simple interface: parse_file() and discover_files()
- parse_directory() is provided as default implementation
- Validation is optional and can be overridden
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional
from .schema import DataSourceConfig, FieldConfig


class DataParser(ABC):
    """
    Abstract base class for data parsers.
    
    Simple, focused interface for parsing data files.
    """
    
    def __init__(self, config: DataSourceConfig):
        """
        Initialize the data parser with configuration.
        
        Parameters:
            config: Data source configuration from JSON
        """
        self.config = config
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single file and return structured data.
        
        Parameters:
            file_path: Path to the file to parse
        
        Returns:
            Dictionary with parsed data fields, or None if parsing fails
        """
        pass
    
    @abstractmethod
    def discover_files(self, directory: Path) -> List[Path]:
        """
        Discover files in a directory that can be parsed.
        
        Parameters:
            directory: Directory to scan
        
        Returns:
            List of file paths that match the parser's criteria
        """
        pass
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Parse all matching files in a directory.
        
        Default implementation that uses discover_files() and parse_file().
        Can be overridden for more efficient batch parsing.
        
        Parameters:
            directory: Directory to scan and parse
        
        Returns:
            List of parsed data dictionaries
        """
        data_points = []
        files = self.discover_files(directory)
        
        for file_path in files:
            try:
                data = self.parse_file(file_path)
                if data is not None:
                    # Validate data if not skipping invalid
                    if not self.config.validation.skip_invalid:
                        if not self._validate_data(data):
                            if self.config.validation.strict_mode:
                                raise ValueError(f"Invalid data in file: {file_path}")
                            continue
                    
                    data_points.append(data)
            except Exception as e:
                if self.config.validation.strict_mode:
                    raise
                # Skip files that fail to parse
                continue
        
        return data_points
    
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate parsed data against field configuration.
        
        Parameters:
            data: Parsed data dictionary
        
        Returns:
            True if data is valid, False otherwise
        """
        for field_name, field_config in self.config.fields.items():
            # Check required fields
            if field_config.required and field_name not in data:
                if not self.config.validation.allow_missing_fields:
                    return False
            
            # Skip validation if field is missing and allowed
            if field_name not in data:
                continue
            
            value = data[field_name]
            
            # Type validation
            if field_config.type == 'integer':
                if not isinstance(value, int):
                    return False
            elif field_config.type == 'float':
                if not isinstance(value, (int, float)):
                    return False
            elif field_config.type == 'string':
                if not isinstance(value, str):
                    return False
            elif field_config.type == 'boolean':
                if not isinstance(value, bool):
                    return False
            
            # Range validation for numeric types
            if field_config.type in ('integer', 'float'):
                if field_config.min is not None and value < field_config.min:
                    return False
                if field_config.max is not None and value > field_config.max:
                    return False
            
            # Pattern validation for strings
            if field_config.type == 'string' and field_config.pattern:
                import re
                if not re.match(field_config.pattern, value):
                    return False
        
        return True


class FilenamePatternParser(DataParser):
    """
    Parser for extracting data from filename patterns.
    
    Extracts structured data from filenames using a pattern
    like: {testcase}_{tris}_{draws}_{timestamp}.png
    """
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Discover files matching the input format."""
        input_format = self.config.input_format
        pattern = f"*.{input_format}"
        return sorted(directory.glob(pattern))
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a filename using the configured pattern.
        
        Pattern format: {field1}_{field2}_{field3}.ext
        Example: {testcase}_{tris}_{draws}_{timestamp}.png
        """
        if not self.config.pattern:
            return None
        
        # Extract the pattern and remove extension
        pattern = self.config.pattern
        
        # Remove extension from pattern if present
        if '.' in pattern:
            pattern_base = pattern.rsplit('.', 1)[0]
        else:
            pattern_base = pattern
        
        # Remove extension from filename
        filename = file_path.stem
        
        # Extract field names from pattern
        import re
        field_names = re.findall(r'\{(\w+)\}', pattern_base)
        
        # For simple underscore-separated patterns
        if '_' in pattern_base:
            # Split filename by underscores
            filename_parts = filename.split('_')
            
            num_fields = len(field_names)
            
            if len(filename_parts) < num_fields:
                return None
            
            data = {}
            
            # First field gets all parts except the last (num_fields - 1)
            if num_fields > 1:
                data[field_names[0]] = '_'.join(filename_parts[:-(num_fields - 1)])
                # Remaining fields get one part each
                for i in range(1, num_fields):
                    field_name = field_names[i]
                    value_str = filename_parts[-(num_fields - i)]
                    data[field_name] = self._convert_value(field_name, value_str)
            else:
                # Only one field
                data[field_names[0]] = filename
            
            # Add the filename itself
            data['img'] = file_path.name
            
            # Map 'timestamp' to 'ts' for compatibility
            if 'timestamp' in data and 'ts' not in data:
                data['ts'] = data['timestamp']
            
            return data
        
        return None
    
    def _convert_value(self, field_name: str, value_str: str) -> Any:
        """Convert a string value to the appropriate type based on field config."""
        if field_name not in self.config.fields:
            return value_str
        
        field_config = self.config.fields[field_name]
        
        try:
            if field_config.type == 'integer':
                return int(value_str)
            elif field_config.type == 'float':
                return float(value_str)
            elif field_config.type == 'boolean':
                return value_str.lower() in ('true', '1', 'yes')
            else:
                return value_str
        except (ValueError, AttributeError):
            return value_str

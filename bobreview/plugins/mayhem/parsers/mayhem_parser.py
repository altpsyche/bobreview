"""
MayhemAutomation Parser.

Parser for MayhemAutomation performance data from PNG filenames.
Extends FilenamePatternParser with MayhemAutomation-specific defaults.

Implements DataParserInterface from core.api (via FilenamePatternParser).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional
import re

from ....report_systems.data_parser_base import FilenamePatternParser
from ....report_systems.schema import DataSourceConfig, FieldConfig

# Note: MayhemParser extends FilenamePatternParser, which extends DataParserInterface
# from core.api. This maintains the core API contract while providing a concrete
# implementation suitable for MayhemAutomation patterns.


@dataclass
class DataPoint:
    """
    Represents a single MayhemAutomation performance data point.
    
    Contains fields specific to MayhemAutomation performance analysis:
    - testcase: Test case or level name
    - tris: Triangle count
    - draws: Draw call count
    - ts: Timestamp
    - img: Image filename
    """
    testcase: str
    tris: int
    draws: int
    ts: int
    img: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert datapoint to dictionary."""
        return {
            'testcase': self.testcase,
            'tris': self.tris,
            'draws': self.draws,
            'ts': self.ts,
            'img': self.img
        }


class MayhemParser(FilenamePatternParser):
    """
    Parser for MayhemAutomation performance data files.
    
    Parses PNG filenames with patterns like:
    - "{testcase}_{tris}_{draws}_{timestamp}.png"
    - "{level}_{triangles}_{drawcalls}_{ts}.png"
    
    Automatically infers field types based on common MayhemAutomation field names.
    """
    
    def __init__(self, config: Optional[DataSourceConfig] = None):
        """
        Initialize MayhemParser.
        
        Parameters:
            config: Optional DataSourceConfig. If None, creates a default config
                    suitable for MayhemAutomation patterns.
        """
        if config is None:
            # Create default config for MayhemAutomation
            config = DataSourceConfig(
                type='filename_pattern',
                input_format='png',
                pattern='{testcase}_{tris}_{draws}_{timestamp}.png',
                fields={
                    'testcase': FieldConfig(type='string', required=True),
                    'tris': FieldConfig(type='integer', required=True, min=0),
                    'draws': FieldConfig(type='integer', required=True, min=0),
                    'timestamp': FieldConfig(type='integer', required=True, min=0),
                }
            )
        super().__init__(config)
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a MayhemAutomation filename.
        
        Overrides parent to add MayhemAutomation-specific field mapping.
        """
        result = super().parse_file(file_path)
        
        if result is None:
            return None
        
        # Map 'timestamp' to 'ts' for compatibility with existing code
        if 'timestamp' in result and 'ts' not in result:
            result['ts'] = result['timestamp']
        
        return result


def parse_filename(filename: str, pattern: str) -> Dict[str, Any]:
    """
    Convenience function to parse a single MayhemAutomation filename.
    
    This is a thin wrapper around MayhemParser for simple use cases.
    For batch parsing, use DataService.parse() instead.
    
    Example patterns:
    - "{testcase}_{tris}_{draws}_{timestamp}.png"
    - "{level}_{triangles}_{drawcalls}_{ts}.png"
    
    Parameters:
        filename (str): The filename to parse.
        pattern (str): Pattern string with field names in curly braces.
    
    Returns:
        dict: A dictionary with parsed field values plus 'img' key with original filename.
              Field 'timestamp' is also mapped to 'ts' for compatibility.
    
    Raises:
        ValueError: If parsing fails or pattern is invalid.
    """
    # Build field configs from pattern
    field_names = re.findall(r'\{(\w+)\}', pattern)
    
    if not field_names:
        raise ValueError(f"Pattern must contain at least one field: {pattern}")
    
    # Infer field types (MayhemAutomation-specific heuristic)
    fields = {}
    for field_name in field_names:
        if field_name in ('tris', 'draws', 'timestamp', 'ts', 'triangles', 'drawcalls'):
            field_type = 'integer'
        else:
            field_type = 'string'
        
        fields[field_name] = FieldConfig(
            type=field_type,
            required=True,
            min=0 if field_type == 'integer' else None
        )
    
    # Determine input format from pattern or filename
    input_format = 'png'  # Default for MayhemAutomation
    if '.' in pattern:
        input_format = pattern.rsplit('.', 1)[-1]
    elif '.' in filename:
        input_format = filename.rsplit('.', 1)[-1]
    
    # Create config
    data_source_config = DataSourceConfig(
        type='filename_pattern',
        input_format=input_format,
        pattern=pattern,
        fields=fields
    )
    
    # Use MayhemParser
    parser = MayhemParser(data_source_config)
    result = parser.parse_file(Path(filename))
    
    if result is None:
        raise ValueError(
            f"Failed to parse filename: {filename}\n"
            f"Pattern: {pattern}\n"
            f"Expected format matching the pattern with fields: {', '.join(field_names)}"
        )
    
    return result


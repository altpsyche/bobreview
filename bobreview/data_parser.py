#!/usr/bin/env python3
"""
Data parsing utilities for BobReview.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DataPoint:
    """Represents a single performance data point."""
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


def parse_filename(filename: str, pattern: str) -> Dict[str, Any]:
    """
    Parse a PNG filename using a configurable pattern.
    
    The filename must match the provided pattern. Field names in curly braces are extracted.
    Example patterns:
    - "{testcase}_{tris}_{draws}_{timestamp}.png"
    - "{level}_{triangles}_{drawcalls}_{ts}.png"
    
    Parameters:
        filename (str): The PNG filename to parse.
        pattern (str): Pattern string with field names in curly braces.
                       Must be provided - no default to avoid plugin-specific assumptions.
    
    Returns:
        dict: A dictionary with parsed field values plus 'img' key with original filename.
              Field 'timestamp' is also mapped to 'ts' for compatibility.
    
    Raises:
        ValueError: If the file is not a PNG, the format doesn't match the pattern,
                    numeric fields cannot be parsed, or validation fails.
    """
    from .report_systems.data_parser_base import FilenamePatternParser
    from .report_systems.schema import DataSourceConfig, FieldConfig
    from pathlib import Path
    import re
    
    # Build field configs from pattern
    field_names = re.findall(r'\{(\w+)\}', pattern)
    
    if not field_names:
        raise ValueError(f"Pattern must contain at least one field: {pattern}")
    
    fields = {}
    for field_name in field_names:
        # Determine type based on field name
        if field_name in ('tris', 'draws', 'timestamp', 'ts', 'triangles', 'drawcalls'):
            field_type = 'integer'
        else:
            field_type = 'string'
        
        fields[field_name] = FieldConfig(
            type=field_type,
            required=True,
            min=0 if field_type == 'integer' else None
        )
    
    # Create config
    data_source_config = DataSourceConfig(
        type='filename_pattern',
        input_format='png',
        pattern=pattern,
        fields=fields
    )
    
    # Use modular parser
    parser = FilenamePatternParser(data_source_config)
    result = parser.parse_file(Path(filename))
    
    if result is None:
        raise ValueError(
            f"Failed to parse filename: {filename}\n"
            f"Pattern: {pattern}\n"
            f"Expected format matching the pattern with fields: {', '.join(field_names)}"
        )
    
    # Map 'timestamp' to 'ts' for compatibility with existing code
    if 'timestamp' in result and 'ts' not in result:
        result['ts'] = result['timestamp']
    
    return result


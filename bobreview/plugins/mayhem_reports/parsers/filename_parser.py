"""
PNG Filename Parser for mayhem-reports Plugin.

Parses performance data from PNG filenames with the pattern:
{testcase}_{tris}_{draws}_{timestamp}.png

Extends FilenamePatternParser from the engine.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from bobreview.engine.data_parser_base import FilenamePatternParser
from bobreview.engine.schema import DataSourceConfig, FieldConfig


@dataclass
class PerformanceDataPoint:
    """
    Represents a single performance data point.
    
    Fields:
    - testcase: Test case or scene name
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


class MayhemReportsParser(FilenamePatternParser):
    """
    Parser for performance data from PNG filenames.
    
    Parses filenames with patterns like:
    - "{testcase}_{tris}_{draws}_{timestamp}.png"
    
    Automatically infers field types based on common performance field names.
    """
    
    # Required for registry
    parser_name = "mayhem_reports_parser"
    
    def __init__(self, config: Optional[DataSourceConfig] = None):
        """
        Initialize MayhemReportsParser.
        
        Parameters:
            config: Optional DataSourceConfig. If None, creates a default config
                    suitable for performance analysis patterns.
        """
        if config is None:
            # Create default config for performance analysis
            config = DataSourceConfig(
                type='mayhem_reports_parser',
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
        Parse a performance PNG filename.
        
        Overrides parent to add field mapping for template compatibility.
        """
        result = super().parse_file(file_path)
        
        if result is None:
            return None
        
        # Map 'timestamp' to 'ts' for compatibility with templates
        if 'timestamp' in result and 'ts' not in result:
            result['ts'] = result['timestamp']
        
        return result

"""
CSV Parser for Hello World Plugin.

Implements DataParserInterface to parse CSV files with:
- name: Entry identifier
- score: Numeric score value
- timestamp: Unix timestamp or ISO date
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

from bobreview.core.api import DataParserInterface


class HelloCsvParser(DataParserInterface):
    """
    Parse CSV files with name, score, and timestamp columns.
    
    This demonstrates how to implement DataParserInterface from the core API.
    
    Expected CSV format:
        name,score,timestamp
        Alice,95,2024-01-15
        Bob,82,2024-01-16
        Charlie,78,2024-01-17
    """
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single CSV file.
        
        For CSV files, we parse the entire file and return records as a list.
        This method is called once per file.
        """
        # For CSV, we read all rows and return them via parse_directory instead
        # This method is used for single-record-per-file formats
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """
        Find all CSV files in the directory.
        """
        return sorted(directory.glob("*.csv"))
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """
        Parse all CSV files and return combined records.
        
        This overrides the default implementation for efficiency with CSV.
        """
        data_points = []
        
        for csv_file in self.discover_files(directory):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        # Parse and validate each row
                        data_point = self._parse_row(row, csv_file.name)
                        if data_point:
                            data_points.append(data_point)
                            
            except (OSError, csv.Error) as e:
                if self.config.validation.strict_mode:
                    raise ValueError(f"Error reading {csv_file}: {e}")
                continue
        
        return data_points
    
    def _parse_row(self, row: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single CSV row into a data point.
        """
        try:
            # Get required fields
            name = row.get('name', '').strip()
            score_str = row.get('score', '').strip()
            timestamp_str = row.get('timestamp', '').strip()
            
            if not name or not score_str:
                return None
            
            # Parse score as float
            try:
                score = float(score_str)
            except ValueError:
                return None
            
            # Parse timestamp (support both Unix and ISO formats)
            timestamp = self._parse_timestamp(timestamp_str)
            
            return {
                'name': name,
                'score': score,
                'timestamp': timestamp,
                'source': source_file,
            }
            
        except Exception:
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """
        Parse timestamp from various formats.
        
        Supports:
        - Unix timestamp (integer)
        - ISO date (YYYY-MM-DD)
        - ISO datetime (YYYY-MM-DDTHH:MM:SS)
        """
        if not timestamp_str:
            from datetime import datetime
            return int(datetime.now().timestamp())
        
        # Try Unix timestamp
        try:
            return int(float(timestamp_str))
        except ValueError:
            pass
        
        # Try ISO date/datetime
        from datetime import datetime
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return int(dt.timestamp())
            except ValueError:
                continue
        
        # Fallback to current time
        return int(datetime.now().timestamp())

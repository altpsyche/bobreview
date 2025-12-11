"""
CSV Parser for mayhem-reports Plugin.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import csv

from bobreview.core.api import DataParserInterface


class MayhemReportsCsvParser(DataParserInterface):
    """
    Parse CSV files with name, score, and timestamp columns.
    
    Expected CSV format:
        name,score,timestamp
        Item1,85,2024-01-15
        Item2,72,2024-01-16
    """
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single CSV file (not used for multi-row CSVs)."""
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Find all CSV files in the directory."""
        return sorted(directory.glob("*.csv"))
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all CSV files and return combined records."""
        data_points = []
        
        for csv_file in self.discover_files(directory):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data_point = self._parse_row(row, csv_file.name)
                        if data_point:
                            data_points.append(data_point)
            except (OSError, csv.Error):
                continue
        
        return data_points
    
    def _parse_row(self, row: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row."""
        try:
            name = row.get('name', '').strip()
            score_str = row.get('score', '').strip()
            
            if not name or not score_str:
                return None
            
            return {
                'name': name,
                'score': float(score_str),
                'timestamp': self._parse_timestamp(row.get('timestamp', '')),
                'source': source_file,
            }
        except (ValueError, TypeError):
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """Parse timestamp from string."""
        from datetime import datetime
        
        if not timestamp_str:
            return int(datetime.now().timestamp())
        
        try:
            return int(float(timestamp_str))
        except ValueError:
            pass
        
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return int(datetime.strptime(timestamp_str.strip(), fmt).timestamp())
            except ValueError:
                continue
        
        return int(datetime.now().timestamp())

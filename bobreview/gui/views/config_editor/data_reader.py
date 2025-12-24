"""
Data Reader - Reads column/field names from data files.

Supports CSV, JSON, and YAML formats.
"""

import csv
import json
import yaml
from pathlib import Path
from typing import List, Optional, Tuple


class DataReader:
    """Reads data fields from various file formats."""
    
    def __init__(self):
        self.columns: List[str] = []
        self.file_type: Optional[str] = None
        self.error: Optional[str] = None
    
    def read_directory(self, data_dir: str) -> bool:
        """
        Read field names from first data file in directory.
        
        Returns True if successful, False otherwise.
        """
        self.columns = []
        self.file_type = None
        self.error = None
        
        try:
            data_path = Path(data_dir)
            
            # Try CSV first
            if self._try_csv(data_path):
                return True
            
            # Try JSON
            if self._try_json(data_path):
                return True
            
            # Try YAML
            if self._try_yaml(data_path):
                return True
            
            self.error = "No data files found (CSV, JSON, YAML)"
            return False
            
        except Exception as ex:
            self.error = f"Error reading data: {ex}"
            return False
    
    def _try_csv(self, data_path: Path) -> bool:
        """Try to read CSV files."""
        csv_files = list(data_path.glob("*.csv"))
        if not csv_files:
            return False
        
        with open(csv_files[0], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.columns = list(reader.fieldnames or [])
        
        self.file_type = "CSV"
        return bool(self.columns)
    
    def _try_json(self, data_path: Path) -> bool:
        """Try to read JSON files."""
        json_files = list(data_path.glob("*.json"))
        if not json_files:
            return False
        
        with open(json_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                self.columns = list(data[0].keys())
            elif isinstance(data, dict):
                self.columns = list(data.keys())
        
        self.file_type = "JSON"
        return bool(self.columns)
    
    def _try_yaml(self, data_path: Path) -> bool:
        """Try to read YAML files."""
        yaml_files = list(data_path.glob("*.yaml")) + list(data_path.glob("*.yml"))
        if not yaml_files:
            return False
        
        with open(yaml_files[0], 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if isinstance(data, list) and data:
                self.columns = list(data[0].keys())
            elif isinstance(data, dict):
                self.columns = list(data.keys())
        
        self.file_type = "YAML"
        return bool(self.columns)
    
    def get_status_message(self) -> Tuple[str, str]:
        """
        Get status message and color for UI.
        
        Returns (message, color) tuple.
        """
        if self.error:
            return self.error, "red"
        
        if self.columns:
            preview = ', '.join(self.columns[:5])
            if len(self.columns) > 5:
                preview += f", +{len(self.columns) - 5} more"
            return f"✓ {self.file_type}: {len(self.columns)} fields ({preview})", "green"
        
        return "No data loaded", "orange"

"""
Generators for data parsing files.

Creates:
- csv_parser.py (schema-driven CSV parser)
- context_builder.py (template context builder)
"""


def generate_csv_parser(name: str, class_name: str) -> str:
    """Generate CSV parser file that reads from data_schema.yaml."""
    return f'''"""
CSV Parser for {name} Plugin.

Schema-Driven Parsing:
- Reads field definitions from data_schema.yaml
- Supports string, number, date, category types
- No code changes needed to parse different CSV formats

Data Flow:
    data_schema.yaml → Parser → CSV files → List[Dict]
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import csv
import yaml


def load_schema(plugin_dir: Path) -> Dict[str, Any]:
    """Load data schema from YAML file."""
    schema_path = plugin_dir / 'data_schema.yaml'
    if not schema_path.exists():
        # Fallback to default schema
        return {{
            'fields': [
                {{'name': 'name', 'type': 'string', 'required': True}},
                {{'name': 'score', 'type': 'number', 'required': True}},
                {{'name': 'category', 'type': 'category', 'required': False, 'default': 'General'}},
            ]
        }}
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {{'fields': []}}


def convert_value(value: str, field_def: Dict[str, Any]) -> Any:
    """Convert string value to appropriate type based on schema."""
    if not value or not value.strip():
        return field_def.get('default')
    
    value = value.strip()
    field_type = field_def.get('type', 'string')
    
    try:
        if field_type == 'number':
            # Try int first, then float
            if '.' in value:
                return float(value)
            return int(value)
        
        elif field_type == 'date':
            fmt = field_def.get('format', '%Y-%m-%d')
            return datetime.strptime(value, fmt).isoformat()
        
        elif field_type in ('string', 'category'):
            return value
        
        else:
            return value
            
    except (ValueError, TypeError):
        return field_def.get('default')


class {class_name}CsvParser:
    """
    Schema-driven CSV parser.
    
    Reads field definitions from data_schema.yaml and parses any CSV format.
    Edit data_schema.yaml to change what columns are parsed - no code changes needed.
    """
    
    def __init__(self):
        self._schema = None
        self._plugin_dir = Path(__file__).parent.parent
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Lazy-load schema."""
        if self._schema is None:
            self._schema = load_schema(self._plugin_dir)
        return self._schema
    
    @property
    def fields(self) -> List[Dict[str, Any]]:
        """Get field definitions."""
        return self.schema.get('fields', [])
    
    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single CSV file (not used for multi-row CSVs)."""
        return None
    
    def discover_files(self, directory: Path) -> List[Path]:
        """Find all CSV files in the directory."""
        return sorted(directory.glob("*.csv"))
    
    def parse_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Parse all CSV files and return combined records."""
        data_points = []
        errors = []
        
        for csv_file in self.discover_files(directory):
            try:
                with open(csv_file, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                        data_point = self._parse_row(row, csv_file.name, row_num)
                        if data_point:
                            data_points.append(data_point)
            except (OSError, csv.Error) as e:
                errors.append(f"{{csv_file.name}}: {{e}}")
                continue
        
        if errors:
            print(f"Warning: {{len(errors)}} file(s) had errors")
        
        return data_points
    
    def _parse_row(self, row: Dict[str, str], source_file: str, row_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row based on schema."""
        result = {{'_source': source_file, '_row': row_num}}
        
        for field_def in self.fields:
            field_name = field_def.get('name')
            if not field_name:
                continue
            
            raw_value = row.get(field_name, '')
            converted = convert_value(raw_value, field_def)
            
            # Check required fields
            if field_def.get('required') and converted is None:
                return None  # Skip row if required field is missing
            
            result[field_name] = converted
        
        return result
'''


def generate_context_builder(name: str, class_name: str) -> str:
    """Generate context builder file."""
    return f'''"""
Context Builder for {name} Plugin.
"""

from typing import Dict, List, Any, Union


def _normalize_data_to_list(data: Union[List[Dict[str, Any]], Any]) -> List[Dict[str, Any]]:
    """
    Convert DataFrame or other iterable to List[Dict].
    
    Uses duck-typing to detect DataFrame-like objects by checking for:
    - __iter__: Iterable interface
    - column_names: Column metadata (Polars, Pandas-like)
    - rows: Row accessor (Polars, custom DataFrame implementations)
    
    Supported DataFrame libraries:
    - Polars: Has column_names and rows attributes
    - Pandas-like: Typically has column_names or columns attribute
    - Custom DataFrame implementations matching this interface
    
    Note: This pragmatic approach may match unintended objects. For stricter
    type checking, consider using isinstance() checks for known DataFrame types.
    """
    # Check if it's a DataFrame (duck-typing with multiple attributes)
    if hasattr(data, '__iter__') and hasattr(data, 'column_names') and hasattr(data, 'rows'):
        return list(data)
    elif isinstance(data, list):
        return data
    else:
        return list(data) if hasattr(data, '__iter__') and not isinstance(data, str) else []


class {class_name}ContextBuilder:
    """Build template context for {name} reports."""
    
    def build_context(
        self,
        data: Union[List[Dict[str, Any]], Any],
        stats: Dict[str, Any],
        config: Any,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enriched context for template rendering."""
        context = dict(base_context)
        
        # Convert DataFrame to list if needed
        data_points = _normalize_data_to_list(data)
        
        # Sort by score (descending)
        ranked = sorted(data_points, key=lambda x: x.get('score', 0), reverse=True)
        context['ranked_data'] = ranked
        
        # Add rankings
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        
        # Categorize by score
        scores = [d.get('score', 0) for d in data_points]
        if scores:
            context['score_range'] = {{
                'min': min(scores),
                'max': max(scores),
                'spread': max(scores) - min(scores),
            }}
        
        return context
'''

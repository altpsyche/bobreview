"""
DataFrame - Universal Data Format for BobReview.

Inspired by Grafana's DataFrame concept, this provides a consistent
data format that all components (widgets, charts, tables) can consume,
regardless of the original data source format (CSV, JSON, FBX, etc.).

This decouples data parsing from visualization - any parser can produce
a DataFrame, and any component can consume it.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator, Union
from enum import Enum


class ColumnType(Enum):
    """Data types for DataFrame columns."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    UNKNOWN = "unknown"


@dataclass
class Column:
    """Metadata for a DataFrame column."""
    name: str
    type: ColumnType = ColumnType.UNKNOWN
    display_name: Optional[str] = None
    unit: Optional[str] = None  # e.g., "ms", "MB", "triangles"
    
    @property
    def label(self) -> str:
        """Human-readable label for the column."""
        return self.display_name or self.name.replace("_", " ").title()


@dataclass
class DataFrame:
    """
    Universal data format for BobReview.
    
    A DataFrame is a table-like structure with typed columns and rows.
    All data flows through this format between layers:
    
        Parser → DataFrame → Analyzer → DataFrame → Components
    
    Example:
        df = DataFrame(
            columns=[
                Column("name", ColumnType.STRING),
                Column("score", ColumnType.NUMBER, unit="points"),
            ],
            rows=[
                ["Alpha", 95],
                ["Beta", 82],
            ]
        )
        
        # Access data
        for row in df:
            print(row["name"], row["score"])
    """
    
    columns: List[Column] = field(default_factory=list)
    rows: List[List[Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Source information
    source: Optional[str] = None  # e.g., "my_data.csv", "game_assets/"
    plugin: Optional[str] = None  # Plugin that created this DataFrame
    
    def __len__(self) -> int:
        """Number of rows in the DataFrame."""
        return len(self.rows)
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over rows as dictionaries."""
        col_names = [c.name for c in self.columns]
        for row in self.rows:
            yield dict(zip(col_names, row))
    
    def __getitem__(self, key: Union[int, str]) -> Any:
        """Access row by index or column by name."""
        if isinstance(key, int):
            # Return row as dict
            col_names = [c.name for c in self.columns]
            return dict(zip(col_names, self.rows[key]))
        elif isinstance(key, str):
            # Return column values
            col_idx = self._column_index(key)
            return [row[col_idx] for row in self.rows]
        raise TypeError(f"Key must be int or str, got {type(key)}")
    
    def _column_index(self, name: str) -> int:
        """Get column index by name."""
        for i, col in enumerate(self.columns):
            if col.name == name:
                return i
        raise KeyError(f"Column not found: {name}")
    
    @property
    def column_names(self) -> List[str]:
        """List of column names."""
        return [c.name for c in self.columns]
    
    def get_column(self, name: str) -> Optional[Column]:
        """Get column metadata by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None
    
    def to_dicts(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries (old format)."""
        return list(self)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize DataFrame to dictionary."""
        return {
            "columns": [
                {
                    "name": c.name,
                    "type": c.type.value,
                    "display_name": c.display_name,
                    "unit": c.unit,
                }
                for c in self.columns
            ],
            "rows": self.rows,
            "metadata": self.metadata,
            "source": self.source,
            "plugin": self.plugin,
        }
    
    @classmethod
    def from_dicts(
        cls,
        data: List[Dict[str, Any]],
        source: Optional[str] = None,
        plugin: Optional[str] = None
    ) -> "DataFrame":
        """
        Create DataFrame from list of dictionaries.
        
        This is the bridge from old format (List[Dict]) to new.
        """
        if not data:
            return cls(source=source, plugin=plugin)
        
        # Infer columns from first row
        first = data[0]
        columns = []
        for key, value in first.items():
            col_type = cls._infer_type(value)
            columns.append(Column(name=key, type=col_type))
        
        # Extract rows
        col_names = [c.name for c in columns]
        rows = [[row.get(name) for name in col_names] for row in data]
        
        return cls(
            columns=columns,
            rows=rows,
            source=source,
            plugin=plugin
        )
    
    @staticmethod
    def _infer_type(value: Any) -> ColumnType:
        """Infer column type from value."""
        if isinstance(value, bool):
            return ColumnType.BOOLEAN
        if isinstance(value, (int, float)):
            return ColumnType.NUMBER
        if isinstance(value, str):
            return ColumnType.STRING
        return ColumnType.UNKNOWN
    
    def filter(self, predicate) -> "DataFrame":
        """Filter rows by predicate function."""
        col_names = [c.name for c in self.columns]
        filtered_rows = [
            row for row in self.rows
            if predicate(dict(zip(col_names, row)))
        ]
        return DataFrame(
            columns=self.columns.copy(),
            rows=filtered_rows,
            metadata=self.metadata.copy(),
            source=self.source,
            plugin=self.plugin
        )
    
    def select(self, *column_names: str) -> "DataFrame":
        """Select specific columns."""
        indices = [self._column_index(name) for name in column_names]
        new_columns = [self.columns[i] for i in indices]
        new_rows = [[row[i] for i in indices] for row in self.rows]
        return DataFrame(
            columns=new_columns,
            rows=new_rows,
            metadata=self.metadata.copy(),
            source=self.source,
            plugin=self.plugin
        )
    
    def sort_by(self, column: str, descending: bool = False) -> "DataFrame":
        """Sort rows by column."""
        idx = self._column_index(column)
        sorted_rows = sorted(
            self.rows,
            key=lambda r: r[idx] if r[idx] is not None else "",
            reverse=descending
        )
        return DataFrame(
            columns=self.columns.copy(),
            rows=sorted_rows,
            metadata=self.metadata.copy(),
            source=self.source,
            plugin=self.plugin
        )

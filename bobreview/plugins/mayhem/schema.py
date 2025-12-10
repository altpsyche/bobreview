"""
MayhemAutomation-specific schema extensions.

These classes were moved from engine/schema.py to keep the core engine
lean and domain-agnostic. Plugins define their own schema extensions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class DerivedMetricConfig:
    """Configuration for a derived metric calculation."""
    id: str
    description: str
    calculation: str  # Expression or function name
    dependencies: List[str] = field(default_factory=list)


@dataclass
class StatisticsConfig:
    """Configuration for statistical calculations.
    
    Defines which statistics to calculate for performance metrics.
    """
    basic: List[str] = field(default_factory=lambda: ['min', 'max', 'mean', 'median', 'stdev'])
    advanced: List[str] = field(default_factory=lambda: ['p90', 'p95', 'p99', 'variance', 'cv'])
    analysis: List[str] = field(default_factory=lambda: ['confidence_interval', 'trend', 'outliers'])


@dataclass
class MetricConfig:
    """Configuration for performance metrics and analysis.
    
    This is MayhemAutomation-specific - defines how to analyze game
    performance data with draw calls, triangles, etc.
    
    Attributes:
        primary: List of primary metric field names to analyze (e.g., ['draws', 'tris'])
        metric_labels: Display names for metrics (e.g., {'draws': 'Draw Calls'})
        threshold_mapping: Maps metric names to threshold config keys
        timestamp_field: Field name for timestamps (default 'ts')
        identifier_field: Field name for item identifier/name (default 'testcase')
        derived: List of derived metric configurations
        statistics: Statistics configuration
    """
    primary: List[str]
    metric_labels: Dict[str, str] = field(default_factory=dict)
    threshold_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)
    timestamp_field: str = 'ts'
    identifier_field: str = 'testcase'
    derived: List[DerivedMetricConfig] = field(default_factory=list)
    statistics: StatisticsConfig = field(default_factory=StatisticsConfig)


def parse_derived_metric_config(data: Dict[str, Any]) -> DerivedMetricConfig:
    """Parse derived metric configuration from JSON."""
    return DerivedMetricConfig(
        id=data['id'],
        description=data['description'],
        calculation=data['calculation'],
        dependencies=data.get('dependencies', [])
    )


def parse_statistics_config(data: Dict[str, Any]) -> StatisticsConfig:
    """Parse statistics configuration from JSON."""
    return StatisticsConfig(
        basic=data.get('basic', ['min', 'max', 'mean', 'median', 'stdev']),
        advanced=data.get('advanced', ['p90', 'p95', 'p99', 'variance', 'cv']),
        analysis=data.get('analysis', ['confidence_interval', 'trend', 'outliers'])
    )


def parse_metric_config(data: Dict[str, Any]) -> MetricConfig:
    """Parse metric configuration from JSON."""
    derived = []
    if 'derived' in data:
        derived = [parse_derived_metric_config(d) for d in data['derived']]
    
    statistics = StatisticsConfig()
    if 'statistics' in data:
        statistics = parse_statistics_config(data['statistics'])
    
    return MetricConfig(
        primary=data['primary'],
        metric_labels=data.get('metric_labels', {}),
        threshold_mapping=data.get('threshold_mapping', {}),
        timestamp_field=data.get('timestamp_field', 'ts'),
        identifier_field=data.get('identifier_field', 'testcase'),
        derived=derived,
        statistics=statistics
    )

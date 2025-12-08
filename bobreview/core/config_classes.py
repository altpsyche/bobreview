"""
Focused configuration classes for ReportConfig.

Following the Interface Segregation Principle, ReportConfig is split into
focused config classes, each handling a single concern.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class ThresholdConfig:
    """
    Configuration for performance thresholds.
    
    Single Responsibility: Threshold values only.
    """
    draw_soft_cap: int = 550
    draw_hard_cap: int = 600
    tri_soft_cap: int = 100000
    tri_hard_cap: int = 120000
    high_load_draw_threshold: int = 600
    high_load_tri_threshold: int = 100000
    low_load_draw_threshold: int = 400
    low_load_tri_threshold: int = 50000
    outlier_sigma: float = 2.0
    mad_threshold: float = 3.5  # MAD threshold for outlier detection


@dataclass
class LLMConfig:
    """
    Configuration for LLM provider settings.
    
    Single Responsibility: LLM settings only.
    """
    provider: str = "openai"  # 'openai', 'anthropic', 'ollama'
    api_key: Optional[str] = None  # API key for the selected provider
    api_base: Optional[str] = None  # Custom API base URL (e.g., for Ollama)
    model: str = "gpt-4o"  # Model name (provider-specific)
    temperature: float = 0.7
    max_tokens: int = 2000  # Max tokens for LLM responses
    chunk_size: int = 10  # Number of data samples to send per LLM call
    combine_warning_threshold: int = 100000  # Character count threshold for warning
    use_cache: bool = True


@dataclass
class CacheConfig:
    """
    Configuration for caching.
    
    Single Responsibility: Cache settings only.
    """
    cache_dir: Path = Path(".bobreview_cache")
    use_cache: bool = True
    clear_cache: bool = False


@dataclass
class ExecutionConfig:
    """
    Configuration for execution behavior.
    
    Single Responsibility: Execution settings only.
    """
    dry_run: bool = False
    sample_size: Optional[int] = None
    verbose: bool = False
    quiet: bool = False
    enable_recommendations: bool = True


@dataclass
class OutputConfig:
    """
    Configuration for output settings.
    
    Single Responsibility: Output settings only.
    """
    embed_images: bool = True  # Embed images as base64 in HTML
    linked_css: bool = False  # Use external CSS file
    theme_id: str = 'dark'  # Report theme
    disabled_pages: Optional[List[str]] = None  # Page IDs to exclude
    
    def __post_init__(self):
        """Initialize mutable default fields."""
        if self.disabled_pages is None:
            self.disabled_pages = []


@dataclass
class ReportConfig:
    """
    Main configuration for report generation.
    
    Composes focused config classes, following the Interface Segregation Principle.
    """
    title: str = "Performance Analysis Report"
    location: str = "Unknown Location"
    
    # Focused config classes
    thresholds: ThresholdConfig = None
    llm: LLMConfig = None
    cache: CacheConfig = None
    execution: ExecutionConfig = None
    output: OutputConfig = None
    
    def __post_init__(self):
        """Initialize focused configs if not provided."""
        if self.thresholds is None:
            self.thresholds = ThresholdConfig()
        if self.llm is None:
            self.llm = LLMConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.execution is None:
            self.execution = ExecutionConfig()
        if self.output is None:
            self.output = OutputConfig()


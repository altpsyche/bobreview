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
    
    # ─────────────────────────────────────────────────────────────────────────
    # Backward Compatibility Properties
    # ─────────────────────────────────────────────────────────────────────────
    # These properties delegate to focused configs for backward compatibility
    
    # Threshold properties
    @property
    def draw_soft_cap(self) -> int:
        return self.thresholds.draw_soft_cap
    
    @draw_soft_cap.setter
    def draw_soft_cap(self, value: int):
        self.thresholds.draw_soft_cap = value
    
    @property
    def draw_hard_cap(self) -> int:
        return self.thresholds.draw_hard_cap
    
    @draw_hard_cap.setter
    def draw_hard_cap(self, value: int):
        self.thresholds.draw_hard_cap = value
    
    @property
    def tri_soft_cap(self) -> int:
        return self.thresholds.tri_soft_cap
    
    @tri_soft_cap.setter
    def tri_soft_cap(self, value: int):
        self.thresholds.tri_soft_cap = value
    
    @property
    def tri_hard_cap(self) -> int:
        return self.thresholds.tri_hard_cap
    
    @tri_hard_cap.setter
    def tri_hard_cap(self, value: int):
        self.thresholds.tri_hard_cap = value
    
    @property
    def high_load_draw_threshold(self) -> int:
        return self.thresholds.high_load_draw_threshold
    
    @high_load_draw_threshold.setter
    def high_load_draw_threshold(self, value: int):
        self.thresholds.high_load_draw_threshold = value
    
    @property
    def high_load_tri_threshold(self) -> int:
        return self.thresholds.high_load_tri_threshold
    
    @high_load_tri_threshold.setter
    def high_load_tri_threshold(self, value: int):
        self.thresholds.high_load_tri_threshold = value
    
    @property
    def low_load_draw_threshold(self) -> int:
        return self.thresholds.low_load_draw_threshold
    
    @low_load_draw_threshold.setter
    def low_load_draw_threshold(self, value: int):
        self.thresholds.low_load_draw_threshold = value
    
    @property
    def low_load_tri_threshold(self) -> int:
        return self.thresholds.low_load_tri_threshold
    
    @low_load_tri_threshold.setter
    def low_load_tri_threshold(self, value: int):
        self.thresholds.low_load_tri_threshold = value
    
    @property
    def outlier_sigma(self) -> float:
        return self.thresholds.outlier_sigma
    
    @outlier_sigma.setter
    def outlier_sigma(self, value: float):
        self.thresholds.outlier_sigma = value
    
    @property
    def mad_threshold(self) -> float:
        return self.thresholds.mad_threshold
    
    @mad_threshold.setter
    def mad_threshold(self, value: float):
        self.thresholds.mad_threshold = value
    
    # LLM properties
    @property
    def llm_provider(self) -> str:
        return self.llm.provider
    
    @llm_provider.setter
    def llm_provider(self, value: str):
        self.llm.provider = value
    
    @property
    def llm_api_key(self) -> Optional[str]:
        return self.llm.api_key
    
    @llm_api_key.setter
    def llm_api_key(self, value: Optional[str]):
        self.llm.api_key = value
    
    @property
    def llm_api_base(self) -> Optional[str]:
        return self.llm.api_base
    
    @llm_api_base.setter
    def llm_api_base(self, value: Optional[str]):
        self.llm.api_base = value
    
    @property
    def llm_model(self) -> str:
        return self.llm.model
    
    @llm_model.setter
    def llm_model(self, value: str):
        self.llm.model = value
    
    @property
    def openai_model(self) -> str:
        """Alias for llm.model (backward compatibility)."""
        return self.llm.model
    
    @openai_model.setter
    def openai_model(self, value: str):
        self.llm.model = value
    
    @property
    def llm_temperature(self) -> float:
        return self.llm.temperature
    
    @llm_temperature.setter
    def llm_temperature(self, value: float):
        self.llm.temperature = value
    
    @property
    def llm_max_tokens(self) -> int:
        return self.llm.max_tokens
    
    @llm_max_tokens.setter
    def llm_max_tokens(self, value: int):
        self.llm.max_tokens = value
    
    @property
    def llm_chunk_size(self) -> int:
        return self.llm.chunk_size
    
    @llm_chunk_size.setter
    def llm_chunk_size(self, value: int):
        self.llm.chunk_size = value
    
    @property
    def llm_combine_warning_threshold(self) -> int:
        return self.llm.combine_warning_threshold
    
    @llm_combine_warning_threshold.setter
    def llm_combine_warning_threshold(self, value: int):
        self.llm.combine_warning_threshold = value
    
    @property
    def use_cache(self) -> bool:
        return self.llm.use_cache
    
    @use_cache.setter
    def use_cache(self, value: bool):
        self.llm.use_cache = value
    
    # Cache properties
    @property
    def cache_dir(self) -> Path:
        return self.cache.cache_dir
    
    @cache_dir.setter
    def cache_dir(self, value: Path):
        self.cache.cache_dir = value
    
    @property
    def clear_cache(self) -> bool:
        return self.cache.clear_cache
    
    @clear_cache.setter
    def clear_cache(self, value: bool):
        self.cache.clear_cache = value
    
    # Execution properties
    @property
    def dry_run(self) -> bool:
        return self.execution.dry_run
    
    @dry_run.setter
    def dry_run(self, value: bool):
        self.execution.dry_run = value
    
    @property
    def sample_size(self) -> Optional[int]:
        return self.execution.sample_size
    
    @sample_size.setter
    def sample_size(self, value: Optional[int]):
        self.execution.sample_size = value
    
    @property
    def verbose(self) -> bool:
        return self.execution.verbose
    
    @verbose.setter
    def verbose(self, value: bool):
        self.execution.verbose = value
    
    @property
    def quiet(self) -> bool:
        return self.execution.quiet
    
    @quiet.setter
    def quiet(self, value: bool):
        self.execution.quiet = value
    
    @property
    def enable_recommendations(self) -> bool:
        return self.execution.enable_recommendations
    
    @enable_recommendations.setter
    def enable_recommendations(self, value: bool):
        self.execution.enable_recommendations = value
    
    # Output properties
    @property
    def embed_images(self) -> bool:
        return self.output.embed_images
    
    @embed_images.setter
    def embed_images(self, value: bool):
        self.output.embed_images = value
    
    @property
    def linked_css(self) -> bool:
        return self.output.linked_css
    
    @linked_css.setter
    def linked_css(self, value: bool):
        self.output.linked_css = value
    
    @property
    def theme_id(self) -> str:
        return self.output.theme_id
    
    @theme_id.setter
    def theme_id(self, value: str):
        self.output.theme_id = value
    
    @property
    def disabled_pages(self) -> Optional[List[str]]:
        return self.output.disabled_pages
    
    @disabled_pages.setter
    def disabled_pages(self, value: Optional[List[str]]):
        self.output.disabled_pages = value


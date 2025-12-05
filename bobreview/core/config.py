#!/usr/bin/env python3
"""
Configuration and data models for BobReview.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    title: str = "Performance Analysis Report"
    location: str = "Unknown Location"
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
    enable_recommendations: bool = True
    
    # LLM provider settings (unified across all providers)
    llm_provider: str = "openai"  # 'openai', 'anthropic', 'ollama'
    llm_api_key: Optional[str] = None  # API key for the selected provider
    llm_api_base: Optional[str] = None  # Custom API base URL (e.g., for Ollama)
    llm_model: str = "gpt-4o"  # Model name (provider-specific)
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000  # Max tokens for LLM responses
    llm_chunk_size: int = 10  # Number of data samples to send per LLM call
    llm_combine_warning_threshold: int = 100000  # Character count threshold for warning
    
    # Caching
    cache_dir: Path = Path(".bobreview_cache")
    use_cache: bool = True
    clear_cache: bool = False
    
    # Execution
    dry_run: bool = False
    sample_size: Optional[int] = None
    verbose: bool = False
    quiet: bool = False
    
    # Output
    embed_images: bool = True  # Embed images as base64 in HTML
    linked_css: bool = False  # Use external CSS file
    theme_id: str = 'dark'  # Report theme
    disabled_pages: Optional[List[str]] = None  # Page IDs to exclude
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.disabled_pages is None:
            self.disabled_pages = []


def validate_config(config: ReportConfig) -> List[str]:
    """
    Validate a ReportConfig for logical consistency and return any validation errors.
    
    Checks:
    - draw_soft_cap is less than or equal to draw_hard_cap
    - tri_soft_cap is less than or equal to tri_hard_cap
    - All threshold values (caps and load thresholds) are non-negative
    - outlier_sigma is greater than 0
    - mad_threshold is greater than 0
    - llm_chunk_size is greater than 0
    - llm_max_tokens is greater than 0
    - llm_combine_warning_threshold is greater than 0
    - sample_size, if provided, is greater than 0
    - llm_temperature is between 0 and 2 (inclusive of 0 and 2)
    - llm_provider is a valid provider name
    
    Parameters:
        config (ReportConfig): Configuration to validate.
    
    Returns:
        List[str]: A list of human-readable error messages for each violated constraint; empty if config is valid.
    """
    errors = []
    
    # Check threshold ordering
    if config.draw_soft_cap > config.draw_hard_cap:
        errors.append("draw_soft_cap must be <= draw_hard_cap")
    
    if config.tri_soft_cap > config.tri_hard_cap:
        errors.append("tri_soft_cap must be <= tri_hard_cap")
    
    # Check non-negative thresholds
    if config.draw_soft_cap < 0:
        errors.append("draw_soft_cap must be non-negative")
    
    if config.draw_hard_cap < 0:
        errors.append("draw_hard_cap must be non-negative")
    
    if config.tri_soft_cap < 0:
        errors.append("tri_soft_cap must be non-negative")
    
    if config.tri_hard_cap < 0:
        errors.append("tri_hard_cap must be non-negative")
    
    if config.high_load_draw_threshold < 0:
        errors.append("high_load_draw_threshold must be non-negative")
    
    if config.high_load_tri_threshold < 0:
        errors.append("high_load_tri_threshold must be non-negative")
    
    if config.low_load_draw_threshold < 0:
        errors.append("low_load_draw_threshold must be non-negative")
    
    if config.low_load_tri_threshold < 0:
        errors.append("low_load_tri_threshold must be non-negative")
    
    if config.outlier_sigma <= 0:
        errors.append("outlier_sigma must be > 0")
    
    if config.mad_threshold <= 0:
        errors.append("mad_threshold must be > 0")
    
    if config.llm_chunk_size <= 0:
        errors.append("llm_chunk_size must be > 0")
    
    if config.llm_max_tokens <= 0:
        errors.append("llm_max_tokens must be > 0")
    
    if config.llm_combine_warning_threshold <= 0:
        errors.append("llm_combine_warning_threshold must be > 0")
    
    if config.sample_size is not None and config.sample_size <= 0:
        errors.append("sample_size must be > 0")
    
    if config.llm_temperature < 0 or config.llm_temperature > 2:
        errors.append("llm_temperature must be between 0 and 2")
    
    # Validate provider
    valid_providers = ['openai', 'anthropic', 'ollama']
    if config.llm_provider not in valid_providers:
        errors.append(f"llm_provider must be one of: {', '.join(valid_providers)}")
    
    return errors

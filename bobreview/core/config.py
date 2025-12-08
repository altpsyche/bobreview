#!/usr/bin/env python3
"""
Configuration and data models for BobReview.
"""

from typing import List

# Import focused config classes
from .config_classes import (
    ReportConfig,
    ThresholdConfig,
    LLMConfig,
    CacheConfig,
    ExecutionConfig,
    OutputConfig,
)

# Re-export for backward compatibility
__all__ = [
    'ReportConfig',
    'ThresholdConfig',
    'LLMConfig',
    'CacheConfig',
    'ExecutionConfig',
    'OutputConfig',
    'validate_config',
]


def validate_config(config: ReportConfig) -> List[str]:
    """
    Validate a ReportConfig for logical consistency.
    
    Performs validation of numeric thresholds, size limits, and LLM settings and collects human-readable error messages for each violated constraint.
    
    Checks performed:
    - draw_soft_cap <= draw_hard_cap and tri_soft_cap <= tri_hard_cap
    - draw/tri caps and high/low load thresholds are >= 0
    - outlier_sigma > 0
    - mad_threshold > 0
    - llm_chunk_size > 0
    - llm_max_tokens > 0
    - llm_combine_warning_threshold > 0
    - sample_size, if provided, > 0
    - llm_temperature is between 0 and 2 (inclusive)
    - llm_provider is one of: "openai", "anthropic", "ollama"
    
    Parameters:
        config (ReportConfig): Configuration instance to validate.
    
    Returns:
        List[str]: List of error messages describing each violated constraint; empty if the configuration is valid.
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
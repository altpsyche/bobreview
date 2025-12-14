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

# Re-exports from models module
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
    
    Performs generic validation of numeric thresholds, size limits, and LLM settings.
    Threshold validation is generic - checks that numeric thresholds are non-negative
    and that soft_cap <= hard_cap for any threshold pairs found.
    
    Checks performed:
    - Generic threshold validation (non-negative values, soft_cap <= hard_cap pairs)
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
    thresholds = config.thresholds
    llm = config.llm
    execution = config.execution
    
    # Generic threshold validation - check all numeric thresholds
    threshold_dict = dict(thresholds) if isinstance(thresholds, dict) else {}
    
    # Find soft_cap/hard_cap pairs and validate ordering
    soft_caps = {k: v for k, v in threshold_dict.items() if k.endswith('_soft_cap')}
    for soft_key, soft_value in soft_caps.items():
        if not isinstance(soft_value, (int, float)):
            continue
        
        # Find corresponding hard_cap
        hard_key = soft_key.replace('_soft_cap', '_hard_cap')
        if hard_key in threshold_dict:
            hard_value = threshold_dict[hard_key]
            if isinstance(hard_value, (int, float)):
                if soft_value > hard_value:
                    errors.append(f"{soft_key} ({soft_value}) must be <= {hard_key} ({hard_value})")
        
        # Check non-negative
        if soft_value < 0:
            errors.append(f"{soft_key} must be non-negative")
    
    # Validate hard_caps are non-negative
    hard_caps = {k: v for k, v in threshold_dict.items() if k.endswith('_hard_cap')}
    for hard_key, hard_value in hard_caps.items():
        if isinstance(hard_value, (int, float)) and hard_value < 0:
            errors.append(f"{hard_key} must be non-negative")
    
    # Validate thresholds are non-negative
    threshold_keys = {k: v for k, v in threshold_dict.items() if k.endswith('_threshold')}
    for threshold_key, threshold_value in threshold_keys.items():
        if isinstance(threshold_value, (int, float)) and threshold_value < 0:
            errors.append(f"{threshold_key} must be non-negative")
    
    # Validate generic outlier thresholds (if present)
    outlier_sigma = threshold_dict.get('outlier_sigma')
    if outlier_sigma is not None and isinstance(outlier_sigma, (int, float)) and outlier_sigma <= 0:
        errors.append("outlier_sigma must be > 0")
    
    mad_threshold = threshold_dict.get('mad_threshold')
    if mad_threshold is not None and isinstance(mad_threshold, (int, float)) and mad_threshold <= 0:
        errors.append("mad_threshold must be > 0")
    
    # Note: All threshold validation is now generic - no hardcoded field names
    
    if llm.chunk_size <= 0:
        errors.append("llm_chunk_size must be > 0")
    
    if llm.max_tokens <= 0:
        errors.append("llm_max_tokens must be > 0")
    
    if llm.combine_warning_threshold <= 0:
        errors.append("llm_combine_warning_threshold must be > 0")
    
    if execution.sample_size is not None and execution.sample_size <= 0:
        errors.append("sample_size must be > 0")
    
    if llm.temperature < 0 or llm.temperature > 2:
        errors.append("llm_temperature must be between 0 and 2")
    
    # Validate provider
    valid_providers = ['openai', 'anthropic', 'ollama']
    if llm.provider not in valid_providers:
        errors.append(f"llm_provider must be one of: {', '.join(valid_providers)}")
    
    return errors
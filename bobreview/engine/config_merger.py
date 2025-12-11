"""
Configuration merger for report systems.

Responsible for merging JSON configuration into ReportConfig.
"""

from typing import Any
from .schema import ReportSystemDefinition
from ..core import ReportConfig
from ..core.config_utils import merge_config


class ConfigMerger:
    """
    Merges report system configuration into ReportConfig.
    
    Single Responsibility: Configuration merging only.
    """
    
    def merge(self, config: ReportConfig, system_def: ReportSystemDefinition) -> None:
        """
        Merge JSON configuration into ReportConfig.
        
        Note: CLI overrides have already been merged into the JSON definition
        by the loader, so we just update the config with JSON values.
        
        Parameters:
            config: ReportConfig to merge into
            system_def: ReportSystemDefinition with configuration values
        """
        # Merge thresholds
        merge_config(config.thresholds, system_def.thresholds)
        
        # Merge LLM config
        llm_cfg = system_def.llm_config
        config.llm.provider = llm_cfg.provider
        config.llm.model = llm_cfg.model
        config.llm.temperature = llm_cfg.temperature
        config.llm.max_tokens = llm_cfg.max_tokens
        config.llm.chunk_size = llm_cfg.chunk_size
        config.llm.enable_cache = llm_cfg.enable_cache
        if llm_cfg.api_base is not None:
            config.llm.api_base = llm_cfg.api_base
        if llm_cfg.api_key is not None:
            config.llm.api_key = llm_cfg.api_key
        
        # Merge output config
        output_cfg = system_def.output
        config.output.embed_images = output_cfg.embed_images
        config.output.linked_css = output_cfg.linked_css
        
        # Merge theme config
        theme_cfg = system_def.theme
        config.output.theme_id = theme_cfg.preset


#!/usr/bin/env python3
"""
LLM response caching for BobReview.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .utils import log_warning, log_success, log_verbose


class LLMCache:
    """Cache for LLM responses to avoid redundant API calls."""
    
    def __init__(self, cache_dir: Path, enabled: bool = True, config=None):
        """
        Initialize the LLMCache.
        
        Ensures the cache directory exists when caching is enabled.
        
        Parameters:
            cache_dir (Path): Filesystem path where cache files will be stored.
            enabled (bool): If True, enables caching and creates `cache_dir` if missing.
            config (Optional[ReportConfig]): Optional configuration used for logging and behavior; may be None.
        """
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.config = config
        if enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, prompt: str, data_table: str, model: str) -> str:
        """
        Create a deterministic SHA-256 cache key representing the combination of prompt, data table, and model.
        
        Parameters:
            prompt (str): The LLM prompt text.
            data_table (str): The optional formatted data table string included with the prompt.
            model (str): The model identifier used for the request.
        
        Returns:
            str: Hexadecimal SHA-256 digest suitable for use as a cache filename or key.
        """
        content = f"{prompt}|{data_table}|{model}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, prompt: str, data_table: str, model: str) -> Optional[str]:
        """
        Return the cached LLM response for the given prompt and data table when available.
        
        Returns:
            str: Cached response text if present.
            None: If caching is disabled, no cache entry exists, or the cache file cannot be read.
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(prompt, data_table, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('response')
            except Exception as e:
                log_warning(f"Failed to read cache file {cache_file}: {e}", self.config)
                return None
        
        return None
    
    def set(self, prompt: str, data_table: str, model: str, response: str):
        """
        Write the LLM response into the cache directory using a deterministic filename based on the prompt, data table, and model.
        
        If caching is disabled, this is a no-op. On I/O or serialization errors the function logs a warning and does not raise.
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(prompt, data_table, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'prompt_hash': cache_key,
                    'model': model,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            log_warning(f"Failed to write cache file {cache_file}: {e}", self.config)
    
    def clear(self):
        """
        Remove all JSON cache files from the cache directory.
        
        Deletes all files matching `*.json` in the cache directory if it exists. Skips silently when the cache directory is missing; logs a warning for any file deletion errors and logs a success message summarizing how many files were cleared.
        """
        if not self.cache_dir.exists():
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                log_warning(f"Failed to delete cache file {cache_file}: {e}", self.config)
        
        log_success(f"Cleared {count} cached responses", self.config)


# Global cache instance
_cache_instance: Optional[LLMCache] = None


def get_cache() -> Optional[LLMCache]:
    """Get the global cache instance."""
    return _cache_instance


def init_cache(config):
    """
    Initialize the module-level LLM cache using values from `config`.
    
    Parameters:
        config (ReportConfig): Configuration containing `cache_dir` and `use_cache`; used to construct the LLMCache instance that will be returned by `get_cache()`.
    """
    global _cache_instance
    _cache_instance = LLMCache(config.cache_dir, enabled=config.use_cache, config=config)


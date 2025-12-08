"""
LLM service for AI content generation.

This service handles LLM content generation:
- Building prompts from templates
- Calling LLM providers
- Caching responses
- Combining chunks
"""

from typing import List, Dict, Any, Optional
import logging

from .base import BaseService, LLMServiceError

logger = logging.getLogger(__name__)


class LLMService(BaseService):
    """
    Service for LLM content generation.
    
    Extracted from ReportSystemExecutor.generate_llm_content() to enable:
    - Independent testing
    - Plugin replacement with custom generators
    - Provider abstraction
    
    Example:
        service = LLMService(config={'provider': 'openai', 'model': 'gpt-4o'})
        content = service.generate(
            generator_config=generator,
            data_points=data,
            stats=stats,
            context={'location': 'City Level'}
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM service."""
        super().__init__(config)
        self._client = None
        self._cache = None
    
    @property
    def client(self):
        """Get LLM client, initializing if needed."""
        if self._client is None:
            from ..llm import LLMClient
            self._client = LLMClient(
                provider=self.config.get('provider', 'openai'),
                api_key=self.config.get('api_key'),
                model=self.config.get('model'),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 2000)
            )
        return self._client
    
    @property
    def cache(self):
        """Get cache instance if caching is enabled."""
        if self._cache is None and self.config.get('use_cache', True):
            from ..core import get_cache
            self._cache = get_cache()
        return self._cache
    
    def generate(
        self,
        generator_config: Any,
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        context: Dict[str, Any],
        dry_run: bool = False,
        report_config: Any = None
    ) -> str:
        """
        Generate content for a single LLM generator.
        
        Supports both Python-based generators (for known generator IDs) and
        template-based generators (for custom generators defined in JSON).
        
        Parameters:
            generator_config: LLMGeneratorConfig from report system
            data_points: Input data points
            stats: Statistical analysis results
            context: Additional context (thresholds, config, etc.)
            dry_run: If True, return placeholder instead of calling LLM
            report_config: ReportConfig instance for Python generators
            
        Returns:
            Generated content string
        """
        if dry_run:
            return self._get_placeholder(generator_config.id, generator_config.name)
        
        # Check if there's a Python-based generator for this ID (from PluginRegistry)
        gen_wrapper = self._get_python_generator(generator_config.id, generator_config.name)
        
        if gen_wrapper and report_config:
            # Extract actual function from wrapper (registered generators have .generate attribute)
            gen_func = getattr(gen_wrapper, 'generate', gen_wrapper)
            if callable(gen_func):
                try:
                    # Check if it's an interface-based generator (takes context parameter)
                    import inspect
                    sig = inspect.signature(gen_func)
                    params = list(sig.parameters.keys())
                    
                    # If it has 4 parameters (data_points, stats, config, context), it's interface-based
                    if len(params) == 4:
                        return gen_func(data_points, stats, report_config, context)
                    else:
                        # Old-style function (data_points, stats, config, images_dir_rel)
                        from ..report_systems.llm_generator_base import LLMGeneratorAdapter
                        adapter = LLMGeneratorAdapter(gen_func, generator_config)
                        return adapter.generate(data_points, stats, report_config, context.get('images_dir_rel', ''))
                except Exception as e:
                    logger.warning(f"Python generator failed, falling back to template: {e}")
        
        # Use template-based generator
        from ..report_systems.llm_generator_base import LLMGeneratorTemplate
        from ..llm import call_llm
        
        generator = LLMGeneratorTemplate(generator_config)
        
        # Select data samples
        selected_data = generator.select_data_samples(data_points, stats)
        
        # Build prompt
        prompt = generator.build_prompt(stats, selected_data, context)
        
        if not prompt:
            logger.warning(f"Empty prompt for generator: {generator_config.id}")
            return ""
        
        # Format data table
        data_table = generator.format_data_table(selected_data)
        
        # Check cache
        cache_key = self._make_cache_key(generator_config.id, prompt)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {generator_config.id}")
                return cached
        
        # Call LLM
        try:
            response = call_llm(prompt, data_table=data_table, config=report_config)
            
            # Cache response
            if self.cache and response:
                self.cache.set(cache_key, response)
            
            return response
            
        except Exception as e:
            raise LLMServiceError(
                f"LLM generation failed for {generator_config.id}: {e}"
            ) from e
    
    def _get_python_generator(self, gen_id: str, gen_name: str):
        """
        Get Python-based generator function from the PluginRegistry.
        
        This allows plugins to register custom generators instead of
        hardcoding them in the service.
        """
        from ..plugins import get_registry
        
        registry = get_registry()
        
        # Try to get from registry first (plugin-registered generators)
        generator = registry.llm_generators.get(gen_id)
        if generator:
            return generator
        
        generator = registry.llm_generators.get(gen_name)
        if generator:
            return generator
        
        # No generator found in registry
        return None
    
    def generate_all(
        self,
        generators: List[Any],
        data_points: List[Dict[str, Any]],
        stats: Dict[str, Any],
        context: Dict[str, Any],
        dry_run: bool = False,
        report_config: Any = None
    ) -> Dict[str, str]:
        """
        Generate content for all configured generators.
        
        Parameters:
            generators: List of LLMGeneratorConfig
            data_points: Input data points
            stats: Statistical analysis results
            context: Additional context
            dry_run: If True, return placeholders
            report_config: ReportConfig instance
            
        Returns:
            Dict mapping generator ID to content
        """
        results = {}
        enabled = [g for g in generators if g.enabled]
        total = len(enabled)
        
        for i, generator in enumerate(enabled, 1):
            # Use config-aware logging if report_config is available
            if report_config:
                from ..core import log_info, log_error
                log_info(f"[{i}/{total}] Generating: {generator.name}", report_config)
            else:
                logger.info(f"[{i}/{total}] Generating: {generator.name}")
            
            try:
                content = self.generate(
                    generator,
                    data_points,
                    stats,
                    context,
                    dry_run=dry_run,
                    report_config=report_config
                )
                results[generator.id] = content
                if report_config:
                    from ..core import log_verbose
                    log_verbose(f"Generated content for: {generator.id}", report_config)
                else:
                    logger.debug(f"Generated content for: {generator.id}")
                
            except LLMServiceError as e:
                if report_config:
                    from ..core import log_error
                    log_error(f"LLM generation failed for {generator.id}: {e}")
                else:
                    logger.error(str(e))
                results[generator.id] = self._get_error_placeholder(generator.id, str(e))
        
        return results
    
    def _make_cache_key(self, generator_id: str, prompt: str) -> str:
        """Create a cache key from generator ID and prompt."""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        return f"llm_{generator_id}_{prompt_hash}"
    
    def _get_placeholder(self, generator_id: str, generator_name: str = None) -> str:
        """Get placeholder content for dry run mode."""
        name = generator_name or generator_id
        placeholders = {
            'executive_summary': (
                f"<p>Dry run mode - {name} would appear here</p>"
            ),
            'metric_deep_dive': (
                f"<p>Dry run mode - {name} would appear here</p>"
            ),
            'optimization_checklist': (
                f"<p>Dry run mode - {name} would appear here</p>"
            ),
        }
        return placeholders.get(
            generator_id,
            f"<p>Dry run mode - {name} would appear here</p>"
        )
    
    def _get_error_placeholder(self, generator_id: str, error: str) -> str:
        """Get placeholder content when generation fails."""
        return f"**{generator_id}**\n\n*Generation failed: {error}*"

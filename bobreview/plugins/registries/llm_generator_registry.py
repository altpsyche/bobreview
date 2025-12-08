"""
LLM generator registry for managing LLM generators.
"""

from typing import Dict, Type, Optional
import logging

from .base_registry import BaseRegistry

logger = logging.getLogger(__name__)


class LLMGeneratorRegistry(BaseRegistry):
    """
    Registry for LLM generators.
    
    Single Responsibility: LLM generator registration and retrieval only.
    """
    
    def __init__(self):
        """Initialize the LLM generator registry."""
        super().__init__()
        self._generators: Dict[str, Type] = {}
    
    def register(self, generator_cls: Type, plugin_name: str = "") -> None:
        """
        Register an LLM generator class.
        
        Parameters:
            generator_cls: Generator class with `generator_name` attribute
            plugin_name: Name of the plugin registering this generator
        """
        generator_name = getattr(generator_cls, 'generator_name', generator_cls.__name__)
        
        if generator_name in self._generators:
            logger.warning(f"Overwriting existing LLM generator: {generator_name}")
        
        self._generators[generator_name] = generator_cls
        self._register_component(f"llm:{generator_name}", plugin_name, overwrite=True)
        logger.debug(f"Registered LLM generator: {generator_name} from {plugin_name or 'core'}")
    
    def get(self, generator_name: str) -> Optional[Type]:
        """Get an LLM generator class by name."""
        return self._generators.get(generator_name)
    
    def get_all(self) -> Dict[str, Type]:
        """Get all registered LLM generators."""
        return dict(self._generators)
    
    def unregister_plugin_components(self, plugin_name: str) -> int:
        """Unregister all generators from a specific plugin."""
        count = 0
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name and key.startswith('llm:')
        ]
        
        for key in to_remove:
            generator_name = key.split(':', 1)[1]
            if generator_name in self._generators:
                del self._generators[generator_name]
                count += 1
            del self._component_owners[key]
        
        logger.info(f"Unregistered {count} LLM generators from plugin: {plugin_name}")
        return count


"""
LLM generator registry system for modular content generation.

This module provides a registry pattern that allows LLM generators to self-register,
making it easy to add new generators without modifying core orchestration code.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import ReportConfig


# Type alias for generator function signature
GeneratorFunc = Callable[
    [List[Dict[str, Any]], Dict[str, Any], "ReportConfig", str],
    Any  # Can return str or Dict[str, str]
]


@dataclass
class PromptCategory:
    """
    Defines a category for structured LLM prompts.
    
    Attributes:
        id: Unique identifier for the category (e.g., 'lod', 'occlusion')
        title: Display title (e.g., 'LOD & Detail Management')
        focus: What the LLM should focus on for this category
        priority: Optional priority for ordering (lower = higher priority)
    """
    id: str
    title: str
    focus: str
    priority: int = 50


@dataclass
class LLMGeneratorDefinition:
    """
    Defines an LLM generator with metadata for content generation.
    
    Attributes:
        section_name: Unique name matching PageDefinition.llm_section (e.g., 'Executive Summary')
        generator_func: Function that generates the LLM content
        description: Human-readable description of what this generator produces
        categories: Optional list of PromptCategory for structured generators
        prompt_template: Optional base prompt template (generator can use or ignore)
    """
    section_name: str
    generator_func: GeneratorFunc
    description: str = ""
    categories: List[PromptCategory] = None
    prompt_template: str = ""
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []


# Global registry of all LLM generators
_LLM_REGISTRY: Dict[str, LLMGeneratorDefinition] = {}


def register_llm_generator(generator: LLMGeneratorDefinition) -> None:
    """
    Register an LLM generator definition in the global registry.
    
    Parameters:
        generator: LLMGeneratorDefinition instance to register
    
    Raises:
        ValueError: If a generator with the same section_name is already registered
    """
    if generator.section_name in _LLM_REGISTRY:
        raise ValueError(f"LLM generator '{generator.section_name}' is already registered")
    _LLM_REGISTRY[generator.section_name] = generator


def get_llm_generator(section_name: str) -> Optional[GeneratorFunc]:
    """
    Get the generator function for a given section name.
    
    Parameters:
        section_name: The name of the LLM section
    
    Returns:
        The generator function if found, None otherwise
    """
    gen = _LLM_REGISTRY.get(section_name)
    return gen.generator_func if gen else None


def get_all_llm_generators() -> Dict[str, LLMGeneratorDefinition]:
    """Get the full LLM generator registry dictionary."""
    return _LLM_REGISTRY.copy()


def has_llm_generator(section_name: str) -> bool:
    """Check if a generator exists for the given section name."""
    return section_name in _LLM_REGISTRY


def clear_llm_registry() -> None:
    """Clear all registered LLM generators. Mainly used for testing."""
    _LLM_REGISTRY.clear()


def get_generator_categories(section_name: str) -> List[PromptCategory]:
    """
    Get the categories for a given generator.
    
    Parameters:
        section_name: The name of the LLM section
    
    Returns:
        List of PromptCategory sorted by priority, or empty list if none
    """
    gen = _LLM_REGISTRY.get(section_name)
    if gen and gen.categories:
        return sorted(gen.categories, key=lambda c: c.priority)
    return []


def get_generator_definition(section_name: str) -> Optional[LLMGeneratorDefinition]:
    """Get the full generator definition for a section."""
    return _LLM_REGISTRY.get(section_name)

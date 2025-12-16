"""
Core API: Minimal interfaces for BobReview.

This module defines the absolute minimum API that core provides.
All domain-specific interfaces have been moved to plugins.

Plugin-First Architecture:
- Core: Infrastructure only (template engine, component system, themes)  
- Plugins: All features (charts, LLM, parsing, components, themes)
- Users: YAML configuration only

See docs/ARCHITECTURE_REFACTOR.md for the full architecture.
"""

# No interfaces defined in core.
# 
# Previously contained:
# - DataParserInterface → Plugin defines parsing contract
# - LLMGeneratorInterface → Plugin component
# - ChartGeneratorInterface → Plugin component
# - ContextBuilderInterface → Plugin component
# - ComponentInterface → Use @register_component + PropTypes
#
# Plugins now use the Property Controls pattern:
#
#     from bobreview.core.components import register_component, PropTypes
#     
#     @register_component("my_component", plugin="my_plugin")
#     class MyComponent:
#         props = {
#             "title": PropTypes.string(required=True),
#             "value": PropTypes.number(default=0),
#         }
#         template = "my_plugin/components/my_component.html.j2"
#
# For data parsing, plugins define their own parser classes.
# There is no base interface - plugins have full freedom.

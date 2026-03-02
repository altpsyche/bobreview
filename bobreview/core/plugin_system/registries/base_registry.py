"""
Base registry class for shared functionality.
"""

from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RegistryCollisionError(Exception):
    """Raised when a component key collision occurs in strict mode."""
    pass


class BaseRegistry:
    """
    Base class for component registries.

    Provides common functionality for tracking component owners
    and detecting naming collisions between plugins.
    """

    def __init__(self):
        """Initialize the registry."""
        self._component_owners: Dict[str, str] = {}  # component_key -> plugin_name
        # Collision log: records every overwrite so auditing is possible
        # Each entry is (component_key, previous_owner, new_owner)
        self._collision_log: List[Tuple[str, str, str]] = []
        self._strict: bool = False

    def set_strict(self, strict: bool) -> None:
        """
        Enable or disable strict collision mode.

        When strict is True, attempting to register a component key
        that is already owned by a *different* plugin raises
        RegistryCollisionError instead of silently overwriting.

        Parameters:
            strict: Whether to raise on collision
        """
        self._strict = strict

    def _register_component(
        self,
        component_key: str,
        plugin_name: str = "",
        overwrite: bool = False
    ) -> None:
        """
        Register component ownership.

        Parameters:
            component_key: Unique key for the component
            plugin_name: Name of the plugin registering this component
            overwrite: Whether to allow overwriting existing registrations

        Raises:
            RegistryCollisionError: In strict mode when a different plugin
                already owns this key and overwrite is True
        """
        if component_key in self._component_owners:
            previous_owner = self._component_owners[component_key]
            is_different_owner = previous_owner != plugin_name

            if is_different_owner:
                self._collision_log.append(
                    (component_key, previous_owner, plugin_name)
                )

                if self._strict and overwrite:
                    raise RegistryCollisionError(
                        f"Component '{component_key}' is already registered by "
                        f"plugin '{previous_owner}'. Cannot overwrite in strict mode "
                        f"(requested by '{plugin_name}')."
                    )

                logger.warning(
                    f"Component '{component_key}' already registered by "
                    f"'{previous_owner}', overwriting with '{plugin_name}'"
                )
            elif not overwrite:
                logger.warning(f"Component already registered: {component_key}")

        self._component_owners[component_key] = plugin_name

    def get_component_owner(self, component_key: str) -> Optional[str]:
        """
        Get the plugin that registered a component.

        Parameters:
            component_key: Component key

        Returns:
            Plugin name or None
        """
        return self._component_owners.get(component_key)

    def get_collision_log(self) -> List[Tuple[str, str, str]]:
        """
        Get the collision log.

        Returns:
            List of (component_key, previous_owner, new_owner) tuples
        """
        return list(self._collision_log)

    def unregister_plugin_components(self, plugin_name: str) -> int:
        """
        Unregister all components from a specific plugin.

        Parameters:
            plugin_name: Name of the plugin to unregister

        Returns:
            Number of components unregistered
        """
        to_remove = [
            key for key, owner in self._component_owners.items()
            if owner == plugin_name
        ]

        for key in to_remove:
            del self._component_owners[key]

        # Clean collision log entries involving this plugin to prevent
        # unbounded growth across load/unload cycles.
        self._collision_log = [
            entry for entry in self._collision_log
            if entry[1] != plugin_name and entry[2] != plugin_name
        ]

        return len(to_remove)


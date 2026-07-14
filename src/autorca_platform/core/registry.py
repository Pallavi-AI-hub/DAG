"""Generic plugin registry for platform extension points."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Generic, TypeVar, cast

from autorca_platform.core.exceptions import PluginLookupError, PluginRegistrationError

T = TypeVar("T")


@dataclass(frozen=True, order=True)
class PluginKey:
    """Stable key identifying a registered plugin.

    Attributes:
        category: Extension category, such as ``metadata_loader`` or ``validator``.
        name: Plugin name unique within the category.
    """

    category: str
    name: str

    def __post_init__(self) -> None:
        """Validate key fields."""

        if not self.category.strip():
            raise PluginRegistrationError("Plugin category must be non-empty.")
        if not self.name.strip():
            raise PluginRegistrationError("Plugin name must be non-empty.")


@dataclass(frozen=True)
class PluginRegistration(Generic[T]):
    """Registered plugin metadata.

    Attributes:
        key: Plugin lookup key.
        plugin: Registered class, factory, or instance.
        description: Human-readable plugin purpose.
    """

    key: PluginKey
    plugin: T
    description: str


class PluginRegistry:
    """Thread-safe single-active-version plugin registry."""

    def __init__(self) -> None:
        """Create an empty plugin registry."""

        self._plugins: dict[PluginKey, PluginRegistration[object]] = {}
        self._lock = RLock()

    def register(
        self,
        category: str,
        name: str,
        plugin: T,
        *,
        description: str = "",
        replace: bool = False,
    ) -> T:
        """Register a plugin.

        Args:
            category: Extension category.
            name: Plugin name within the category.
            plugin: Plugin object, class, or factory.
            description: Optional human-readable purpose.
            replace: Whether an existing registration may be replaced.

        Returns:
            The registered plugin, allowing decorator usage.

        Raises:
            PluginRegistrationError: If the key already exists and replacement is disabled.
        """

        key = PluginKey(category=category, name=name)
        with self._lock:
            if key in self._plugins and not replace:
                raise PluginRegistrationError(
                    f"Plugin '{category}:{name}' is already registered."
                )
            self._plugins[key] = PluginRegistration(
                key=key,
                plugin=plugin,
                description=description,
            )
        return plugin

    def get(self, category: str, name: str, expected_type: type[T] | None = None) -> T:
        """Return a registered plugin by key.

        Args:
            category: Extension category.
            name: Plugin name within the category.
            expected_type: Optional runtime type assertion for plugin instances.

        Returns:
            Registered plugin.

        Raises:
            PluginLookupError: If the plugin does not exist or has the wrong runtime type.
        """

        key = PluginKey(category=category, name=name)
        with self._lock:
            registration = self._plugins.get(key)

        if registration is None:
            raise PluginLookupError(f"Plugin '{category}:{name}' is not registered.")

        plugin = registration.plugin
        if expected_type is not None and not isinstance(plugin, expected_type):
            raise PluginLookupError(
                f"Plugin '{category}:{name}' is not of expected type "
                f"'{expected_type.__name__}'."
            )
        return cast(T, plugin)

    def list(self, category: str | None = None) -> tuple[PluginRegistration[object], ...]:
        """List registered plugins.

        Args:
            category: Optional category filter.

        Returns:
            Sorted plugin registrations.
        """

        with self._lock:
            registrations = tuple(self._plugins.values())

        if category is not None:
            registrations = tuple(item for item in registrations if item.key.category == category)
        return tuple(sorted(registrations, key=lambda item: item.key))

    def clear(self) -> None:
        """Remove all plugins from the registry.

        This is intended for test isolation and controlled composition resets.
        """

        with self._lock:
            self._plugins.clear()


_DEFAULT_REGISTRY = PluginRegistry()


def get_default_registry() -> PluginRegistry:
    """Return the process-default plugin registry."""

    return _DEFAULT_REGISTRY


def register_plugin(
    category: str,
    name: str,
    *,
    description: str = "",
    registry: PluginRegistry | None = None,
    replace: bool = False,
) -> Callable[[T], T]:
    """Create a decorator that registers a plugin with a registry.

    Args:
        category: Extension category.
        name: Plugin name within the category.
        description: Optional human-readable purpose.
        registry: Optional registry override. Defaults to the process registry.
        replace: Whether an existing registration may be replaced.

    Returns:
        Decorator that registers and returns the decorated plugin.
    """

    selected_registry = registry or get_default_registry()

    def decorator(plugin: T) -> T:
        return selected_registry.register(
            category,
            name,
            plugin,
            description=description,
            replace=replace,
        )

    return decorator

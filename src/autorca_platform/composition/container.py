"""Composition root for assembling Phase 1 platform dependencies."""

from dataclasses import dataclass

from autorca_platform.core.config import PlatformConfig
from autorca_platform.core.logging import configure_logging
from autorca_platform.core.registry import PluginRegistry, get_default_registry

# Import plugins to trigger automatic registration
import autorca_platform.plugins.callbacks.autorca_callback_plugin  # noqa: F401
import autorca_platform.plugins.notifications.teams_plugin  # noqa: F401
import autorca_platform.plugins.observability.datadog_plugin  # noqa: F401
import autorca_platform.plugins.operators  # noqa: F401



@dataclass(frozen=True)
class Container:
    """Runtime container for shared platform dependencies.

    Attributes:
        config: Platform configuration.
        registry: Plugin registry used by the process.
    """

    config: PlatformConfig
    registry: PluginRegistry


def build_container(
    config: PlatformConfig | None = None,
    registry: PluginRegistry | None = None,
    *,
    configure_loggers: bool = True,
) -> Container:
    """Build the platform composition container.

    Args:
        config: Optional explicit configuration. Defaults to environment variables.
        registry: Optional explicit plugin registry. Defaults to the process registry.
        configure_loggers: Whether to configure root logging during composition.

    Returns:
        Runtime dependency container.
    """

    selected_config = config or PlatformConfig.from_env()
    selected_registry = registry or get_default_registry()

    if configure_loggers:
        configure_logging(selected_config)

    return Container(config=selected_config, registry=selected_registry)

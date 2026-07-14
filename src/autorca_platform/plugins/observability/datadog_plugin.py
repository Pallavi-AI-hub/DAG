"""Datadog observability sink plugin."""

import logging
from collections.abc import Mapping

from autorca_platform.core.registry import register_plugin
from autorca_platform.interfaces.observability_sink import ObservabilitySink

logger = logging.getLogger("autorca_platform.plugins.observability.datadog_plugin")


@register_plugin(
    "observability",
    "datadog",
    description="Datadog integration for tracking task metrics and events.",
    replace=True,
)
class DatadogPlugin(ObservabilitySink):
    """Datadog metrics and event emission plugin."""

    def emit_event(self, name: str, attributes: Mapping[str, str]) -> None:
        """Emit an event to the Datadog logs.

        Args:
            name: Event identifier.
            attributes: Custom metadata mapping.
        """

        logger.info(f"[Datadog Event] Name: {name} | Attributes: {dict(attributes)}")

    def emit_metric(self, name: str, value: float, tags: Mapping[str, str]) -> None:
        """Emit a metric to Datadog.

        Args:
            name: Metric identifier.
            value: Float metric value.
            tags: Dimension tags mapping.
        """

        logger.info(f"[Datadog Metric] Name: {name} | Value: {value} | Tags: {dict(tags)}")

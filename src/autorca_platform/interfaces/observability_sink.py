"""Observability sink interface for metrics and events."""

from typing import Mapping, Protocol


class ObservabilitySink(Protocol):
    """Contract for emitting observability signals."""

    def emit_event(self, name: str, attributes: Mapping[str, str]) -> None:
        """Emit an event to an observability backend.

        Args:
            name: Event name.
            attributes: Event attributes.
        """

    def emit_metric(self, name: str, value: float, tags: Mapping[str, str]) -> None:
        """Emit a numeric metric.

        Args:
            name: Metric name.
            value: Metric value.
            tags: Metric tags.
        """

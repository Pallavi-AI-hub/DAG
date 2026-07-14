"""No-op example plugin demonstrating Phase 1 registry mechanics."""

from dataclasses import dataclass

from autorca_platform.core.registry import register_plugin


@register_plugin(
    "validator",
    "noop",
    description="Example validator plugin that accepts every subject.",
    replace=True,
)
@dataclass(frozen=True)
class NoopValidator:
    """Example validator that intentionally performs no checks."""

    reason: str = "Phase 1 smoke-test plugin"

    def validate(self, subject: object) -> None:
        """Accept a subject without raising.

        Args:
            subject: Any object supplied by the caller.
        """

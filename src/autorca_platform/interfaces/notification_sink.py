"""Notification sink interface for outbound platform messages."""

from typing import Mapping, Protocol


class NotificationSink(Protocol):
    """Contract for sending human-facing platform notifications."""

    def notify(self, subject: str, body: str, metadata: Mapping[str, str]) -> None:
        """Send a notification.

        Args:
            subject: Short message title.
            body: Notification body.
            metadata: Structured metadata for routing, auditing, or formatting.
        """

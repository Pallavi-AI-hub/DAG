"""Microsoft Teams notification sink plugin."""

import logging
from collections.abc import Mapping

from autorca_platform.core.registry import register_plugin
from autorca_platform.interfaces.notification_sink import NotificationSink

logger = logging.getLogger("autorca_platform.plugins.notifications.teams_plugin")


@register_plugin(
    "notification",
    "teams",
    description="Microsoft Teams webhook integration for sending Adaptive Card alerts.",
    replace=True,
)
class TeamsPlugin(NotificationSink):
    """Teams notification sink plugin."""

    def notify(self, subject: str, body: str, metadata: Mapping[str, str]) -> None:
        """Send an Adaptive Card format message mockup to Teams logs.

        Args:
            subject: Brief title.
            body: Alert details.
            metadata: Filtering and routing tags.
        """

        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "medium",
                                "weight": "bolder",
                                "text": subject,
                            },
                            {
                                "type": "TextBlock",
                                "text": body,
                                "wrap": True,
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": k, "value": v} for k, v in metadata.items()
                                ],
                            },
                        ],
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.4",
                    },
                }
            ],
        }
        logger.info(f"[Teams Notification] Card payload: {card}")

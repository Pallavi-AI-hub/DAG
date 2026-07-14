"""Structured logging utilities with correlation-ID support."""

from __future__ import annotations

import contextvars
import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from autorca_platform.core.config import PlatformConfig

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "autorca_correlation_id",
    default=None,
)


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the correlation ID for the current execution context.

    Args:
        correlation_id: Identifier propagated across related workflow operations.
    """

    _correlation_id.set(correlation_id)


def get_correlation_id() -> str | None:
    """Return the current execution-context correlation ID."""

    return _correlation_id.get()


class CorrelationIdFilter(logging.Filter):
    """Attach correlation ID context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Mutate the log record with current correlation context.

        Args:
            record: Logging record being emitted.

        Returns:
            Always true so the record continues through the handler chain.
        """

        record.correlation_id = get_correlation_id()
        return True


class JsonFormatter(logging.Formatter):
    """Format log records as newline-delimited JSON."""

    def __init__(self, *, service_name: str, environment: str) -> None:
        """Create a JSON formatter.

        Args:
            service_name: Stable service name emitted on every record.
            environment: Deployment environment emitted on every record.
        """

        super().__init__()
        self._service_name = service_name
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: Logging record to format.

        Returns:
            Serialized JSON log line.
        """

        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self._service_name,
            "environment": self._environment,
            "correlation_id": getattr(record, "correlation_id", None),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra = getattr(record, "autorca_extra", None)
        if isinstance(extra, Mapping):
            payload["extra"] = dict(extra)

        return json.dumps(payload, sort_keys=True)


def configure_logging(config: PlatformConfig) -> None:
    """Configure root logging according to platform settings.

    Args:
        config: Runtime platform configuration.
    """

    handler = logging.StreamHandler()
    handler.addFilter(CorrelationIdFilter())

    if config.log_format == "json":
        handler.setFormatter(
            JsonFormatter(service_name=config.service_name, environment=config.environment)
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s "
                "[correlation_id=%(correlation_id)s] %(message)s"
            )
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(config.log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger scoped to a module or component name.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """

    return logging.getLogger(name)

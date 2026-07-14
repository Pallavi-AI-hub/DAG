"""Environment-backed configuration for the AI AutoRCA platform."""

from dataclasses import dataclass
from os import getenv
from typing import Literal

from autorca_platform.core.exceptions import ConfigurationError

EnvironmentName = Literal["local", "dev", "staging", "prod", "test"]
LogFormat = Literal["console", "json"]

_VALID_ENVIRONMENTS: set[str] = {"local", "dev", "staging", "prod", "test"}
_VALID_LOG_FORMATS: set[str] = {"console", "json"}
_VALID_LOG_LEVELS: set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class PlatformConfig:
    """Runtime configuration shared by platform components.

    Attributes:
        environment: Deployment environment name.
        log_level: Python logging level name.
        log_format: Log output format.
        service_name: Stable service name for log records.
    """

    environment: EnvironmentName
    log_level: str
    log_format: LogFormat
    service_name: str = "ai-autorca-platform"

    @classmethod
    def from_env(cls) -> "PlatformConfig":
        """Build platform configuration from environment variables.

        Returns:
            Parsed and validated platform configuration.

        Raises:
            ConfigurationError: If an environment variable contains an unsupported value.
        """

        environment = getenv("AUTORCA_ENVIRONMENT", "local").lower()
        log_level = getenv("AUTORCA_LOG_LEVEL", "INFO").upper()
        default_log_format = "console" if environment == "local" else "json"
        log_format = getenv("AUTORCA_LOG_FORMAT", default_log_format).lower()
        service_name = getenv("AUTORCA_SERVICE_NAME", "ai-autorca-platform")

        if environment not in _VALID_ENVIRONMENTS:
            raise ConfigurationError(
                f"Unsupported AUTORCA_ENVIRONMENT '{environment}'. "
                f"Expected one of: {sorted(_VALID_ENVIRONMENTS)}."
            )
        if log_level not in _VALID_LOG_LEVELS:
            raise ConfigurationError(
                f"Unsupported AUTORCA_LOG_LEVEL '{log_level}'. "
                f"Expected one of: {sorted(_VALID_LOG_LEVELS)}."
            )
        if log_format not in _VALID_LOG_FORMATS:
            raise ConfigurationError(
                f"Unsupported AUTORCA_LOG_FORMAT '{log_format}'. "
                f"Expected one of: {sorted(_VALID_LOG_FORMATS)}."
            )

        return cls(
            environment=environment,  # type: ignore[arg-type]
            log_level=log_level,
            log_format=log_format,  # type: ignore[arg-type]
            service_name=service_name,
        )

"""Domain exception hierarchy for the AI AutoRCA platform."""


class AutoRCABaseException(Exception):
    """Base class for all platform-owned exceptions."""


class ConfigurationError(AutoRCABaseException):
    """Raised when platform configuration is missing or invalid."""


class PluginRegistrationError(AutoRCABaseException):
    """Raised when plugin registration fails."""


class PluginLookupError(AutoRCABaseException):
    """Raised when a requested plugin is not registered."""


class MetadataValidationError(AutoRCABaseException):
    """Raised when metadata validation fails in later phases."""

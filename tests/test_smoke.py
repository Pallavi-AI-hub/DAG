"""Smoke tests for the Phase 1 platform scaffold."""

import importlib
import logging

import pytest

from autorca_platform.composition.container import build_container
from autorca_platform.core.config import PlatformConfig
from autorca_platform.core.exceptions import PluginRegistrationError
from autorca_platform.core.registry import PluginRegistry
from autorca_platform.plugins.examples.noop_plugin import NoopValidator


def test_package_imports_cleanly() -> None:
    """The package should import without side effects beyond plugin registration."""

    module = importlib.import_module("autorca_platform")

    assert module.__version__ == "0.1.0"


def test_plugin_registry_registers_and_lists_noop_plugin() -> None:
    """Registry lookup should return the registered example plugin class."""

    registry = PluginRegistry()
    registry.register("validator", "noop", NoopValidator)

    plugin = registry.get("validator", "noop")
    registrations = registry.list("validator")

    assert plugin is NoopValidator
    assert len(registrations) == 1
    assert registrations[0].key.category == "validator"
    assert registrations[0].key.name == "noop"


def test_plugin_registry_rejects_collisions() -> None:
    """Duplicate registrations should fail unless replacement is explicit."""

    registry = PluginRegistry()
    registry.register("validator", "noop", NoopValidator)

    with pytest.raises(PluginRegistrationError, match="already registered"):
        registry.register("validator", "noop", NoopValidator)


def test_container_builds_with_explicit_config_and_registry() -> None:
    """The composition root should assemble config and registry dependencies."""

    registry = PluginRegistry()
    config = PlatformConfig(environment="test", log_level="INFO", log_format="console")

    container = build_container(config=config, registry=registry, configure_loggers=False)

    assert container.config is config
    assert container.registry is registry


def test_logging_can_be_configured_from_container() -> None:
    """Container composition should configure the root logger when requested."""

    registry = PluginRegistry()
    config = PlatformConfig(environment="test", log_level="DEBUG", log_format="console")

    build_container(config=config, registry=registry, configure_loggers=True)

    assert logging.getLogger().level == logging.DEBUG

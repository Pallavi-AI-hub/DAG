"""Tests for the product catalog PLIM-17222 metadata-driven pipeline."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from autorca_platform.factory.dependency_resolver import DependencyResolver
from autorca_platform.factory.task_registry import TaskRegistry
from autorca_platform.metadata.loader import JsonMetadataLoader
from autorca_platform.plugins.operators.product_catalog import ProductCatalogTaskBuilder


REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_PATH = REPO_ROOT / "configs" / "dags" / "product_catalog_update_pipeline.json"
WRAPPER_PATH = REPO_ROOT / "dags" / "product_catalog_update_pipeline.py"
PRODUCT_CATALOG_TASK_TYPES = (
    "initialize_incident",
    "validate_product",
    "prepare_state",
    "writer_a_holds_lock",
    "writer_b_lock_timeout",
    "collect_lock_evidence",
    "publish_incident",
)


def test_product_catalog_metadata_loads_and_carries_plim_17222() -> None:
    """The PLIM-17222 pipeline should load through the existing metadata loader."""

    metadata = JsonMetadataLoader().load_dag_config(METADATA_PATH)

    assert metadata.dag.dag_id == "product_catalog_update_pipeline"
    assert metadata.incident.incident_id == "PLIM-17222"
    assert [task.task_name for task in metadata.tasks] == list(PRODUCT_CATALOG_TASK_TYPES)
    assert metadata.tasks[4].operator_config["simulated_outcome"] == "lock_timeout"


def test_product_catalog_dependencies_are_valid() -> None:
    """The pipeline should keep the requested branch and fan-in dependency shape."""

    metadata = JsonMetadataLoader().load_dag_config(METADATA_PATH)

    DependencyResolver().detect_cycles(metadata.tasks)
    task_by_name = {task.task_name: task for task in metadata.tasks}

    assert task_by_name["prepare_state"].downstream_tasks == (
        "writer_a_holds_lock",
        "writer_b_lock_timeout",
    )
    assert task_by_name["collect_lock_evidence"].upstream_tasks == (
        "writer_a_holds_lock",
        "writer_b_lock_timeout",
    )


def test_product_catalog_task_types_are_registered() -> None:
    """Every reusable product catalog task type should resolve through the registry."""

    registry = TaskRegistry()

    for task_type in PRODUCT_CATALOG_TASK_TYPES:
        assert isinstance(registry.get_builder(task_type), ProductCatalogTaskBuilder)


def test_product_catalog_generated_dag_imports() -> None:
    """The generated wrapper should remain thin and importable."""

    spec = importlib.util.spec_from_file_location("product_catalog_update_pipeline", WRAPPER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    assert module.dag.dag_id == "product_catalog_update_pipeline"

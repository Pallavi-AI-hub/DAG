"""Tests for DependencyResolver cycle detection."""

import pytest

from autorca_platform.factory.dependency_resolver import DependencyCycleError, DependencyResolver
from autorca_platform.metadata.models import SourceRow, TaskRow


def _task(name: str, upstream: tuple[str, ...] = (), downstream: tuple[str, ...] = ()) -> TaskRow:
    return TaskRow(
        source_row=SourceRow(sheet="DAG Structure", row_number=1),
        dag_id="TEST_DAG",
        task_name=name,
        task_type="EmptyOperator",
        upstream_tasks=upstream,
        downstream_tasks=downstream,
        trigger_rule="all_success",
    )


def test_no_cycle_succeeds() -> None:
    """A directed acyclic graph should pass validation."""

    resolver = DependencyResolver()
    tasks = (
        _task("task_a", downstream=("task_b",)),
        _task("task_b", upstream=("task_a",), downstream=("task_c",)),
        _task("task_c", upstream=("task_b",)),
    )
    resolver.detect_cycles(tasks)


def test_simple_cycle_raises_error() -> None:
    """A direct cycle should be detected and raise DependencyCycleError."""

    resolver = DependencyResolver()
    tasks = (_task("task_a", downstream=("task_b",)), _task("task_b", downstream=("task_a",)))
    with pytest.raises(DependencyCycleError) as exc_info:
        resolver.detect_cycles(tasks)
    assert "Circular dependency detected" in str(exc_info.value)
    assert "task_a" in str(exc_info.value)
    assert "task_b" in str(exc_info.value)

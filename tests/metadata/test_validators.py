"""Tests for metadata validation helpers."""

import pytest

from autorca_platform.core.exceptions import MetadataValidationError
from autorca_platform.metadata.models import SourceRow, TaskRow
from autorca_platform.metadata.validators import normalize_task_dependencies


def _task(name: str, upstream: tuple[str, ...] = ()) -> TaskRow:
    """Build a task row for validator tests."""

    return TaskRow(
        source_row=SourceRow(sheet="DAG Structure", row_number=1),
        dag_id="DAG_A",
        task_name=name,
        task_type="PythonOperator",
        upstream_tasks=upstream,
        trigger_rule="all_success",
    )


def test_normalize_task_dependencies_expands_existing_range() -> None:
    """Dependency range notation should expand when all tasks exist."""

    tasks = (
        _task("extract_p1"),
        _task("extract_p2"),
        _task("extract_p3"),
        _task("extract_p4"),
        _task("volume_check", upstream=("extract_p1..p4",)),
    )

    normalized = normalize_task_dependencies(tasks)
    volume_check = next(task for task in normalized if task.task_name == "volume_check")

    assert volume_check.upstream_tasks == ("extract_p1", "extract_p2", "extract_p3", "extract_p4")


def test_normalize_task_dependencies_rejects_missing_range_member() -> None:
    """Dependency range notation should fail if any expanded task is absent."""

    tasks = (
        _task("extract_p1"),
        _task("extract_p2"),
        _task("volume_check", upstream=("extract_p1..p4",)),
    )

    with pytest.raises(MetadataValidationError, match="expands to unknown tasks"):
        normalize_task_dependencies(tasks)

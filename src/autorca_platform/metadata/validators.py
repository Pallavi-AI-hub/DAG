"""Cross-row and cross-sheet validation for compiled metadata."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from autorca_platform.core.exceptions import MetadataValidationError
from autorca_platform.metadata.models import (
    DagInventoryRow,
    ExpectedRcaRow,
    IncidentRow,
    TaskRow,
)

_DEPENDENCY_RANGE_PATTERN = re.compile(r"^(.+?)(\d+)\.\.(?:[A-Za-z_]+)?(\d+)$")


@dataclass(frozen=True)
class ValidationIssue:
    """Single validation issue with source context."""

    sheet: str
    row_number: int
    field: str
    message: str

    def format(self) -> str:
        """Return a compact human-readable issue."""

        return f"{self.sheet} row {self.row_number} field '{self.field}': {self.message}"


@dataclass(frozen=True)
class ValidationReport:
    """Collection of validation issues."""

    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether no validation issues were found."""

        return not self.issues

    def raise_if_invalid(self) -> None:
        """Raise a metadata validation error when issues exist."""

        if self.is_valid:
            return

        formatted = "\n".join(issue.format() for issue in self.issues)
        raise MetadataValidationError(f"Metadata validation failed:\n{formatted}")


def normalize_task_dependencies(tasks: tuple[TaskRow, ...]) -> tuple[TaskRow, ...]:
    """Expand supported dependency shorthand after checking task existence.

    Args:
        tasks: Raw task rows.

    Returns:
        Task rows with dependency lists expanded.

    Raises:
        MetadataValidationError: If shorthand cannot be expanded to real tasks.
    """

    by_dag: dict[str, set[str]] = {}
    for task in tasks:
        by_dag.setdefault(task.dag_id, set()).add(task.task_name)

    normalized: list[TaskRow] = []
    issues: list[ValidationIssue] = []
    for task in tasks:
        valid_task_names = by_dag[task.dag_id]
        upstream = _expand_dependency_list(task, "Upstream Tasks", task.upstream_tasks, valid_task_names)
        downstream = _expand_dependency_list(
            task,
            "Downstream Tasks",
            task.downstream_tasks,
            valid_task_names,
        )
        normalized.append(task.model_copy(update={"upstream_tasks": upstream, "downstream_tasks": downstream}))

    for task in normalized:
        for field_name, dependency_names in (
            ("Upstream Tasks", task.upstream_tasks),
            ("Downstream Tasks", task.downstream_tasks),
        ):
            for dependency_name in dependency_names:
                if dependency_name not in by_dag[task.dag_id]:
                    issues.append(
                        ValidationIssue(
                            sheet=task.source_row.sheet,
                            row_number=task.source_row.row_number,
                            field=field_name,
                            message=(
                                f"references unknown task '{dependency_name}' "
                                f"within DAG '{task.dag_id}'"
                            ),
                        )
                    )

    ValidationReport(tuple(issues)).raise_if_invalid()
    return tuple(normalized)


def validate_workbook_entities(
    dags: tuple[DagInventoryRow, ...],
    tasks: tuple[TaskRow, ...],
    incidents: tuple[IncidentRow, ...],
    expected_rcas: tuple[ExpectedRcaRow, ...],
) -> ValidationReport:
    """Validate cross-sheet referential integrity.

    Args:
        dags: DAG inventory rows.
        tasks: Task structure rows.
        incidents: Incident catalogue rows.
        expected_rcas: Expected RCA rows.

    Returns:
        Validation report containing every discovered issue.
    """

    issues: list[ValidationIssue] = []
    dag_ids = tuple(dag.dag_id for dag in dags)
    incident_ids = tuple(incident.incident_id for incident in incidents)

    issues.extend(_duplicate_issues("DAG Inventory", "DAG ID", dag_ids))
    issues.extend(_duplicate_issues("Incident Catalogue", "Incident ID", incident_ids))

    dag_id_set = set(dag_ids)
    task_dag_ids = {task.dag_id for task in tasks}
    incident_dag_ids = {incident.dag_id for incident in incidents}
    rca_incident_ids = {rca.incident_id for rca in expected_rcas}
    inventory_by_dag = {dag.dag_id: dag for dag in dags}
    incident_by_id = {incident.incident_id: incident for incident in incidents}

    for dag_id in sorted(dag_id_set - task_dag_ids):
        dag = inventory_by_dag[dag_id]
        issues.append(
            ValidationIssue(
                dag.source_row.sheet,
                dag.source_row.row_number,
                "DAG ID",
                "has no task rows in DAG Structure",
            )
        )
    for dag_id in sorted(task_dag_ids - dag_id_set):
        task = next(task for task in tasks if task.dag_id == dag_id)
        issues.append(
            ValidationIssue(
                task.source_row.sheet,
                task.source_row.row_number,
                "DAG ID",
                "does not exist in DAG Inventory",
            )
        )
    for dag_id in sorted(dag_id_set - incident_dag_ids):
        dag = inventory_by_dag[dag_id]
        issues.append(
            ValidationIssue(
                dag.source_row.sheet,
                dag.source_row.row_number,
                "DAG ID",
                "has no incident row in Incident Catalogue",
            )
        )
    for dag_id in sorted(incident_dag_ids - dag_id_set):
        incident = next(incident for incident in incidents if incident.dag_id == dag_id)
        issues.append(
            ValidationIssue(
                incident.source_row.sheet,
                incident.source_row.row_number,
                "DAG ID",
                "does not exist in DAG Inventory",
            )
        )
    for incident_id in sorted(set(incident_ids) - rca_incident_ids):
        incident = incident_by_id[incident_id]
        issues.append(
            ValidationIssue(
                incident.source_row.sheet,
                incident.source_row.row_number,
                "Incident ID",
                "has no expected RCA row",
            )
        )
    for incident_id in sorted(rca_incident_ids - set(incident_ids)):
        rca = next(rca for rca in expected_rcas if rca.incident_id == incident_id)
        issues.append(
            ValidationIssue(
                rca.source_row.sheet,
                rca.source_row.row_number,
                "Incident ID",
                "does not exist in Incident Catalogue",
            )
        )

    for incident in incidents:
        dag = inventory_by_dag.get(incident.dag_id)
        if dag is not None and incident.category != dag.lrj_category:
            issues.append(
                ValidationIssue(
                    incident.source_row.sheet,
                    incident.source_row.row_number,
                    "Category",
                    f"does not match DAG Inventory LRJ Category '{dag.lrj_category}'",
                )
            )

    for rca in expected_rcas:
        incident = incident_by_id.get(rca.incident_id)
        if incident is not None and rca.resolution != incident.resolution:
            issues.append(
                ValidationIssue(
                    rca.source_row.sheet,
                    rca.source_row.row_number,
                    "Resolution",
                    "does not match Incident Catalogue resolution",
                )
            )

    issues.extend(_duplicate_task_issues(tasks))
    return ValidationReport(tuple(issues))


def _duplicate_issues(sheet: str, field: str, values: tuple[str, ...]) -> tuple[ValidationIssue, ...]:
    """Return duplicate-value issues for row-independent checks."""

    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    return tuple(
        ValidationIssue(sheet=sheet, row_number=0, field=field, message=f"duplicate value '{value}'")
        for value in duplicates
    )


def _duplicate_task_issues(tasks: tuple[TaskRow, ...]) -> tuple[ValidationIssue, ...]:
    """Return duplicate task-name issues scoped to each DAG."""

    issues: list[ValidationIssue] = []
    task_keys = Counter((task.dag_id, task.task_name) for task in tasks)
    duplicate_keys = {key for key, count in task_keys.items() if count > 1}
    for task in tasks:
        if (task.dag_id, task.task_name) in duplicate_keys:
            issues.append(
                ValidationIssue(
                    task.source_row.sheet,
                    task.source_row.row_number,
                    "Task Name",
                    f"duplicate task '{task.task_name}' in DAG '{task.dag_id}'",
                )
            )
    return tuple(issues)


def _expand_dependency_list(
    task: TaskRow,
    field: str,
    dependency_names: tuple[str, ...],
    valid_task_names: set[str],
) -> tuple[str, ...]:
    """Expand explicit dependency ranges in a single dependency list."""

    expanded: list[str] = []
    issues: list[ValidationIssue] = []
    for dependency_name in dependency_names:
        range_match = _DEPENDENCY_RANGE_PATTERN.match(dependency_name)
        if range_match is None:
            expanded.append(dependency_name)
            continue

        prefix, start_text, end_text = range_match.groups()
        start = int(start_text)
        end = int(end_text)
        if end < start:
            issues.append(
                ValidationIssue(
                    task.source_row.sheet,
                    task.source_row.row_number,
                    field,
                    f"range '{dependency_name}' has descending bounds",
                )
            )
            continue

        width = len(start_text) if len(start_text) == len(end_text) else 0
        candidates = tuple(f"{prefix}{index:0{width}d}" for index in range(start, end + 1))
        missing = tuple(candidate for candidate in candidates if candidate not in valid_task_names)
        if missing:
            issues.append(
                ValidationIssue(
                    task.source_row.sheet,
                    task.source_row.row_number,
                    field,
                    f"range '{dependency_name}' expands to unknown tasks {missing}",
                )
            )
            continue
        expanded.extend(candidates)

    ValidationReport(tuple(issues)).raise_if_invalid()
    return tuple(expanded)

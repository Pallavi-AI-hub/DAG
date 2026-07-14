"""Compile architecture workbook metadata into normalized JSON configs."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from autorca_platform.core.exceptions import MetadataValidationError
from autorca_platform.metadata.excel_reader import ArchitectureWorkbookReader, SheetTable
from autorca_platform.metadata.models import (
    CompiledMetadataSet,
    DagConfig,
    DagInventoryRow,
    ExpectedRcaRow,
    GlobalConfig,
    IncidentRow,
    MetadataFieldRow,
    SourceRow,
    TaskRow,
    WorkbookSchema,
    config_file_name,
    default_dag_config_dir,
    default_global_config_path,
    json_dump_options,
)
from autorca_platform.metadata.validators import (
    normalize_task_dependencies,
    validate_workbook_entities,
)


class MetadataCompiler:
    """Compile the architecture workbook into validated JSON metadata."""

    def __init__(self, reader: ArchitectureWorkbookReader | None = None) -> None:
        """Create a compiler.

        Args:
            reader: Optional workbook reader override.
        """

        self._reader = reader or ArchitectureWorkbookReader()

    def compile(self, workbook_path: Path) -> CompiledMetadataSet:
        """Compile a workbook into in-memory metadata configs.

        Args:
            workbook_path: Architecture workbook path.

        Returns:
            Compiled metadata set.

        Raises:
            MetadataValidationError: If validation fails.
        """

        tables = self._reader.read(workbook_path)
        try:
            dags = tuple(_map_dag_row(row) for row in tables.dag_inventory.rows)
            tasks = tuple(_map_task_row(row) for row in tables.dag_structure.rows)
            incidents = tuple(_map_incident_row(row) for row in tables.incident_catalogue.rows)
            expected_rcas = tuple(_map_expected_rca_row(row) for row in tables.expected_ai_rca.rows)
            metadata_fields = tuple(_map_metadata_field_row(row) for row in tables.metadata_model.rows)
        except ValidationError as exc:
            raise MetadataValidationError(f"Workbook row validation failed:\n{exc}") from exc

        tasks = normalize_task_dependencies(tasks)
        validate_workbook_entities(dags, tasks, incidents, expected_rcas).raise_if_invalid()

        incident_by_dag = {incident.dag_id: incident for incident in incidents}
        expected_rca_by_incident = {rca.incident_id: rca for rca in expected_rcas}
        tasks_by_dag: dict[str, list[TaskRow]] = {}
        for task in tasks:
            tasks_by_dag.setdefault(task.dag_id, []).append(task)

        dag_configs = tuple(
            DagConfig(
                dag=dag,
                tasks=tuple(tasks_by_dag[dag.dag_id]),
                incident=incident_by_dag[dag.dag_id],
                expected_rca=expected_rca_by_incident[incident_by_dag[dag.dag_id].incident_id],
            )
            for dag in dags
        )

        global_config = GlobalConfig(
            source_workbook=str(workbook_path),
            dag_count=len(dag_configs),
            task_count=len(tasks),
            incident_count=len(incidents),
            expected_rca_count=len(expected_rcas),
            metadata_fields=metadata_fields,
            workbook_schema=WorkbookSchema(sheets=tables.schema()),
            notes=(
                "Compiled from Excel at build time; Airflow DAG parsing must use JSON only.",
                "Dependency ranges such as extract_p1..p4 are expanded only when all tasks exist.",
            ),
        )
        return CompiledMetadataSet(global_config=global_config, dag_configs=dag_configs)

    def compile_to_directory(self, workbook_path: Path, output_dir: Path) -> CompiledMetadataSet:
        """Compile a workbook and write JSON configs to disk.

        Args:
            workbook_path: Architecture workbook path.
            output_dir: Directory for generated config artifacts.

        Returns:
            Compiled metadata set.
        """

        compiled = self.compile(workbook_path)
        dag_config_dir = default_dag_config_dir(output_dir)
        dag_config_dir.mkdir(parents=True, exist_ok=True)
        default_global_config_path(output_dir).write_text(
            compiled.global_config.model_dump_json(**json_dump_options()),
            encoding="utf-8",
        )
        for dag_config in compiled.dag_configs:
            output_path = dag_config_dir / config_file_name(dag_config.dag.dag_id)
            output_path.write_text(
                dag_config.model_dump_json(**json_dump_options()),
                encoding="utf-8",
            )
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": compiled.global_config.schema_version,
                    "dag_count": compiled.global_config.dag_count,
                    "dag_ids": list(compiled.dag_ids()),
                    "global_config": default_global_config_path(output_dir).as_posix(),
                    "dag_config_dir": dag_config_dir.as_posix(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return compiled


def _source_row(row: dict[str, str | int], sheet_name: str) -> SourceRow:
    """Build source row context from a table row."""

    return SourceRow(sheet=sheet_name, row_number=int(row["_row_number"]))


def _split_dependency_list(raw_value: str | int | None) -> tuple[str, ...]:
    """Split dependency cells into task-name tuples."""

    if raw_value is None:
        return ()
    text = str(raw_value).strip()
    if not text or text == "-":
        return ()
    return tuple(part.strip() for part in text.split(",") if part.strip())


def _optional_text(raw_value: str | int | None) -> str | None:
    """Return normalized optional text."""

    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if not text or text == "-":
        return None
    return text


def _required_bool(raw_value: str | int) -> bool:
    """Parse workbook Yes/No values."""

    text = str(raw_value).strip().lower()
    if text == "yes":
        return True
    if text == "no":
        return False
    raise MetadataValidationError(f"Expected Yes/No value in Metadata Model Required column, got {raw_value!r}")


def _map_dag_row(row: dict[str, str | int]) -> DagInventoryRow:
    """Map a workbook row to a DAG inventory model."""

    return DagInventoryRow(
        source_row=_source_row(row, "DAG Inventory"),
        dag_id=str(row["DAG ID"]),
        dag_name=str(row["DAG Name"]),
        business_domain=str(row["Business Domain"]),
        lrj_category=str(row["LRJ Category"]),
        schedule=str(row["Schedule"]),
        sla=str(row["SLA"]),
        priority=str(row["Priority"]),
        criticality=str(row["Criticality"]),
        source=str(row["Source"]),
        destination=str(row["Destination"]),
    )


def _map_task_row(row: dict[str, str | int]) -> TaskRow:
    """Map a workbook row to a task model."""

    return TaskRow(
        source_row=_source_row(row, "DAG Structure"),
        dag_id=str(row["DAG ID"]),
        task_name=str(row["Task Name"]),
        task_type=str(row["Task Type"]),
        upstream_tasks=_split_dependency_list(row["Upstream Tasks"]),
        downstream_tasks=_split_dependency_list(row["Downstream Tasks"]),
        parallel_group=_optional_text(row["Parallel Group"]),
        trigger_rule=str(row["Trigger Rule"]),
        dependencies=_optional_text(row["Dependencies"]),
    )


def _map_incident_row(row: dict[str, str | int]) -> IncidentRow:
    """Map a workbook row to an incident model."""

    return IncidentRow(
        source_row=_source_row(row, "Incident Catalogue"),
        incident_id=str(row["Incident ID"]),
        dag_id=str(row["DAG ID"]),
        incident_name=str(row["Incident Name"]),
        category=str(row["Category"]),
        severity=str(row["Severity"]),
        description=str(row["Description"]),
        symptoms=str(row["Symptoms"]),
        root_cause=str(row["Root Cause"]),
        business_impact=str(row["Business Impact"]),
        resolution=str(row["Resolution"]),
    )


def _map_expected_rca_row(row: dict[str, str | int]) -> ExpectedRcaRow:
    """Map a workbook row to an expected RCA model."""

    return ExpectedRcaRow(
        source_row=_source_row(row, "Expected AI RCA"),
        incident_id=str(row["Incident ID"]),
        expected_rca_summary=str(row["Expected RCA Summary"]),
        evidence_required=str(row["Evidence Required"]),
        airflow_logs=str(row["Airflow Logs"]),
        datadog_metrics=str(row["Datadog Metrics"]),
        confidence_score=float(str(row["Confidence Score"])),
        resolution=str(row["Resolution"]),
        preventive_action=str(row["Preventive Action"]),
    )


def _map_metadata_field_row(row: dict[str, str | int]) -> MetadataFieldRow:
    """Map a workbook row to a metadata dictionary model."""

    return MetadataFieldRow(
        source_row=_source_row(row, "Metadata Model"),
        section=str(row["Section"]),
        field_name=str(row["Field Name"]),
        data_type=str(row["Data Type"]),
        required=_required_bool(row["Required"]),
        description=str(row["Description"]),
        example_value=_optional_text(row["Example Value"]),
    )

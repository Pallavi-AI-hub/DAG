"""Pydantic models for compiled AI AutoRCA metadata."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from autorca_platform.metadata.schema_version import COMPILED_METADATA_SCHEMA_VERSION


class StrictModel(BaseModel):
    """Base model that rejects unexpected fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceRow(StrictModel):
    """Workbook source location for audit-friendly validation errors."""

    sheet: str
    row_number: int = Field(ge=1)


class DagInventoryRow(StrictModel):
    """DAG-level inventory row from the workbook."""

    source_row: SourceRow
    dag_id: str
    dag_name: str
    business_domain: str
    lrj_category: str
    schedule: str
    sla: str
    priority: str
    criticality: str
    source: str
    destination: str

    @field_validator("dag_id", "dag_name", "business_domain", "lrj_category", mode="before")
    @classmethod
    def _require_text(cls, value: object) -> str:
        """Validate required text fields are populated."""

        text = str(value).strip()
        if not text:
            raise ValueError("field must be non-empty")
        return text


class TaskRow(StrictModel):
    """Task-level orchestration graph row from the workbook."""

    source_row: SourceRow
    dag_id: str
    task_name: str
    task_type: str
    upstream_tasks: tuple[str, ...] = ()
    downstream_tasks: tuple[str, ...] = ()
    parallel_group: str | None = None
    trigger_rule: str
    dependencies: str | None = None

    @field_validator("dag_id", "task_name", "task_type", "trigger_rule", mode="before")
    @classmethod
    def _require_text(cls, value: object) -> str:
        """Validate required text fields are populated."""

        text = str(value).strip()
        if not text:
            raise ValueError("field must be non-empty")
        return text


class IncidentRow(StrictModel):
    """Incident catalogue row mapped to a DAG."""

    source_row: SourceRow
    incident_id: str
    dag_id: str
    incident_name: str
    category: str
    severity: str
    description: str
    symptoms: str
    root_cause: str
    business_impact: str
    resolution: str


class ExpectedRcaRow(StrictModel):
    """Expected AI RCA ground-truth row mapped to an incident."""

    source_row: SourceRow
    incident_id: str
    expected_rca_summary: str
    evidence_required: str
    airflow_logs: str
    datadog_metrics: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    resolution: str
    preventive_action: str


class MetadataFieldRow(StrictModel):
    """Metadata model dictionary row from the workbook."""

    source_row: SourceRow
    section: str
    field_name: str
    data_type: str
    required: bool
    description: str
    example_value: str | None = None


class DagConfig(StrictModel):
    """Compiled metadata for one generated Airflow DAG."""

    schema_version: str = COMPILED_METADATA_SCHEMA_VERSION
    dag: DagInventoryRow
    tasks: tuple[TaskRow, ...]
    incident: IncidentRow
    expected_rca: ExpectedRcaRow

    @model_validator(mode="after")
    def _validate_task_ownership(self) -> "DagConfig":
        """Ensure every task belongs to the config's DAG."""

        bad_tasks = [task.task_name for task in self.tasks if task.dag_id != self.dag.dag_id]
        if bad_tasks:
            raise ValueError(f"Tasks do not belong to DAG {self.dag.dag_id}: {bad_tasks}")
        if self.incident.dag_id != self.dag.dag_id:
            raise ValueError(
                f"Incident {self.incident.incident_id} does not belong to DAG {self.dag.dag_id}"
            )
        return self


class WorkbookSchema(StrictModel):
    """Discovered workbook schema summary."""

    sheets: dict[str, tuple[str, ...]]


class GlobalConfig(StrictModel):
    """Compiled global metadata shared by all DAG configs."""

    schema_version: str = COMPILED_METADATA_SCHEMA_VERSION
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_workbook: str
    dag_count: int
    task_count: int
    incident_count: int
    expected_rca_count: int
    metadata_fields: tuple[MetadataFieldRow, ...]
    workbook_schema: WorkbookSchema
    notes: tuple[str, ...] = ()


class CompiledMetadataSet(StrictModel):
    """In-memory result of compiling the workbook."""

    global_config: GlobalConfig
    dag_configs: tuple[DagConfig, ...]

    def dag_ids(self) -> tuple[str, ...]:
        """Return DAG IDs in compiled order."""

        return tuple(config.dag.dag_id for config in self.dag_configs)


def json_dump_options() -> dict[str, object]:
    """Return consistent options for writing Pydantic JSON payloads."""

    return {"indent": 2, "exclude_none": True}


def config_file_name(dag_id: str) -> str:
    """Return the JSON file name for a compiled DAG config.

    Args:
        dag_id: DAG identifier.

    Returns:
        Lowercase JSON file name.
    """

    return f"{dag_id.lower()}.json"


def default_global_config_path(output_dir: Path) -> Path:
    """Return the standard global config output path."""

    return output_dir / "global_config.json"


def default_dag_config_dir(output_dir: Path) -> Path:
    """Return the standard DAG config output directory."""

    return output_dir / "dags"

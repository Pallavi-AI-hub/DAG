"""Airflow DAG builder constructing DAG objects from compiled metadata."""

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from autorca_platform.factory.callback_hooks import (
    default_on_failure_callback,
    default_sla_miss_callback,
)
from autorca_platform.factory.dependency_resolver import DependencyResolver
from autorca_platform.factory.pool_retry_config import get_default_args
from autorca_platform.factory.task_group_builder import TaskGroupBuilder
from autorca_platform.factory.task_registry import TaskRegistry
from autorca_platform.metadata.models import DagConfig

logger = logging.getLogger("autorca_platform.factory.dag_builder")


class AirflowDagBuilder:
    """Builder for constructing Airflow DAG objects from validated metadata."""

    def __init__(self, task_registry: TaskRegistry | None = None) -> None:
        """Initialize the DAG builder.

        Args:
            task_registry: Optional custom TaskRegistry instance.
        """

        self.task_registry = task_registry or TaskRegistry()
        self.resolver = DependencyResolver()

    def build(self, metadata: DagConfig) -> Any:
        """Build an Airflow DAG from the compiled metadata.

        Args:
            metadata: The compiled DAG configuration metadata.

        Returns:
            Constructed Airflow DAG object.
        """

        sla_delta = self._parse_sla(metadata.dag.sla)
        default_args = get_default_args(metadata.dag.priority)
        if sla_delta:
            default_args["sla"] = sla_delta

        try:
            from airflow.sdk import DAG
        except ImportError:
            try:
                from airflow import DAG
            except ImportError:

                class DAG:  # type: ignore[no-redef]
                    """Mock DAG if Airflow is not present."""

                    def __init__(self, dag_id: str, **kwargs: Any) -> None:
                        self.dag_id = dag_id
                        self.task_dict: dict[str, Any] = {}
                        for k, v in kwargs.items():
                            setattr(self, k, v)

                    def __enter__(self) -> "DAG":
                        return self

                    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                        pass

        dag = DAG(
            dag_id=metadata.dag.dag_id,
            schedule=metadata.dag.schedule,
            start_date=datetime(2026, 1, 1, tzinfo=UTC),
            catchup=False,
            default_args=default_args,
            doc_md=self._build_doc_md(metadata),
            sla_miss_callback=default_sla_miss_callback,
            on_failure_callback=default_on_failure_callback,
            tags=[
                metadata.dag.business_domain,
                metadata.dag.lrj_category,
                metadata.dag.priority,
            ],
        )

        self.resolver.detect_cycles(metadata.tasks)

        tasks: dict[str, Any] = {}
        with dag:
            tg_builder = TaskGroupBuilder(dag)
            for row in metadata.tasks:
                tg = tg_builder.get_or_create_group(row.parallel_group)

                builder = self.task_registry.get_builder(row.task_type)

                if tg is not None:
                    with tg:
                        task = builder.build(row)
                else:
                    task = builder.build(row)

                tasks[row.task_name] = task

            self.resolver.wire_dependencies(tasks, metadata.tasks)

        return dag

    def _parse_sla(self, sla_str: str) -> timedelta | None:
        """Parse SLA duration string like '2h' or '30m' to timedelta.

        Args:
            sla_str: Raw SLA string.

        Returns:
            Timedelta object or None if invalid or absent.
        """

        if not sla_str:
            return None

        match = re.search(r"(\d+(?:\.\d+)?)\s*(h|m)", sla_str, re.IGNORECASE)
        if not match:
            return None

        val = float(match.group(1))
        unit = match.group(2).lower()
        if unit == "h":
            return timedelta(hours=val)
        return timedelta(minutes=val)

    def _build_doc_md(self, metadata: DagConfig) -> str:
        """Format a rich description of the DAG from catalog metadata.

        Args:
            metadata: DAG config model.

        Returns:
            Markdown documentation block.
        """

        return f"""
# {metadata.dag.dag_name}

- **Business Domain**: {metadata.dag.business_domain}
- **LRJ Category**: {metadata.dag.lrj_category}
- **Priority**: {metadata.dag.priority}
- **Criticality**: {metadata.dag.criticality}
- **Data Path**: `{metadata.dag.source}` &rarr; `{metadata.dag.destination}`

## Registered Incident Info
- **Incident ID**: {metadata.incident.incident_id}
- **Name**: {metadata.incident.incident_name}
- **Description**: {metadata.incident.description}
- **Symptoms**: {metadata.incident.symptoms}
- **Root Cause**: {metadata.incident.root_cause}
- **Resolution**: {metadata.incident.resolution}
"""

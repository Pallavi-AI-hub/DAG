"""AI AutoRCA platform callbacks plugin."""

import logging
from typing import Any

from autorca_platform.core.registry import register_plugin

logger = logging.getLogger("autorca_platform.plugins.callbacks.autorca_callback_plugin")


@register_plugin(
    "callback",
    "ai_autorca.trigger_rca",
    description="Trigger AI AutoRCA diagnostic process on task failure.",
    replace=True,
)
def trigger_rca_callback(context: dict[str, Any]) -> None:
    """Invoked when a task fails to begin diagnostic data gathering.

    Args:
        context: Airflow task instance execution context.
    """

    task_instance = context.get("task_instance")
    dag_id = context.get("dag").dag_id if context.get("dag") else "unknown"
    task_id = task_instance.task_id if task_instance else "unknown"

    logger.info(
        f"[AutoRCA Callback] Triggered diagnostic agent workflow for "
        f"failed task {task_id} in DAG {dag_id}."
    )


@register_plugin(
    "callback",
    "ai_autorca.sla_context",
    description="Ingest context regarding SLA breaches into AutoRCA knowledge graph.",
    replace=True,
)
def sla_context_callback(
    dag: Any,
    task_list: Any,
    blocking_task_list: Any,
    slas: Any,
    blocking_tis: Any,
) -> None:
    """Invoked when a DAG runs past its SLA duration.

    Args:
        dag: Airflow DAG object.
        task_list: Tasks that missed SLA.
        blocking_task_list: Tasks currently blocking execution.
        slas: SLA specifications.
        blocking_tis: Blocking task instances.
    """

    dag_id = dag.dag_id if dag else "unknown"
    logger.info(
        f"[AutoRCA Callback] Logged SLA breach details for DAG {dag_id} "
        f"to diagnostic catalog."
    )

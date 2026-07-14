"""Callback hooks for Airflow task failures and SLA breaches."""

import logging
from typing import Any

from autorca_platform.core.exceptions import PluginLookupError
from autorca_platform.core.registry import get_default_registry
from autorca_platform.interfaces.notification_sink import NotificationSink
from autorca_platform.interfaces.observability_sink import ObservabilitySink

logger = logging.getLogger("autorca_platform.factory.callback_hooks")


def default_on_failure_callback(context: dict[str, Any]) -> None:
    """Fires when a task fails. Emits metrics and sends notifications if configured.

    Args:
        context: Airflow task instance execution context dictionary.
    """

    task_instance = context.get("task_instance")
    dag_id = context.get("dag").dag_id if context.get("dag") else "unknown"
    task_id = task_instance.task_id if task_instance else "unknown"
    exception = context.get("exception")

    logger.error(f"Task {task_id} in DAG {dag_id} failed: {exception}")

    registry = get_default_registry()

    try:
        datadog = registry.get("observability", "datadog", expected_type=ObservabilitySink)
        datadog.emit_metric(
            name="airflow.task.failure",
            value=1.0,
            tags={"dag_id": dag_id, "task_id": task_id},
        )
        datadog.emit_event(
            name="Task Failure",
            attributes={
                "dag_id": dag_id,
                "task_id": task_id,
                "error": str(exception),
            },
        )
    except PluginLookupError:
        logger.warning("Datadog observability sink is not registered.")

    try:
        teams = registry.get("notification", "teams", expected_type=NotificationSink)
        teams.notify(
            subject=f"Failure in DAG {dag_id} (Task: {task_id})",
            body=f"Task {task_id} failed with error: {exception}",
            metadata={"dag_id": dag_id, "task_id": task_id, "severity": "error"},
        )
    except PluginLookupError:
        logger.warning("Teams notification sink is not registered.")

    try:
        autorca_cb = registry.get("callback", "ai_autorca.trigger_rca")
        if callable(autorca_cb):
            autorca_cb(context)
    except PluginLookupError:
        pass


def default_sla_miss_callback(
    dag: Any,
    task_list: Any,
    blocking_task_list: Any,
    slas: Any,
    blocking_tis: Any,
) -> None:
    """Fires on SLA miss. Emits metrics and sends notifications if configured.

    Args:
        dag: Airflow DAG object.
        task_list: List of tasks that missed SLA.
        blocking_task_list: List of tasks blocking execution.
        slas: SLA specifications.
        blocking_tis: Blocking task instances.
    """

    dag_id = dag.dag_id if dag else "unknown"
    logger.warning(f"SLA missed for DAG {dag_id}. Tasks: {task_list}")

    registry = get_default_registry()

    try:
        datadog = registry.get("observability", "datadog", expected_type=ObservabilitySink)
        datadog.emit_metric(
            name="airflow.dag.sla_miss",
            value=1.0,
            tags={"dag_id": dag_id},
        )
    except PluginLookupError:
        pass

    try:
        teams = registry.get("notification", "teams", expected_type=NotificationSink)
        teams.notify(
            subject=f"SLA Breach in DAG {dag_id}",
            body=f"DAG {dag_id} missed its SLA.",
            metadata={"dag_id": dag_id, "severity": "warning"},
        )
    except PluginLookupError:
        pass

    try:
        autorca_cb = registry.get("callback", "ai_autorca.sla_context")
        if callable(autorca_cb):
            autorca_cb(dag, task_list, blocking_task_list, slas, blocking_tis)
    except PluginLookupError:
        pass

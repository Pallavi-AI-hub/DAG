"""Sensor builder helper for Airflow sensor constructs."""

from typing import Any


def resolve_sensor_params(task_name: str, dependencies_desc: str | None) -> dict[str, Any]:
    """Resolve required parameters for ExternalTaskSensor.

    Args:
        task_name: Sensor task name.
        dependencies_desc: Optional description from metadata.

    Returns:
        Dict of parameters including external_dag_id and external_task_id.
    """

    external_dag_id = f"external_{task_name}"

    return {
        "external_dag_id": external_dag_id,
        "external_task_id": "end",
        "mode": "reschedule",
        "check_existence": False,
    }

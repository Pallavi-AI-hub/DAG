"""Pool and retry configuration helper for the Airflow builder subsystem."""

from datetime import timedelta
from typing import Any

from autorca_platform.metadata.models import TaskRow


def get_default_args(priority: str) -> dict[str, Any]:
    """Build Airflow default_args with production-grade retries.

    Args:
        priority: Business priority (e.g., P1, P2, P3).

    Returns:
        Dict of default args for Airflow DAG initialization.
    """

    # Higher priority DAGs can have more aggressive retry profiles
    retries = 3
    retry_delay = timedelta(minutes=5)

    if priority.upper() == "P1":
        retries = 4
        retry_delay = timedelta(minutes=2)

    return {
        "owner": "ai-autorca-platform",
        "depends_on_past": False,
        "retries": retries,
        "retry_delay": retry_delay,
    }


def apply_pool_and_trigger_rule(operator_kwargs: dict[str, Any], task_row: TaskRow) -> None:
    """Apply pool and trigger rule options to operator kwargs from metadata.

    Args:
        operator_kwargs: Keyword arguments dict to pass to the operator.
        task_row: Task metadata configuration.
    """

    if task_row.parallel_group:
        operator_kwargs["pool"] = task_row.parallel_group

    if task_row.trigger_rule:
        operator_kwargs["trigger_rule"] = task_row.trigger_rule

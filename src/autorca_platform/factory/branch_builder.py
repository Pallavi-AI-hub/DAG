"""Branch builder helper for the Airflow construction engine."""

from collections.abc import Callable
from typing import Any


def get_dummy_branch_callable(downstream_task_ids: list[str]) -> Callable[..., Any]:
    """Return a python callable that chooses the first downstream task or None.

    Args:
        downstream_task_ids: List of candidate task IDs to branch to.

    Returns:
        Callable that returns one of the downstream task IDs.
    """

    def dummy_branch(**kwargs: Any) -> Any:
        if downstream_task_ids:
            return downstream_task_ids[0]
        return None

    return dummy_branch

"""Dynamic task mapping support for Airflow builder subsystem."""

from typing import Any


def is_mapped_task(task_type: str) -> bool:
    """Check if task type indicates dynamic mapping.

    Args:
        task_type: Task type configuration string.

    Returns:
        True if the task type requires dynamic mapping expansion.
    """

    task_type_lower = task_type.lower()
    return "expand" in task_type_lower or "dynamic task mapping" in task_type_lower


def build_mapped_task(
    operator_class: type,
    task_name: str,
    dag: Any,
    trigger_rule: str,
    pool: str | None,
    **kwargs: Any,
) -> Any:
    """Construct a dynamically mapped task instance in Airflow.

    Args:
        operator_class: Concrete Airflow operator class (e.g. PythonOperator).
        task_name: Unique task identifier.
        dag: Target Airflow DAG.
        trigger_rule: Airflow trigger rule.
        pool: Airflow pool name.
        **kwargs: Keyword arguments for the task.

    Returns:
        Mapped operator object.
    """

    partial_kwargs = {
        "task_id": task_name,
        "dag": dag,
        "trigger_rule": trigger_rule,
    }
    if pool:
        partial_kwargs["pool"] = pool

    partial_kwargs.update(kwargs)

    operator_name = operator_class.__name__
    if "PythonOperator" in operator_name or "BranchPythonOperator" in operator_name:
        # PythonOperator expansions typically map op_args or op_kwargs
        return operator_class.partial(**partial_kwargs).expand(op_args=[[1], [2], [3]])
    else:
        # Fallback to general expansion parameter
        return operator_class.partial(**partial_kwargs).expand(dummy_param=[1, 2, 3])

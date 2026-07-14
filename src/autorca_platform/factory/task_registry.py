"""Task registry for mapping metadata task types to concrete builders."""

from typing import Any

from autorca_platform.core.exceptions import PluginLookupError
from autorca_platform.core.registry import get_default_registry
from autorca_platform.interfaces.task_builder import TaskBuilder
from autorca_platform.metadata.models import TaskRow


class TaskRegistry:
    """Registry resolving task types to concrete operator builders."""

    def __init__(self, registry: Any = None) -> None:
        """Initialize the task registry.

        Args:
            registry: Optional custom PluginRegistry instance.
        """

        # Importing the operators package registers the built-in task builders.
        import autorca_platform.plugins.operators  # noqa: F401

        self._registry = registry or get_default_registry()

    def get_builder(self, task_type: str) -> TaskBuilder[TaskRow, Any]:
        """Lookup task builder plugin. If missing, fall back to base builders.

        Args:
            task_type: Task type string from metadata.

        Returns:
            Registered TaskBuilder.

        Raises:
            PluginLookupError: If no builder can be resolved.
        """

        try:
            return self._registry.get("task_builder", task_type, expected_type=TaskBuilder)
        except PluginLookupError:
            normalized = self._normalize_task_type(task_type)
            try:
                return self._registry.get("task_builder", normalized, expected_type=TaskBuilder)
            except PluginLookupError as exc:
                raise PluginLookupError(
                    f"Unknown task type '{task_type}' (nor its normalized form '{normalized}')"
                ) from exc

    def _normalize_task_type(self, task_type: str) -> str:
        """Normalize complex/parameterized task type string to base builder name.

        Args:
            task_type: Raw task type string.

        Returns:
            Normalized base task type string.
        """

        task_type_lower = task_type.lower()
        if "emptyoperator" in task_type_lower:
            return "EmptyOperator"
        elif "branchpythonoperator" in task_type_lower:
            return "BranchPythonOperator"
        elif "externaltasksensor" in task_type_lower:
            return "ExternalTaskSensor"
        elif "sensor" in task_type_lower:
            return "Sensor"
        elif "pythonoperator.expand" in task_type_lower or "expand" in task_type_lower:
            return "PythonOperator.expand"
        elif "pythonoperator" in task_type_lower:
            return "PythonOperator"
        elif (
            "snowflakeoperator" in task_type_lower
            or "postgresoperator" in task_type_lower
            or "sqlexecutequeryoperator" in task_type_lower
            or "sqloperator" in task_type_lower
        ):
            return "SnowflakeOperator"
        return task_type

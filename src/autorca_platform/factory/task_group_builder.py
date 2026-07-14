"""TaskGroup construction helper for the Airflow builder subsystem."""

from typing import Any


class TaskGroupBuilder:
    """Build and manage Airflow TaskGroups based on metadata config."""

    def __init__(self, dag: Any) -> None:
        """Initialize the task group builder.

        Args:
            dag: The Airflow DAG object.
        """

        self.dag = dag
        self.groups: dict[str, Any] = {}

    def get_or_create_group(self, group_name: str | None) -> Any:
        """Retrieve an existing TaskGroup or build one if non-existent.

        Args:
            group_name: Name of the task group. If None or empty, returns None.

        Returns:
            Airflow TaskGroup instance or None.
        """

        if not group_name or not group_name.strip():
            return None

        clean_name = group_name.strip()
        if clean_name not in self.groups:
            try:
                from airflow.utils.task_group import TaskGroup

                self.groups[clean_name] = TaskGroup(group_id=clean_name, dag=self.dag)
            except ImportError:

                class MockTaskGroup:
                    """Mock class for TaskGroup if Airflow is not installed."""

                    def __init__(self, group_id: str, dag: Any) -> None:
                        self.group_id = group_id
                        self.dag = dag

                    def __enter__(self) -> "MockTaskGroup":
                        return self

                    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                        pass

                self.groups[clean_name] = MockTaskGroup(clean_name, self.dag)

        return self.groups[clean_name]

"""Task builder interface reserved for task construction plugins."""

from typing import Protocol, TypeVar, runtime_checkable

TaskMetadataT = TypeVar("TaskMetadataT")
TaskT = TypeVar("TaskT")


@runtime_checkable
class TaskBuilder(Protocol[TaskMetadataT, TaskT]):
    """Contract for constructing task objects from task metadata."""

    def build(self, metadata: TaskMetadataT) -> TaskT:
        """Build a task object from validated task metadata.

        Args:
            metadata: Validated task metadata.

        Returns:
            Framework-specific task object.
        """

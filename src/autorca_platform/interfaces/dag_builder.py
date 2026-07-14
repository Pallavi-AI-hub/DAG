"""DAG builder interface reserved for Airflow construction phases."""

from typing import Protocol, TypeVar

MetadataT = TypeVar("MetadataT")
DagT = TypeVar("DagT")


class DagBuilder(Protocol[MetadataT, DagT]):
    """Contract for constructing DAG objects from metadata."""

    def build(self, metadata: MetadataT) -> DagT:
        """Build a DAG object from validated metadata.

        Args:
            metadata: Validated DAG metadata.

        Returns:
            Framework-specific DAG object.
        """

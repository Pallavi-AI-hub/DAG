"""Metadata loading interface used by later platform phases."""

from pathlib import Path
from typing import Protocol, TypeVar

MetadataT = TypeVar("MetadataT")


class MetadataLoader(Protocol[MetadataT]):
    """Contract for loading compiled metadata artifacts."""

    def load(self, path: Path) -> MetadataT:
        """Load metadata from a compiled artifact path.

        Args:
            path: Path to a compiled metadata artifact.

        Returns:
            Parsed metadata object.
        """

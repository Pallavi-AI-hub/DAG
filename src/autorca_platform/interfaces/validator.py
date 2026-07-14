"""Validation interface for metadata and platform checks."""

from typing import Protocol, TypeVar

SubjectT = TypeVar("SubjectT")


class Validator(Protocol[SubjectT]):
    """Contract for validating a subject and raising clear domain errors."""

    def validate(self, subject: SubjectT) -> None:
        """Validate the supplied subject.

        Args:
            subject: Entity to validate.

        Raises:
            AutoRCABaseException: Implementations raise domain-specific validation errors.
        """

# Contributing

## Engineering Standards

- Use Python 3.11 or newer.
- Keep public functions and classes typed and documented with Google-style docstrings.
- Use `typing.Protocol` for platform extension contracts.
- Keep business logic out of `core/`; later behavior must attach through interfaces and
  plugin registration.
- Use structured logging instead of `print`.
- Catch named exceptions only, and re-raise domain exceptions where appropriate.
- Keep functions small and focused. Split complex logic before it becomes hard to review.

## Branches and Commits

- Use short-lived feature branches.
- Prefer small, reviewable commits.
- Use imperative commit subjects, for example: `Add plugin registry collision checks`.

## Pull Requests

Every PR should include:

- A concise summary of behavior changed.
- Tests for new behavior or a clear reason tests are not applicable.
- Confirmation that `pytest`, `ruff`, `black --check`, and `mypy` pass locally.
- Notes for follow-up work when a phase boundary intentionally defers implementation.

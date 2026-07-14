# AI AutoRCA Platform Architecture

## Phase 1: Platform Scaffold

Phase 1 creates the framework-agnostic foundation for AI AutoRCA. The package is split
into stable layers:

- `core/` contains platform primitives: exceptions, logging, configuration, and plugin
  registry.
- `interfaces/` defines extension contracts using `typing.Protocol`.
- `plugins/examples/` demonstrates registration without introducing business logic.
- `composition/` provides the composition root that assembles runtime dependencies.

The core rule is that later behavior should be added by implementing interfaces and
registering plugins, not by editing foundational modules. This keeps metadata loading,
DAG construction, notifications, observability, and validation independently replaceable.

```text
environment
    |
    v
core.config -----> composition.container
    |                       |
    v                       v
core.logging          core.registry
                            |
                            v
                   registered plugin instances
```

Phase 1 intentionally excludes Airflow objects, Excel parsing, metadata compilation,
external service clients, and production DAG definitions.

## Phase 2: Metadata Layer

Phase 2 introduces a build-time metadata compiler. The compiler reads the architecture
workbook, maps rows into strict Pydantic models, validates cross-sheet references, and
writes normalized JSON artifacts.

```text
Architecture workbook (.xlsx)
    |
    v
metadata.excel_reader
    |
    v
metadata.models + metadata.validators
    |
    v
configs/global_config.json
configs/manifest.json
configs/dags/<dag_id>.json
```

The compiler validates:

- DAG IDs are unique and every DAG has tasks.
- Every task belongs to an inventory DAG.
- Every incident maps to a known DAG.
- Every expected RCA row maps to a known incident.
- Incident category and RCA resolution remain consistent across sheets.
- Task dependencies reference existing tasks in the same DAG.

The workbook uses a compact dependency notation such as `extract_p1..p4`. The compiler
expands that notation only when every expanded task exists. The generated JSON never
contains shorthand dependencies.

Airflow-facing code must load compiled JSON, not the workbook.

## Phase 3: Dynamic DAG Factory

To be completed in Phase 3.

## Phase 4: DAG Generation and Integrations

To be completed in Phase 4.

## Phase 5: Testing, Deployment, and Operations

To be completed in Phase 5.

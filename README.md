# AI AutoRCA Platform

AI AutoRCA is a metadata-driven Apache Airflow platform for long-running-job monitoring,
incident evidence collection, and root-cause-analysis workflows.

This repository currently contains Phase 1 of the platform: a framework-agnostic Python
scaffold with plugin registration, dependency composition, configuration, structured
logging, interface contracts, and smoke-test coverage. Later phases add metadata
compilation, dynamic DAG construction, generated production DAG wrappers, integrations,
deployment, and operations documentation.

## Five-Phase Build Plan

1. Project scaffold, plugin architecture, and engineering standards.
2. Excel metadata ingestion, schema modeling, validation, and compiled config output.
3. Dynamic DAG factory and Airflow builder subsystem.
4. Production DAG generation and integration plugins.
5. Testing, CI/CD, deployment, and complete operations documentation.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check .
black --check .
mypy src tests
```

Development tools are declared as optional dependencies.

## Compile Metadata

Phase 2 compiles the architecture workbook into JSON so Airflow never reads Excel during
DAG parsing.

```powershell
$env:PYTHONPATH = "src"
python -m autorca_platform.cli.compile_metadata compile `
  --input "C:\Users\mpallavi\Downloads\AI_AutoRCA_Platform_Architecture.xlsx" `
  --output configs
```

After editable installation, the console script is also available:

```powershell
autorca-metadata compile --input "C:\path\to\spec.xlsx" --output configs
```

The compiler writes:

- `configs/global_config.json`
- `configs/manifest.json`
- `configs/dags/<dag_id>.json`, one file per DAG

## Phase 1 Decisions

- Interfaces use `typing.Protocol` consistently.
- The plugin registry is single-active-version by design for Phase 1.
- Logging supports JSON and console formats, with environment-controlled log level and
  correlation IDs.
- No Airflow, Excel, Datadog, Teams, Kafka, MinIO, Snowflake, dbt, FastAPI, or Kubernetes
  implementation code is included in Phase 1.

## Phase 2 Decisions

- Compiled metadata uses JSON for strict parsing and fast Airflow startup.
- Excel parsing is build-time only.
- Dependency shorthand such as `extract_p1..p4` is expanded only when every expanded task
  exists in the same DAG.
- Secrets do not belong in compiled config. Store credentials in environment variables,
  Kubernetes Secrets, or the approved secrets backend in later deployment phases.

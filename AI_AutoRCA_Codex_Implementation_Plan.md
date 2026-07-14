# AI AutoRCA Platform — Codex Implementation Plan
### Five Sequential, Self-Contained Engineering Prompts

---

# PROMPT 1 — Project Scaffold and Platform Architecture

## 1. Title
**Phase 1: Foundational Platform Scaffold, Plugin Architecture, and Engineering Standards for the AI AutoRCA Airflow Platform**

## 2. Background
You are acting as a Principal Software Architect building the foundation layer of a production-grade, metadata-driven Apache Airflow platform called **AI AutoRCA**. This platform will eventually orchestrate 56 production DAGs and is explicitly designed to scale to 500+ DAGs without linear growth in code complexity. This is an enterprise system, not a tutorial project — treat every decision as if it will be code-reviewed by a staff engineer and will run in a regulated production environment with on-call rotations, SLAs, and audit requirements.

This is Phase 1 of a 5-phase build. In this phase you are building ONLY the reusable, business-logic-free platform skeleton: the package layout, plugin architecture, dependency injection scaffolding, logging framework, interface contracts, and engineering standards that every later phase will build on top of. No Airflow DAGs, no metadata parsing, no Excel ingestion, and no business logic exist yet. Treat this phase as building the "chassis" before the "engine" is installed.

The downstream stack that this scaffold must be compatible with (but must NOT yet integrate against) includes: Apache Airflow, Kubernetes, Rancher, PostgreSQL, Kafka, MinIO, Snowflake, dbt, Datadog, Microsoft Teams, and FastAPI.

## 3. Objective
Produce a clean, idiomatic, enterprise-grade Python project scaffold that:
- Establishes a plugin-based, dependency-injected architecture that later phases (metadata layer, DAG factory, DAG generation, testing/CI/CD) can extend without modifying core files.
- Defines abstract interfaces/contracts (builders, registries, loaders, validators) that later phases will implement concretely.
- Establishes logging, configuration, and error-handling conventions used platform-wide.
- Establishes coding standards, linting, typing, and documentation conventions that all subsequent phases must follow without exception.

## 4. Scope
**In scope for this phase:**
- Repository/package structure
- Dependency management (pyproject.toml based, not requirements.txt-only)
- Plugin registry architecture (abstract base classes + registration mechanism)
- Dependency injection container or equivalent composition pattern
- Structured logging framework
- Custom exception hierarchy
- Configuration management scaffold (environment-based, not yet wired to real config values)
- Interface definitions (abstract classes / Protocols) for: MetadataLoader, DagBuilder, TaskBuilder, Validator, NotificationSink, ObservabilitySink
- Developer tooling: linting (ruff), formatting (black), type checking (mypy), pre-commit hooks
- Root-level documentation: README, CONTRIBUTING, ARCHITECTURE (skeleton only, to be expanded in later phases)
- Testing scaffold (pytest configuration, no real tests yet beyond a smoke test)

**Explicitly out of scope for this phase:**
- Any Excel/metadata parsing
- Any Airflow DAG objects
- Any concrete DAG Factory logic
- Any Datadog, Teams, Kafka, MinIO, Snowflake, dbt, or FastAPI integration code — only interface stubs referencing where they will plug in later
- Any of the 56 production DAGs

## 5. Inputs
None. This phase has no external inputs (no Excel file, no metadata). If Codex believes it needs an input that has not been provided, it must stop and ask rather than inventing one.

## 6. Outputs
A complete, runnable (via `pip install -e .` and `pytest`) Python package scaffold with:
- Zero business logic
- Fully documented interfaces
- A working plugin registration mechanism demonstrated with at least one trivial no-op plugin (clearly marked as an example, to be deleted or replaced in later phases)
- Passing lint, type-check, and smoke-test CI-equivalent local commands

## 7. Deliverables
1. Full repository directory tree (see Folder Structure below)
2. `pyproject.toml` with pinned/ranged dependencies, project metadata, tool configuration (ruff, black, mypy, pytest) in one file
3. Abstract base classes / `typing.Protocol` definitions for all core extension points
4. A generic, type-safe plugin registry (e.g., decorator-based `@register_plugin("category", "name")`) with lookup, listing, and collision-detection behavior
5. A composition root / DI wiring module that shows how plugins will be assembled at runtime (no real plugins yet, just the mechanism)
6. Structured logging module (JSON-capable, environment-aware log level, correlation-ID support since RCA workflows require traceability across DAG runs)
7. Custom exception hierarchy (e.g., `AutoRCABaseException`, `ConfigurationError`, `PluginRegistrationError`, `MetadataValidationError` — the last one stubbed for Phase 2 to use)
8. `README.md` explaining the platform's purpose, the 5-phase build plan, and how to set up a dev environment
9. `CONTRIBUTING.md` with coding standards, branching, commit conventions, and PR expectations
10. `docs/ARCHITECTURE.md` skeleton with sections reserved for each phase (Phase 1 section fully written, Phases 2–5 marked "To be completed in Phase N")
11. Pre-commit configuration wired to ruff, black, mypy
12. A single smoke test proving the package imports cleanly and the plugin registry works end-to-end with the example plugin

## 8. Folder Structure
```
ai-autorca-platform/
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── .pre-commit-config.yaml
├── docs/
│   └── ARCHITECTURE.md
├── src/
│   └── autorca_platform/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── logging.py
│       │   ├── config.py
│       │   └── registry.py
│       ├── interfaces/
│       │   ├── __init__.py
│       │   ├── metadata_loader.py
│       │   ├── dag_builder.py
│       │   ├── task_builder.py
│       │   ├── validator.py
│       │   ├── notification_sink.py
│       │   └── observability_sink.py
│       ├── plugins/
│       │   ├── __init__.py
│       │   └── examples/
│       │       └── noop_plugin.py
│       └── composition/
│           ├── __init__.py
│           └── container.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_smoke.py
```

## 9. Coding Standards
- Python 3.11+ only. Use modern typing (`X | None`, not `Optional[X]`) throughout.
- 100% of public functions/classes must have type hints and docstrings (Google-style docstrings).
- No bare `except:` clauses anywhere. Every caught exception must be caught by name and either re-raised as a domain exception or logged with context.
- No global mutable state outside the registry module, and even that must be encapsulated behind functions, never a raw module-level dict accessed externally.
- No print statements — logging module only, from the very first commit.
- Every module must have a module-level docstring explaining its single responsibility.
- Enforce max function length as a lint rule guideline (soft limit ~40 lines) — if Codex writes something longer, it must split it and explain why in a comment.
- All interfaces must be defined as `typing.Protocol` or `abc.ABC` — Codex must pick one convention and use it consistently across the entire codebase, not mix both without justification.

## 10. Architecture Rules
- **Plugin-based extensibility**: nothing in later phases should require editing `core/` files to add new behavior (new DAG types, new notification channels, new validators). Everything extends via registration.
- **Loose coupling**: interfaces in `interfaces/` must not import anything from `plugins/`. Dependency direction is strictly plugins → interfaces, never the reverse.
- **High cohesion**: each module does one thing. `logging.py` does not know about DAGs. `registry.py` does not know about Airflow.
- **No premature Airflow coupling**: nothing in this phase should import `airflow` at all. This proves the platform core is framework-agnostic and testable without a running Airflow instance.
- **Composition root pattern**: a single, clearly identified module (`composition/container.py`) is the only place where concrete plugins get wired together. This is where later phases will register their DAG factories, metadata loaders, etc.
- **Fail-fast configuration**: `core/config.py` must validate required environment variables at startup and raise a clear `ConfigurationError` rather than failing silently or with a KeyError deep in the stack later.

## 11. Constraints
- Do not add any dependency on `apache-airflow` yet — this phase must remain installable in a lightweight environment without a full Airflow install.
- Do not invent business concepts (DAG names, task names, ETL failure types) — those come from the Excel spec in Phase 2 onward.
- Do not create placeholder DAG files "just to show it works" — that violates the phase boundary and will be explicitly rejected.
- Keep the example plugin trivial (e.g., a no-op validator) — it exists only to prove the registry mechanism works, not to imply real functionality.

## 12. Acceptance Criteria
- `pip install -e .` succeeds in a clean virtual environment.
- `pytest` passes with the single smoke test.
- `ruff check .`, `black --check .`, and `mypy src/` all pass cleanly.
- Running the composition root wiring demonstration registers and resolves the example plugin correctly, proving the DI/registry mechanism functions end-to-end.
- No file in the repository imports `airflow`.
- Every interface has at least one docstring explaining what future phase will implement it and why it exists.
- `docs/ARCHITECTURE.md` clearly documents the plugin registration mechanism with a code example.

## 13. Things NOT to Do
- Do NOT generate any Airflow DAG files.
- Do NOT parse or reference any Excel file — none exists yet in this phase.
- Do NOT hardcode any business logic, DAG names, or task names.
- Do NOT add Datadog, Teams, Kafka, MinIO, Snowflake, dbt, or FastAPI SDK dependencies — only reserve the interface seams for them.
- Do NOT skip type hints "for now" — this is a standard set once, in Phase 1, and enforced forever after.
- Do NOT use a requirements.txt-only dependency setup — use `pyproject.toml` as the single source of truth.
- Do NOT silently swallow exceptions anywhere in the scaffold.

## 14. Questions Codex Should Ask Instead of Assuming
- Should the project use `abc.ABC` or `typing.Protocol` as the standard interface convention platform-wide?
- Should logging default to JSON-structured output (for downstream Datadog ingestion in later phases) or human-readable console output in dev mode, and how should that be toggled?
- What is the minimum supported Python version — is 3.11 confirmed, or should it target 3.12?
- Should the plugin registry support versioned plugins (e.g., multiple versions of the same DAG builder coexisting) or is a single-active-version model sufficient for this platform?
- Is there an existing internal Python style guide (e.g., a specific docstring format, import ordering convention) that should override the defaults proposed here?

---

# PROMPT 2 — Metadata Layer, Schema, and Validation

## 1. Title
**Phase 2: Metadata Ingestion, Schema Modeling, and Validation Layer for the AI AutoRCA Airflow Platform**

## 2. Background
Phase 1 delivered a framework-agnostic platform scaffold with plugin architecture, DI composition root, logging, and interface contracts — but zero business logic and zero Airflow awareness. This phase, Phase 2, introduces the **single source of truth**: a finalized Architecture Specification Excel workbook that describes every DAG, task, dependency, schedule, pool, retry policy, and integration touchpoint for the 56 production DAGs (and by extension, the pattern for any future DAG #57+).

This phase builds the **metadata layer**: the code that reads that Excel workbook, converts it into strongly-typed, validated Python objects, and persists it into a normalized, machine-readable intermediate format (YAML or JSON) that Phase 3's Dynamic DAG Factory will consume. This phase does NOT build any DAGs. It builds the data contract and validation gate that makes DAG generation in Phase 3 safe, deterministic, and free of hardcoded business logic.

Think of this phase as building a compiler front-end: lexing/parsing the Excel "source code" into a validated Abstract Syntax Tree (the metadata model) that the next phase's "code generator" (DAG Factory) will consume.

## 3. Objective
Build a robust metadata ingestion pipeline that:
- Reads the attached Architecture Specification Excel file (all relevant sheets/tabs).
- Converts every row/sheet into strongly-typed Pydantic models with full validation (types, required fields, referential integrity across sheets, enum constraints).
- Compiles the validated in-memory model into normalized YAML or JSON configuration artifacts, one per DAG (plus shared/global configuration), that Phase 3 will consume as its sole input.
- Rejects invalid, incomplete, or ambiguous metadata loudly and specifically — never silently defaults or guesses at missing values.
- Provides a metadata loader interface (implementing the `MetadataLoader` interface stubbed in Phase 1) that Phase 3+ code will import rather than re-implementing parsing logic.

## 4. Scope
**In scope:**
- Excel reading (all relevant sheets: e.g., DAG registry, task definitions, dependency graph, schedules, pools, retries, callbacks, integration mappings — Codex must inventory the actual sheet names/columns from the attached file and not assume a fixed schema in advance)
- Pydantic model definitions mirroring every entity in the spec (DAG, Task, Dependency, Pool, Schedule, RetryPolicy, CallbackConfig, IntegrationConfig, etc.)
- Cross-sheet referential integrity validation (e.g., every task's "depends_on" references an actual task ID that exists; every DAG references pools that are defined)
- A metadata compiler that serializes validated models into normalized YAML/JSON, one file per DAG plus a global/shared config file
- A metadata loader module implementing the Phase 1 `MetadataLoader` interface, capable of loading the compiled YAML/JSON (not re-parsing Excel at DAG-parse time — Excel parsing is a build-time/compile-time step, not a runtime step, for performance and Airflow DAG-parse-time constraints)
- Schema versioning so future metadata format changes don't silently break older compiled configs
- CLI entrypoint (e.g., `autorca-metadata compile --input spec.xlsx --output configs/`) to run the compilation step

**Out of scope:**
- Any DAG object construction
- Any Airflow operator instantiation
- Any of the 56 DAG wrapper files
- Runtime Excel parsing inside Airflow's DAG-parsing loop (this is explicitly forbidden — see Constraints)

## 5. Inputs
- The Architecture Specification Excel file (attached by the user in the actual working session — Codex must inspect its real sheet names, column headers, and data types rather than assuming a structure, and must ask if the file is not actually provided).
- The Phase 1 platform scaffold (interfaces, registry, logging, exceptions) as a hard dependency — this phase extends it, not replaces it.

## 6. Outputs
- A `MetadataCompiler` that transforms the Excel workbook into validated Pydantic model instances.
- A set of normalized YAML/JSON files (one per DAG, plus shared config) written to a `configs/` directory, representing the compiled, validated metadata.
- A `MetadataLoader` implementation that Phase 3 will use to load these compiled configs at DAG-factory time.
- A validation report (human-readable, e.g., printed table or written report file) summarizing every validation error found, with sheet name, row number, and field name — never a generic "invalid metadata" message.

## 7. Deliverables
1. `metadata/models.py` — full Pydantic model hierarchy representing the Excel spec's entities
2. `metadata/excel_reader.py` — Excel ingestion logic (using `openpyxl` or `pandas`, Codex should justify the choice) that maps raw sheet rows into the Pydantic models
3. `metadata/validators.py` — cross-entity/referential validation logic beyond what Pydantic field validators alone can express (e.g., DAG-to-DAG dependency cycle pre-checks at the metadata level, distinct from Phase 3's DAG-level cycle detection)
4. `metadata/compiler.py` — orchestrates read → validate → serialize into YAML/JSON
5. `metadata/loader.py` — implements Phase 1's `MetadataLoader` interface; loads compiled YAML/JSON at DAG-factory time
6. `metadata/schema_version.py` — versioning/migration scaffold for the compiled config format
7. `cli/compile_metadata.py` — CLI entrypoint wired via `pyproject.toml` console_scripts
8. Validation report generator producing clear, actionable, per-row/per-field error output
9. Unit tests covering: happy path compilation, missing required field, invalid enum value, dangling reference (task depends on non-existent task), duplicate DAG ID, duplicate task ID within a DAG
10. Updated `docs/ARCHITECTURE.md` Phase 2 section describing the metadata compilation pipeline with a diagram (ASCII or Mermaid) showing Excel → Pydantic models → validation → YAML/JSON → Phase 3 consumption

## 8. Folder Structure (additions to Phase 1 tree)
```
src/autorca_platform/
├── metadata/
│   ├── __init__.py
│   ├── models.py
│   ├── excel_reader.py
│   ├── validators.py
│   ├── compiler.py
│   ├── loader.py
│   └── schema_version.py
├── cli/
│   ├── __init__.py
│   └── compile_metadata.py
configs/                      # generated output, not hand-written
├── global_config.yaml
└── dags/
    └── <dag_id>.yaml
tests/
├── metadata/
│   ├── test_excel_reader.py
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_compiler.py
```

## 9. Coding Standards
- All models must use Pydantic v2 idioms (`model_validator`, `field_validator`, `ConfigDict`) — not deprecated v1-style validators.
- Every model field must have an explicit type, and `Any` is banned except where the Excel source genuinely allows heterogeneous data (must be justified in a comment if used).
- Excel reading must never use magic column indices (`row[3]`) — always resolve columns by header name, with a clear error if an expected header is missing or renamed.
- All validation errors must be collected and reported together (not fail on first error) so a spec author can fix all issues in one pass rather than one Codex run per error.
- Follow all Phase 1 standards (typing, docstrings, exception hierarchy usage, logging, no print statements) without exception.

## 10. Architecture Rules
- **Compile-time, not runtime, Excel parsing.** Airflow re-parses DAG files on a scan interval; parsing a multi-sheet Excel file on every DAG-parse cycle would be a severe performance and reliability anti-pattern in a 500+ DAG platform. Excel parsing happens once via CLI, producing static YAML/JSON that Phase 3's factory loads cheaply and repeatedly.
- **Fail loudly, fail early, fail specifically.** Invalid metadata must never silently produce a partially-built DAG later — it must be rejected at compile time with a precise, actionable error.
- **Single source of truth.** The Excel file is authoritative. The compiled YAML/JSON is a derived artifact, not a second source of truth — it should be treated as regeneratable/disposable build output (consider whether it belongs in version control or `.gitignore`, and ask if unclear).
- **Schema versioning from day one.** Enterprise metadata formats evolve; the compiled config format must carry a version field so Phase 3+ loaders can detect and reject/migrate incompatible formats rather than crash unpredictably.
- **Extend, don't modify, Phase 1 interfaces.** `MetadataLoader` from Phase 1 must be implemented, not redefined.

## 11. Constraints
- Do not assume the Excel sheet names, column names, or tab count — inspect the actual attached file first and document the discovered schema before writing ingestion code.
- Do not build any Airflow-specific code (no `DAG()`, no operators) in this phase.
- Do not perform metadata validation only at the Pydantic field level if the spec implies cross-row/cross-sheet constraints (e.g., dependency references, pool existence) — those require explicit custom validators.
- Do not silently coerce mismatched types (e.g., a schedule column containing both cron strings and preset values like `@daily`) — explicitly model and validate the allowed value space.

## 12. Acceptance Criteria
- Running the CLI against the real attached Excel file produces valid YAML/JSON for every DAG defined in the spec, or a complete, readable validation error report if the spec has issues.
- Every entity type in the Excel maps to exactly one Pydantic model with full field coverage — no silently dropped columns.
- Referential integrity (task dependency references, pool references, DAG-level dependency references) is fully validated with specific, row-referenced error messages.
- Unit tests achieve meaningful coverage of both happy-path and failure-path scenarios listed in Deliverables item 9.
- The compiled config format includes a schema version field, and the loader rejects unknown/future versions with a clear error rather than attempting best-effort parsing.

## 13. Things NOT to Do
- Do NOT generate any DAG objects or Airflow operator instances.
- Do NOT hardcode assumptions about sheet/column names without first inspecting the actual attached Excel file.
- Do NOT parse Excel inside any function that Airflow's scheduler would call repeatedly (DAG-parse-time performance is a hard constraint for a 500+ DAG platform).
- Do NOT silently default missing required fields — every missing required field is a validation error, not a "reasonable default" opportunity.
- Do NOT proceed with ingestion logic if the Excel structure is ambiguous or inconsistent — stop and ask.

## 14. Questions Codex Should Ask Instead of Assuming
- What are the exact sheet names and column headers in the attached Architecture Specification Excel? (Must inspect before modeling, not assume.)
- Should the compiled YAML/JSON output be committed to version control, or treated as a build artifact regenerated in CI?
- Are DAG IDs and Task IDs guaranteed unique within the spec, or does the spec have known duplicates/aliases that need special handling?
- Should schema validation be strict (reject any unrecognized extra column) or permissive (ignore and warn on unrecognized columns) — this has real implications as the spec evolves toward DAG #57 and beyond?
- Is YAML or JSON the preferred compiled format, and is there a reason to prefer one (e.g., YAML for human readability during ops review, JSON for stricter typing/parsing speed)?

---

# PROMPT 3 — Dynamic DAG Factory and Builder Subsystem

## 1. Title
**Phase 3: Dynamic DAG Factory, Builder Subsystem, and Metadata-Driven Airflow Construction Engine**

## 2. Background
Phase 1 built the framework-agnostic platform chassis. Phase 2 built the metadata compiler that converts the Architecture Specification Excel into validated, normalized YAML/JSON per DAG. Neither phase has touched Apache Airflow itself. Phase 3 is where Airflow enters the codebase for the first time: this phase builds the **Dynamic DAG Factory** — the engine that reads Phase 2's compiled metadata and constructs fully-formed Airflow `DAG` objects, task graphs, TaskGroups, branching logic, sensors, dynamic task mapping, pools, retries, callbacks, and trigger rules — entirely driven by metadata, with zero hardcoded business logic for any specific DAG.

This is the architectural core of the entire platform: if this phase is built correctly, generating DAG #57 (or #500) in Phase 4 becomes a metadata-only exercise with zero new Python code. If this phase is built with any hardcoded per-DAG logic, the platform fails its core design goal and will not scale past a handful of DAGs without linear engineering cost.

## 3. Objective
Build a fully generic, metadata-driven DAG construction engine consisting of:
- A `DagBuilder` (implementing Phase 1's `DagBuilder` interface) that takes one compiled DAG metadata object (from Phase 2) and produces a valid Airflow `DAG` instance.
- A `TaskRegistry` mapping metadata-declared task "types" to concrete Airflow operator/plugin implementations, extensible via the Phase 1 plugin registry.
- A `DependencyResolver` that wires task dependencies from the metadata's dependency graph, including cycle detection at DAG-construction time (distinct from Phase 2's metadata-level pre-check).
- A `TaskGroupBuilder`, `BranchBuilder`, and `SensorBuilder` for the corresponding Airflow constructs, all driven by metadata flags/config rather than DAG-specific code paths.
- Support for dynamic task mapping (Airflow's `.expand()` pattern) where metadata specifies mapped tasks.
- Metadata-driven configuration of pools, retries, callbacks (`on_failure_callback`, `sla_miss_callback`), and trigger rules — no defaults silently assumed unless explicitly specified as platform-wide defaults in Phase 2's global config.

## 4. Scope
**In scope:**
- `DagBuilder` core class and its supporting builder subsystem (Task, TaskGroup, Branch, Sensor)
- `TaskRegistry` — extensible mapping from metadata task "type" strings to operator factory functions/plugins
- `DependencyResolver` with cycle detection and topological construction order
- Dynamic task mapping support
- Pool, retry, callback, and trigger-rule wiring, all sourced from metadata, none hardcoded
- Concurrency pattern support (DAG-level `max_active_runs`, `max_active_tasks`, task-level `pool`, `pool_slots`) as metadata-driven fields
- Validation at DAG-construction time (e.g., referenced operator type exists in the registry; catches errors Phase 2 couldn't catch because they require live Airflow operator classes)
- A demonstration harness that builds a DAG object from a *sample* metadata file (not yet the real 56 — that's Phase 4) to prove the factory works end-to-end

**Out of scope:**
- The actual 56 production DAG wrapper files (Phase 4)
- Concrete Datadog/Teams/AI AutoRCA callback *implementations* (Phase 4 wires stubs; this phase only defines the callback *interface hook points*)
- CI/CD, deployment, Helm, Rancher (Phase 5)

## 5. Inputs
- Phase 1 platform scaffold (interfaces, plugin registry, DI container, logging, exceptions)
- Phase 2 metadata layer (compiled YAML/JSON configs, `MetadataLoader` implementation, Pydantic models)
- The Architecture Specification Excel (already compiled via Phase 2 — this phase consumes compiled metadata, not the raw Excel, per the compile-time/runtime separation established in Phase 2)

## 6. Outputs
- A working, generic `DagBuilder` capable of producing valid Airflow `DAG` objects from any correctly-formed compiled metadata file, without modification for new DAGs.
- An extensible `TaskRegistry` with at least the operator types actually present in the Architecture Specification Excel registered as plugins (inspect the real spec to determine which operator/task types are needed — do not assume a generic set like "just PythonOperator and BashOperator" without checking).
- Full dependency graph resolution with cycle detection that fails DAG construction (not silently drops edges) on any cycle.
- A proof-of-concept DAG built entirely from a sample metadata file, parseable by `airflow dags list` (or equivalent local validation) without errors.

## 7. Deliverables
1. `factory/dag_builder.py` — implements Phase 1's `DagBuilder` interface
2. `factory/task_registry.py` — plugin-registry-backed mapping of task types to operator constructors
3. `factory/dependency_resolver.py` — dependency graph construction + cycle detection (e.g., via topological sort, raising a domain-specific `DependencyCycleError` with the exact cycle path in the error message)
4. `factory/task_group_builder.py`
5. `factory/branch_builder.py`
6. `factory/sensor_builder.py`
7. `factory/dynamic_mapping.py` — dynamic task mapping support
8. `factory/pool_retry_config.py` — pool/retry/trigger-rule application logic, metadata-driven
9. `factory/callback_hooks.py` — defines the extension points for `on_failure_callback`/`sla_miss_callback` that Phase 4 will populate with real Datadog/Teams/AI AutoRCA stubs; this phase defines the hook signature and a no-op default, not the real integration
10. A sample metadata fixture (synthetic, small, e.g., 2–3 tasks) used purely to prove the factory works, clearly labeled as a test fixture and not a real production DAG
11. Unit + integration tests: successful DAG construction, cycle detection triggers correctly, unknown task type raises a clear registry error, dynamic mapping produces the expected task instances, pool/retry config is correctly applied to constructed tasks
12. Updated `docs/ARCHITECTURE.md` Phase 3 section with a diagram showing metadata → DagBuilder → registry lookups → constructed DAG object, and an explicit worked example of "how DAG #57 would be added using only metadata, zero new code" (conceptual walkthrough, not the actual DAG #57 build — that's a Phase 5 documentation deliverable in full)

## 8. Folder Structure (additions)
```
src/autorca_platform/
├── factory/
│   ├── __init__.py
│   ├── dag_builder.py
│   ├── task_registry.py
│   ├── dependency_resolver.py
│   ├── task_group_builder.py
│   ├── branch_builder.py
│   ├── sensor_builder.py
│   ├── dynamic_mapping.py
│   ├── pool_retry_config.py
│   └── callback_hooks.py
tests/
├── factory/
│   ├── test_dag_builder.py
│   ├── test_task_registry.py
│   ├── test_dependency_resolver.py
│   ├── test_dynamic_mapping.py
│   └── fixtures/
│       └── sample_dag_metadata.yaml
```

## 9. Coding Standards
- All Airflow-specific imports must be isolated to the `factory/` package — no `airflow` imports should leak into `metadata/` or `core/` from Phase 1/2, preserving the framework-agnostic boundary established earlier.
- Every builder class must be independently unit-testable without a running Airflow scheduler/webserver (construct DAG objects in-process, assert on their structure).
- No `try/except Exception: pass` around DAG construction — every failure mode (unknown task type, cycle, missing required metadata field not caught in Phase 2) must raise a specific, named exception from the Phase 1 exception hierarchy (extended here with factory-specific subclasses).
- Follow all standards from Phases 1 and 2 (typing, docstrings, logging, no prints, Pydantic v2 idioms where models are touched).

## 10. Architecture Rules
- **Zero hardcoded business logic.** No DAG name, task name, or DAG-specific branching condition may appear as a literal in any file under `factory/`. If Codex finds itself writing `if dag_id == "etl_snowflake_daily":`, that is an architecture violation — the distinguishing behavior must come from metadata fields, not code branches.
- **Registry-driven extensibility.** New task types must be addable by registering a new plugin, never by editing `dag_builder.py`'s internals.
- **Explicit failure over implicit recovery.** A DAG that cannot be fully and correctly constructed from its metadata must fail construction loudly, not partially construct with missing tasks/dependencies.
- **Separation of construction from execution.** The `DagBuilder` produces DAG objects; it must not itself perform any DAG *runtime* concerns (no actual task execution logic belongs here — that lives in the operator/plugin implementations the registry points to).
- **Idempotent construction.** Calling the builder twice on the same metadata must produce structurally identical DAGs (important given Airflow's DAG-parsing re-invocation model).

## 11. Constraints
- Do not build any of the real 56 production DAGs in this phase — only the generic factory and one clearly-labeled synthetic test fixture.
- Do not implement real Datadog/Teams/AI AutoRCA callback logic — only the hook interface and a no-op default implementation.
- Do not assume the full set of task/operator types needed — inspect Phase 2's compiled metadata (or the original Excel) to determine the actual operator types the real 56 DAGs require, and register at least those.
- Do not skip cycle detection "because the metadata was already validated in Phase 2" — Phase 2 checks metadata-level references; Phase 3 must independently verify the constructed dependency graph is acyclic as a defense-in-depth measure, since these are different representations built by different code.

## 12. Acceptance Criteria
- The `DagBuilder`, given the sample fixture metadata, produces a DAG object that Airflow can parse without error (verifiable via `airflow dags list` or the equivalent DAG-parsing validation used in the platform's test suite).
- Introducing a deliberately cyclic sample metadata fixture causes construction to fail with a `DependencyCycleError` naming the exact cycle, not a generic failure.
- Introducing an unregistered task type in sample metadata causes a clear `UnknownTaskTypeError`, not a silent skip or a raw `KeyError`.
- Dynamic task mapping fixture produces the correct number of mapped task instances at construction/expansion time.
- No literal DAG ID or business-specific task name appears anywhere in `factory/` source files (searchable/verifiable).
- All Phase 3 unit and integration tests pass, and Phase 1/2 tests continue to pass unmodified.

## 13. Things NOT to Do
- Do NOT hardcode any of the 56 production DAG names, task names, or business conditions anywhere in this phase's code.
- Do NOT implement real external integrations (Datadog, Teams, AI AutoRCA) — stubs/hooks only.
- Do NOT skip independent cycle detection at this layer on the assumption Phase 2 already handled it.
- Do NOT couple `factory/` code to a specific Kubernetes/Rancher execution environment — that belongs in Phase 4/5 deployment concerns, not DAG construction logic.

## 14. Questions Codex Should Ask Instead of Assuming
- What is the complete, real set of task/operator "types" declared across all 56 DAGs in the compiled metadata — should Codex enumerate this from the actual Phase 2 output before building the registry, rather than guessing a generic operator set?
- Are there platform-wide default retry/pool/trigger-rule values that apply when a DAG's metadata omits them, and where should those defaults be defined — in Phase 2's global config, or as constants in the factory?
- Should dynamic task mapping support be limited to simple list-based `.expand()`, or does the spec require more advanced patterns like mapping over XCom-derived values?
- What Airflow version is targeted, since dynamic task mapping, TaskGroup, and callback APIs have evolved across Airflow 2.x versions and this affects exact implementation details?
- Should the DAG-construction-time cycle detection algorithm and error format match Phase 2's metadata-level cycle pre-check exactly, for consistent error messaging to platform users, or can they differ since they serve different audiences (metadata authors vs. DAG-parse-time debugging)?

---

# PROMPT 4 — DAG Generation and Integration Plugins

## 1. Title
**Phase 4: Production DAG Generation (All 56 DAGs) and Integration Plugin Implementation for the AI AutoRCA Airflow Platform**

## 2. Background
Phases 1–3 built, in order: the framework-agnostic platform scaffold, the metadata compiler (Excel → validated YAML/JSON), and the generic, metadata-driven Dynamic DAG Factory with its full builder subsystem (task registry, dependency resolver, TaskGroup/branch/sensor builders, dynamic mapping, pool/retry/callback hooks). No hardcoded business logic exists anywhere in the codebase yet, and no real DAG has been generated — only a synthetic test fixture proved the factory works.

Phase 4 is where the platform becomes real: this phase generates the actual 56 production DAG wrapper files (one lightweight file per DAG, each doing nothing but invoking the Phase 3 factory with its specific compiled metadata) and implements the concrete integration plugins the platform has been reserving interface seams for since Phase 1 — Datadog observability, Microsoft Teams notification, AI AutoRCA callback stubs, Kubernetes execution support, and the operator/connector/validation plugins the real 56 DAGs actually require.

The defining success criterion of this entire 5-phase build lives in this phase: **adding a hypothetical DAG #57 after this phase is complete must require only a new metadata entry (Excel row + recompile), never a new Python file or any change to `factory/` or `plugins/` internals.**

## 3. Objective
- Generate all 56 DAG wrapper files, each a thin, near-identical file that loads its compiled metadata and calls the Phase 3 `DagBuilder` — no per-DAG custom logic.
- Implement concrete plugin classes for every task/operator type the real metadata references (registered into Phase 3's `TaskRegistry`).
- Implement Datadog integration stubs (metric/event emission hooks wired to Phase 3's observability interface) — "stub" here means a real, working integration point with a clearly documented interface, using either a real Datadog client call or a well-defined mockable boundary, per whatever the actual environment allows; Codex must ask if unsure whether live Datadog credentials/environment are available in this phase.
- Implement Microsoft Teams Adaptive Card notification stubs wired to Phase 1's `NotificationSink` interface.
- Implement AI AutoRCA callback stubs wired to Phase 3's `callback_hooks` extension points.
- Implement Kubernetes execution support (e.g., KubernetesPodOperator-based plugin registration) if the metadata specifies Kubernetes-executed tasks.
- Implement any additional connector/validation plugins the real metadata requires (e.g., Snowflake connector, dbt runner, Kafka producer/consumer task types) — determined by inspecting the actual compiled metadata from Phase 2, not assumed in advance.

## 4. Scope
**In scope:**
- 56 DAG wrapper files (or however many DAG entries the real compiled metadata actually contains — Codex must verify this count against Phase 2's output rather than blindly trusting the number 56 if the real data differs, and flag any discrepancy)
- Concrete operator/task-type plugins for every type referenced in the real metadata
- Datadog integration plugin
- Microsoft Teams integration plugin (Adaptive Card formatting)
- AI AutoRCA callback plugin
- Kubernetes/Rancher execution plugin(s) as required by metadata
- Any connector plugins for Snowflake, Kafka, MinIO, dbt as required by the real metadata (inspect first)
- Validation plugins referenced by metadata (e.g., data quality checks, schema validation tasks)
- A "how to add DAG #57" proof: a documented, executable demonstration that adding one new metadata entry and recompiling produces a working 57th DAG with zero new/changed Python source files outside the metadata/config directory

**Out of scope:**
- Testing framework, CI/CD pipelines, Helm charts, Rancher deployment manifests, and comprehensive documentation guides (Phase 5)
- Any changes to the core `factory/` builder logic from Phase 3 — if Phase 4 discovers Phase 3 is missing a needed capability, that is a defect to report and fix in `factory/`, not a workaround to hack into a DAG wrapper file

## 5. Inputs
- Phases 1–3 complete codebase
- Phase 2's compiled metadata (the real YAML/JSON for all actual DAGs in the Architecture Specification Excel)
- The Architecture Specification Excel itself (for cross-referencing integration requirements, e.g., which DAGs need Datadog vs. Teams vs. both)
- Any real credentials/environment details needed for live integration testing of Datadog/Teams/Kubernetes — Codex must ask what's available (e.g., sandbox Datadog account, test Teams webhook URL, dev Kubernetes namespace) rather than assuming production credentials are usable

## 6. Outputs
- 56 (or the verified real count) DAG wrapper files, each under ~20–30 lines, each structurally near-identical, differing only in which metadata file they load.
- A complete set of registered plugins covering every task type, connector, and integration the real metadata requires.
- A working demonstration of the "DAG #57 requires only metadata" claim.
- Zero duplicated business logic across DAG wrapper files (verify via a duplication/similarity check if feasible).

## 7. Deliverables
1. `dags/` directory containing all real DAG wrapper files, generated from Phase 2's compiled metadata list
2. `plugins/operators/` — concrete operator plugin implementations for each task type
3. `plugins/connectors/` — Snowflake/Kafka/MinIO/dbt connector plugins as required
4. `plugins/observability/datadog_plugin.py` — Datadog integration implementing Phase 1's `ObservabilitySink`
5. `plugins/notifications/teams_plugin.py` — Teams Adaptive Card integration implementing Phase 1's `NotificationSink`
6. `plugins/callbacks/autorca_callback_plugin.py` — AI AutoRCA callback implementation wired to Phase 3's `callback_hooks`
7. `plugins/execution/kubernetes_plugin.py` — Kubernetes/Rancher execution plugin(s) as required
8. `plugins/validation/` — any data quality/schema validation plugins required by metadata
9. A DAG-generation script/CLI (e.g., `autorca-dags generate`) that reads Phase 2's compiled metadata list and emits the wrapper files — so the 56 files are themselves generated output from a documented, reproducible process, not hand-typed one by one
10. The "add DAG #57" demonstration: a new sample metadata entry, a recompile step, and proof (test or manual walkthrough with commands) that the new DAG appears and is structurally valid with zero new/edited files outside `configs/` and the generated `dags/` output
11. Integration tests for each plugin (mockable where live credentials aren't available, clearly documented which tests require real credentials vs. which run fully mocked)
12. A duplication check/report across the 56 DAG wrapper files confirming they are structurally uniform

## 8. Folder Structure (additions)
```
src/autorca_platform/
├── plugins/
│   ├── operators/
│   │   └── <one file per real task type>.py
│   ├── connectors/
│   │   ├── snowflake_connector.py
│   │   ├── kafka_connector.py
│   │   ├── minio_connector.py
│   │   └── dbt_connector.py
│   ├── observability/
│   │   └── datadog_plugin.py
│   ├── notifications/
│   │   └── teams_plugin.py
│   ├── callbacks/
│   │   └── autorca_callback_plugin.py
│   ├── execution/
│   │   └── kubernetes_plugin.py
│   └── validation/
│       └── <validation plugins as required>.py
├── codegen/
│   ├── __init__.py
│   └── generate_dag_wrappers.py
dags/
├── <dag_id_1>.py
├── <dag_id_2>.py
├── ...
└── <dag_id_56>.py
tests/
├── plugins/
│   └── <test per plugin category>
└── codegen/
    └── test_generate_dag_wrappers.py
```

## 9. Coding Standards
- Every DAG wrapper file must be near-byte-identical in structure to every other one (differing only in the metadata file path/DAG ID it references) — any structural divergence between two DAG wrapper files is a defect, not a stylistic choice.
- Every plugin must be registered via Phase 1's plugin registry decorator pattern, not imported and wired ad hoc.
- Integration plugins must clearly separate "build the payload" logic (easily unit-testable, pure functions) from "send the payload" logic (the only part that needs mocking/live credentials in tests).
- Follow all standards from Phases 1–3.

## 10. Architecture Rules
- **The DAG #57 test is the north star.** Every design decision in this phase must be evaluated against: "if a new row is added to the Excel spec and recompiled, does a new working DAG appear with zero new Python code?" If not, the architecture has failed its core goal and must be fixed in `factory/` (Phase 3) or `plugins/` (this phase), never patched around in a DAG wrapper file.
- **DAG wrapper files are generated artifacts, not hand-authored code.** They should be produced by `codegen/generate_dag_wrappers.py` reading Phase 2's metadata list, ensuring consistency and making regeneration trivial when metadata changes.
- **Plugins are the only place business-specific logic lives**, and even there, logic should be per-task-type or per-integration, never per-DAG.
- **Fail-safe integrations.** A Datadog or Teams outage must not fail the underlying data pipeline task — observability/notification failures should be caught, logged, and (per platform convention established here) not raise exceptions that fail the primary task unless explicitly configured to be critical-path.

## 11. Constraints
- Do not hand-write 56 individually customized DAG files — they must come from the codegen script reading metadata, proving true metadata-driven generation.
- Do not modify `factory/` internals in this phase to work around a missing capability discovered — file it as a required fix to Phase 3's design and implement it there, keeping phase boundaries clean, then resume Phase 4.
- Do not fabricate Datadog/Teams/Kubernetes credentials or assume a specific account/namespace exists — ask what's actually available for integration testing.
- Do not let observability/notification plugin failures silently swallow errors in a way that would hide real pipeline failures from on-call engineers — failures in the plugin itself must still be logged, even if they don't fail the parent task.

## 12. Acceptance Criteria
- The number of generated DAG wrapper files matches the actual number of DAG entries in Phase 2's compiled metadata (verify against the real Excel; flag if it isn't exactly 56).
- All generated DAG files pass Airflow's DAG-parsing validation with zero import errors.
- A structural diff/duplication check confirms DAG wrapper files are uniform aside from metadata references.
- Every task type referenced in the real metadata has a corresponding registered plugin — no "unknown task type" errors when the factory builds any of the 56 real DAGs.
- The DAG #57 demonstration succeeds: new metadata entry + recompile + codegen re-run produces a valid new DAG with zero hand-edited files outside metadata/config and the generated `dags/` output.
- Datadog, Teams, and AI AutoRCA callback plugins have passing tests, clearly marked as mocked vs. live-credential-dependent.

## 13. Things NOT to Do
- Do NOT hand-author DAG wrapper files individually — they must be generated from metadata via the codegen script.
- Do NOT put any per-DAG conditional logic inside a DAG wrapper file.
- Do NOT modify Phase 3's `factory/` to sneak in DAG-specific behavior — if the factory is missing something, fix it generically.
- Do NOT assume live Datadog/Teams/Kubernetes credentials exist in the development/build environment without confirming.
- Do NOT let a notification or observability plugin exception crash the primary ETL task without that being an explicit, documented, metadata-driven choice.

## 14. Questions Codex Should Ask Instead of Assuming
- Does the real compiled metadata contain exactly 56 DAG entries, or does the actual Excel spec differ from that number — should Codex verify and reconcile before generating wrapper files?
- What credentials/environment are actually available for Datadog, Teams, and Kubernetes integration testing in this build phase — sandbox accounts, mocked clients only, or none yet (stub-only until Phase 5 deployment)?
- Should observability/notification plugin failures ever be allowed to fail the parent Airflow task (i.e., are there specific DAGs where "the RCA notification must succeed or the task fails" is a real business requirement), or is fail-safe (log-and-continue) the correct default for all 56 DAGs?
- Which specific task/operator types actually appear in the real metadata (Snowflake queries, Kafka producers/consumers, dbt runs, Kubernetes pods, plain Python callables, etc.) — should Codex enumerate this list from Phase 2's real output before building the plugin set, rather than guessing?
- For the Teams Adaptive Card format, is there an existing card schema/template already in use elsewhere in the organization that this plugin should match, or should Codex design a new card layout from the RCA notification requirements in the spec?

---

# PROMPT 5 — Testing, CI/CD, Deployment, and Documentation

## 1. Title
**Phase 5: Testing Strategy, CI/CD Pipeline, Kubernetes/Rancher Deployment, and Complete Documentation Suite for the AI AutoRCA Airflow Platform**

## 2. Background
Phases 1–4 delivered a complete, working, metadata-driven Airflow platform: a framework-agnostic core, a validated metadata compilation pipeline, a generic Dynamic DAG Factory, and all 56 real production DAGs generated via codegen with fully implemented integration plugins (Datadog, Teams, AI AutoRCA callbacks, Kubernetes execution, connectors). The platform is functionally complete but not yet production-ready in the enterprise sense: it lacks a comprehensive automated test suite, a CI/CD pipeline, deployment artifacts for Kubernetes/Rancher, and the documentation suite a real engineering organization requires to operate, extend, and hand off the platform safely.

Phase 5 closes the loop. This is where the platform becomes something a real platform team can run on-call, onboard new engineers into, and confidently extend to DAG #57 and well beyond, using only the documentation and tooling this phase produces — without ever needing to ask the original author a question.

## 3. Objective
- Build a comprehensive, layered automated test suite covering unit, integration, metadata-validation, dependency/cycle-detection, and DAG-parse-integrity tests across all prior phases.
- Build a CI/CD pipeline (the actual CI system must be confirmed — GitHub Actions is a reasonable default given the stack, but Codex must ask rather than assume) that runs linting, type-checking, the full test suite, metadata compilation validation, and DAG-parse validation on every change, and that builds/pushes deployable artifacts on merge to main.
- Build Kubernetes/Helm deployment artifacts and Rancher-specific configuration for running the platform (Airflow scheduler/webserver/workers, or KubernetesExecutor pods, as appropriate to the target Airflow deployment model).
- Write the complete documentation suite: README (finalize from Phase 1's skeleton), Developer Guide, Architecture Guide (finalize from Phases 1–4's incremental sections), Deployment Guide, Operations Guide, and a dedicated Future Extension Guide with a fully worked, step-by-step example of adding DAG #57.

## 4. Scope
**In scope:**
- Unit tests (extending/completing coverage across `core/`, `metadata/`, `factory/`, `plugins/`, `codegen/`)
- Integration tests (metadata compile → DAG build → DAG-parse-validate, end to end, for a sample of real DAGs and ideally all 56 if feasible in CI time budget — ask about CI time constraints)
- Metadata validation tests (Phase 2's validators, exercised against both valid and deliberately invalid fixture data)
- Dependency tests and cycle detection tests (both at Phase 2 metadata level and Phase 3 DAG-construction level)
- CI pipeline definition (lint, type-check, test, metadata-compile-check, DAG-parse-check, build)
- CD/deployment: Helm chart(s) for the platform, Rancher-specific values/overlays, environment-specific config (dev/staging/prod) — ask what environments actually exist
- Documentation: README, CONTRIBUTING (finalize), ARCHITECTURE (finalize), Developer Guide, Deployment Guide, Operations Guide, Future Extension Guide (with the DAG #57 walkthrough as its centerpiece)

**Out of scope:**
- Any new business logic, DAGs, or plugins beyond what Phase 4 already produced (this phase tests, deploys, and documents what exists — it does not extend platform capability)
- Live production credentials/secrets management specifics beyond documenting the pattern (e.g., document that secrets come from a Kubernetes Secret/Vault, but do not embed or fabricate actual secret values)

## 5. Inputs
- The complete Phase 1–4 codebase
- Information about the actual target CI system (GitHub Actions confirmed via the earlier project context referencing `github.com`/`codeload.github.com` access, but Codex should still confirm rather than assume other CI-specific details like runner types, required approvals, or environment protection rules)
- Information about the actual Kubernetes/Rancher target environment(s) — namespace conventions, existing Helm chart standards in the organization, ingress/networking conventions — Codex must ask rather than invent these

## 6. Outputs
- A complete, passing automated test suite with documented coverage expectations.
- A working CI pipeline definition file(s).
- Helm chart(s) and Rancher deployment configuration, environment-parameterized.
- A complete documentation suite, each guide self-contained and cross-linked.

## 7. Deliverables
1. `tests/` suite completed across all layers (unit, integration, metadata validation, dependency/cycle detection, DAG-parse integrity) with a documented coverage target (e.g., minimum 85% line coverage on `core/`, `metadata/`, `factory/`; plugin coverage documented separately given live-credential constraints)
2. `.github/workflows/ci.yml` (or the confirmed equivalent) implementing: lint → type-check → unit+integration tests → metadata compile check against the real Excel/compiled configs → DAG-parse validation for all 56 DAGs → build artifact
3. `.github/workflows/cd.yml` (or equivalent) implementing deployment on merge to main, environment-gated (dev auto-deploy, staging/prod gated per whatever approval model is confirmed)
4. `deploy/helm/` — Helm chart for the platform (Airflow components + any platform-specific config maps/secrets references), parameterized via `values.yaml` with environment overlays (`values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`)
5. `deploy/rancher/` — Rancher-specific manifests/config as required (namespace definitions, project associations, or whatever the real Rancher setup requires — ask)
6. `docs/README.md` — finalized, platform-level entry point
7. `docs/DEVELOPER_GUIDE.md` — local dev setup, running tests, adding a plugin, coding standards recap
8. `docs/ARCHITECTURE.md` — finalized, consolidating all 5 phases into one coherent architecture narrative with diagrams
9. `docs/DEPLOYMENT_GUIDE.md` — how to deploy to each environment, Helm/Rancher usage, rollback procedure
10. `docs/OPERATIONS_GUIDE.md` — on-call runbook: how to diagnose a failed DAG, how Datadog/Teams alerts map to platform components, how to read AI AutoRCA callback output, common failure modes and their resolutions
11. `docs/FUTURE_EXTENSION_GUIDE.md` — the definitive "how to add DAG #58, #59, ... #500" guide, built around a fully worked step-by-step example (using the DAG #57 proof-of-concept from Phase 4 as its basis), including how to add a brand-new task type (plugin) and a brand-new integration (e.g., adding a Slack notification sink alongside Teams) as extended examples of the plugin architecture's reach beyond just new DAGs

## 8. Folder Structure (additions)
```
.github/
└── workflows/
    ├── ci.yml
    └── cd.yml
deploy/
├── helm/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-staging.yaml
│   ├── values-prod.yaml
│   └── templates/
│       └── <k8s manifests>
└── rancher/
    └── <rancher-specific config>
docs/
├── README.md
├── DEVELOPER_GUIDE.md
├── ARCHITECTURE.md
├── DEPLOYMENT_GUIDE.md
├── OPERATIONS_GUIDE.md
└── FUTURE_EXTENSION_GUIDE.md
tests/
├── integration/
│   └── test_end_to_end_dag_generation.py
└── ... (completed suites across core/metadata/factory/plugins/codegen)
```

## 9. Coding Standards
- CI pipeline definitions must fail fast on the cheapest checks first (lint/type-check before the full test suite, metadata compile before DAG-parse validation) to keep feedback loops fast for developers.
- Helm chart values must never contain literal secrets — reference Kubernetes Secrets or an external secrets manager, and document (not implement, unless explicitly asked) the actual secrets backend in use.
- All documentation must be written in the same terse, precise, engineer-to-engineer register as the platform's code comments — no marketing language, no filler, every section actionable.
- Test names must clearly describe the scenario and expected outcome (`test_dag_builder_raises_cycle_error_on_circular_dependency`, not `test_1`).

## 10. Architecture Rules
- **CI mirrors the phase boundaries.** Pipeline stages should map recognizably to the platform's own layering (metadata compile check ≈ Phase 2, DAG-parse validation ≈ Phase 3/4), so a failing stage immediately tells an engineer which phase/layer likely has the defect.
- **Documentation is a first-class deliverable, not an afterthought.** The Future Extension Guide's DAG #57 walkthrough is the platform's ultimate acceptance test — if a new engineer, following only that document, cannot add a DAG without asking anyone a question, the documentation has failed.
- **Environment parity via Helm values, not branching Helm templates.** Differences between dev/staging/prod must be expressed as values overrides, not as forked/duplicated template logic — consistent with the platform-wide "configuration over code branching" philosophy established since Phase 1.
- **Operations Guide is written for 3 a.m. on-call, not for a design review.** It must be scannable, symptom-first (e.g., "Teams notification not received" → diagnostic steps → likely causes → fix), not a narrative walkthrough of the architecture.

## 11. Constraints
- Do not fabricate specific CI runner types, approval gates, secrets-manager products, or Rancher project/namespace names — confirm the real ones or clearly mark them as placeholders the operating team must fill in.
- Do not write documentation that merely restates code comments — it must add the "why" and the "how to operate/extend" context that isn't already in the source.
- Do not skip DAG-parse validation for any of the 56 real DAGs in CI on the assumption "the factory was already tested in Phase 3" — Phase 3 tested the generic factory with a synthetic fixture; Phase 5 must validate the real, complete set.
- Do not treat test coverage percentage as the sole quality bar — flag any critical path (e.g., cycle detection, referential integrity validation) that has high coverage numbers but shallow assertions, since that's a false signal of quality.

## 12. Acceptance Criteria
- CI pipeline runs successfully end to end against the real Phase 1–4 codebase: lint, type-check, full test suite, metadata compilation against the real Excel-derived configs, and DAG-parse validation for all 56 real DAGs.
- Helm chart deploys successfully (or is validated via `helm template`/`helm lint` at minimum, with real cluster deployment confirmed if a target cluster is actually available — ask) to at least a dev-equivalent configuration.
- Documentation suite is internally consistent (no contradictions between the Architecture Guide and the actual code), and the Future Extension Guide's DAG #57 example is directly traceable to the real Phase 4 proof-of-concept.
- A reviewer following only `DEVELOPER_GUIDE.md` can set up a working local dev environment and run the full test suite without needing to ask a question.
- A reviewer following only `FUTURE_EXTENSION_GUIDE.md` can (at least conceptually, if live credentials aren't available) trace every step required to add DAG #58 with zero new Python source files outside metadata/config.

## 13. Things NOT to Do
- Do NOT invent CI/CD infrastructure details (secrets manager brand, specific Rancher project names, cluster names) without confirming — mark clearly as placeholders otherwise.
- Do NOT write a documentation suite that only covers the happy path — the Operations Guide specifically must cover realistic failure modes.
- Do NOT let CI validate only a sample of the 56 DAGs when validating all 56 is feasible — sampling here undermines the platform's core reliability promise, unless CI time constraints genuinely require it (ask, and if so, document the tradeoff explicitly).
- Do NOT treat this phase as "just write some tests" — it is the platform's production-readiness gate, covering testing, deployment, and operational documentation together.

## 14. Questions Codex Should Ask Instead of Assuming
- What is the confirmed CI/CD system and its constraints (GitHub Actions is implied by repository access patterns established earlier, but are there runner time limits, required approvals for prod deploys, or existing organizational CI templates this pipeline must conform to)?
- What are the real target deployment environments (dev/staging/prod, or a different set), and is there an existing organizational Helm chart standard or Rancher project structure this platform must fit into rather than defining from scratch?
- What secrets management backend is actually in use (Kubernetes Secrets, HashiCorp Vault, cloud provider secrets manager) for Datadog API keys, Teams webhook URLs, and Snowflake/database credentials?
- Is there a required minimum test coverage threshold mandated by the organization, or should Codex propose one based on the criticality of each layer (core/metadata/factory higher, plugin integration code lower given credential constraints)?
- Should DAG-parse validation for all 56 real DAGs run on every CI trigger (every PR), or only on merge to main, given potential CI time/cost constraints — and is there a target CI pipeline duration this needs to stay under?

---

*End of five-phase Codex implementation plan. Each prompt above is self-contained and copy-paste ready. Phases must be executed in order (1 → 2 → 3 → 4 → 5); each phase's Codex session should be given only that phase's prompt plus the actual deliverables produced by prior phases, not the other four prompts.*

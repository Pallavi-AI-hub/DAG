"""Parse checks for generated production DAG wrappers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_generated_dag_wrappers_match_manifest_and_import() -> None:
    """Every manifest DAG should have one importable generated wrapper."""

    manifest = json.loads((REPO_ROOT / "configs" / "manifest.json").read_text(encoding="utf-8"))
    expected_dag_id_by_file = {dag_id.lower(): dag_id for dag_id in manifest["dag_ids"]}
    expected_dag_ids = set(expected_dag_id_by_file)
    wrapper_paths = sorted((REPO_ROOT / "dags").glob("*.py"))
    wrapper_ids = {path.stem for path in wrapper_paths}

    assert manifest["dag_count"] == len(expected_dag_ids)
    assert wrapper_ids == expected_dag_ids

    for path in wrapper_paths:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        assert hasattr(module, "dag")
        assert module.dag.dag_id == expected_dag_id_by_file[path.stem]

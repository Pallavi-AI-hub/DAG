"""Tests for the metadata compiler."""

from pathlib import Path

import pytest

from autorca_platform.metadata.compiler import MetadataCompiler
from autorca_platform.metadata.loader import JsonMetadataLoader

REAL_WORKBOOK = Path(r"C:\Users\mpallavi\Downloads\AI_AutoRCA_Platform_Architecture.xlsx")


@pytest.mark.skipif(not REAL_WORKBOOK.exists(), reason="real architecture workbook is not present")
def test_compiler_generates_56_configs_from_real_workbook(tmp_path: Path) -> None:
    """The real architecture workbook should compile to 56 DAG configs."""

    compiled = MetadataCompiler().compile_to_directory(REAL_WORKBOOK, tmp_path)

    assert compiled.global_config.dag_count == 56
    assert compiled.global_config.task_count == 686
    assert (tmp_path / "global_config.json").exists()
    assert (tmp_path / "manifest.json").exists()
    assert len(list((tmp_path / "dags").glob("*.json"))) == 56


@pytest.mark.skipif(not REAL_WORKBOOK.exists(), reason="real architecture workbook is not present")
def test_loader_reads_compiled_dag_config(tmp_path: Path) -> None:
    """The JSON loader should read compiler output back into strict models."""

    MetadataCompiler().compile_to_directory(REAL_WORKBOOK, tmp_path)

    config = JsonMetadataLoader().load_dag_config(tmp_path / "dags" / "rtl_log_ulrj.json")
    volume_check = next(task for task in config.tasks if task.task_name == "volume_check")

    assert config.dag.dag_id == "RTL_LOG_ULRJ"
    assert volume_check.upstream_tasks == ("extract_p1", "extract_p2", "extract_p3", "extract_p4")

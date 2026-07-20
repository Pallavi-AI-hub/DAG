"""Reusable task builders for product catalog incident simulations."""

from __future__ import annotations

import logging
from typing import Any

from autorca_platform.metadata.models import TaskRow

logger = logging.getLogger("autorca_platform.plugins.operators.product_catalog")


def run_product_catalog_task(
    *,
    task_kind: str,
    dag_id: str,
    task_name: str,
    operator_config: dict[str, Any],
    **_: Any,
) -> dict[str, Any]:
    """Execute a metadata-driven product catalog incident step.

    The implementation deliberately takes all business values from metadata so it can be reused
    by future product-catalog pipelines without changing the generated DAG wrapper.
    """

    event = {
        "dag_id": dag_id,
        "task_name": task_name,
        "task_kind": task_kind,
        "incident_id": operator_config.get("incident_id"),
        "pipeline_name": operator_config.get("pipeline_name"),
        "product_id": operator_config.get("product_id"),
        "lock_key": operator_config.get("lock_key"),
        "simulated_outcome": operator_config.get("simulated_outcome", "success"),
        "evidence": operator_config.get("evidence", {}),
    }
    logger.info("Product catalog incident step completed: %s", event)
    return event


class ProductCatalogTaskBuilder:
    """Build Product Catalog PythonOperator tasks from metadata."""

    def __init__(self, task_kind: str) -> None:
        """Create a builder for a reusable product-catalog task kind."""

        self.task_kind = task_kind

    def build(self, metadata: TaskRow) -> Any:
        """Build a metadata-driven Product Catalog task."""

        try:
            from airflow.providers.standard.operators.python import PythonOperator
        except ImportError:
            try:
                from airflow.operators.python import PythonOperator
            except ImportError:

                class PythonOperator:  # type: ignore[no-redef]
                    """Mock PythonOperator if Airflow is not present."""

                    def __init__(self, **kwargs: Any) -> None:
                        for key, value in kwargs.items():
                            setattr(self, key, value)

        kwargs = {
            "task_id": metadata.task_name,
            "python_callable": run_product_catalog_task,
            "op_kwargs": {
                "task_kind": self.task_kind,
                "dag_id": metadata.dag_id,
                "task_name": metadata.task_name,
                "operator_config": metadata.operator_config,
            },
            "trigger_rule": metadata.trigger_rule,
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return PythonOperator(**kwargs)

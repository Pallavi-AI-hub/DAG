"""Reusable task builders for product catalog incident simulations."""

from __future__ import annotations

import logging
import time
from typing import Any

from autorca_platform.metadata.models import TaskRow

logger = logging.getLogger("autorca_platform.plugins.operators.product_catalog")

PLIM_POSTGRES_CONN_ID = "plim_postgres"
PRODUCT_CATALOG_TABLE = "plim_demo.product_catalog"
PRODUCT_ID = 500000


def _get_postgres_conn() -> Any:
    """Return a new DB-API connection from Airflow's configured PLIM Postgres connection."""

    try:
        from airflow.providers.postgres.hooks.postgres import PostgresHook
    except ImportError:
        from airflow.hooks.postgres_hook import PostgresHook  # type: ignore[no-redef]

    return PostgresHook(postgres_conn_id=PLIM_POSTGRES_CONN_ID).get_conn()


def _validate_product() -> dict[str, Any]:
    """Validate that the target product row exists."""

    conn = _get_postgres_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT product_id FROM {PRODUCT_CATALOG_TABLE} WHERE product_id = %s",
                (PRODUCT_ID,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        raise ValueError(f"Product row does not exist: product_id={PRODUCT_ID}")
    return {"product_id": PRODUCT_ID, "validated": True}


def _prepare_state() -> dict[str, Any]:
    """Read the target row before concurrent writers run."""

    conn = _get_postgres_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT product_id FROM {PRODUCT_CATALOG_TABLE} WHERE product_id = %s",
                (PRODUCT_ID,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        raise ValueError(f"Cannot prepare state; product row missing: product_id={PRODUCT_ID}")
    return {"product_id": PRODUCT_ID, "state_prepared": True}


def _writer_a_holds_lock() -> dict[str, Any]:
    """Update and hold the target row lock for 30 seconds before committing."""

    conn = _get_postgres_conn()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute(
                f"UPDATE {PRODUCT_CATALOG_TABLE} "
                "SET product_id = product_id "
                "WHERE product_id = %s",
                (PRODUCT_ID,),
            )
            if cur.rowcount != 1:
                raise ValueError(f"Expected one locked row for product_id={PRODUCT_ID}, got {cur.rowcount}")
            logger.info("writer_a_holds_lock acquired row lock for product_id=%s", PRODUCT_ID)
            time.sleep(30)
        conn.commit()
        return {"product_id": PRODUCT_ID, "writer": "a", "lock_held_seconds": 30}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _writer_b_lock_timeout() -> dict[str, Any]:
    """Attempt the same row update through a separate connection and fail on lock timeout."""

    time.sleep(2)
    conn = _get_postgres_conn()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute("SET LOCAL lock_timeout = '5s'")
            cur.execute(
                f"UPDATE {PRODUCT_CATALOG_TABLE} "
                "SET product_id = product_id "
                "WHERE product_id = %s",
                (PRODUCT_ID,),
            )
        conn.commit()
        return {"product_id": PRODUCT_ID, "writer": "b", "lock_timeout": False}
    except Exception:
        conn.rollback()
        logger.exception("writer_b_lock_timeout failed as expected for product_id=%s", PRODUCT_ID)
        raise
    finally:
        conn.close()


def _collect_lock_evidence() -> dict[str, Any]:
    """Collect lightweight PostgreSQL lock evidence for the target relation."""

    conn = _get_postgres_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT locktype, mode, granted, COUNT(*) AS lock_count
                FROM pg_locks
                WHERE relation = %s::regclass
                GROUP BY locktype, mode, granted
                ORDER BY locktype, mode, granted
                """,
                (PRODUCT_CATALOG_TABLE,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return {
        "product_id": PRODUCT_ID,
        "lock_evidence": [
            {"locktype": row[0], "mode": row[1], "granted": row[2], "lock_count": row[3]}
            for row in rows
        ],
    }


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

    postgres_handlers = {
        "validate_product": _validate_product,
        "prepare_state": _prepare_state,
        "writer_a_holds_lock": _writer_a_holds_lock,
        "writer_b_lock_timeout": _writer_b_lock_timeout,
        "collect_lock_evidence": _collect_lock_evidence,
    }
    if task_kind in postgres_handlers:
        result = postgres_handlers[task_kind]()
        event = {
            "dag_id": dag_id,
            "task_name": task_name,
            "task_kind": task_kind,
            "incident_id": operator_config.get("incident_id"),
            **result,
        }
        logger.info("Product catalog PostgreSQL task completed: %s", event)
        return event

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

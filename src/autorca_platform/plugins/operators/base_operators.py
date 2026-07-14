"""Base operator builders for the AI AutoRCA platform."""

import logging
from typing import Any

from autorca_platform.factory.dynamic_mapping import build_mapped_task
from autorca_platform.factory.sensor_builder import resolve_sensor_params
from autorca_platform.metadata.models import TaskRow

logger = logging.getLogger("autorca_platform.plugins.operators.base_operators")


def autorca_noop_callable(task_name: str, dag_id: str, **_: Any) -> None:
    """Serializable no-op callable for metadata-backed placeholder tasks."""

    logger.info("Executing metadata-backed task %s in DAG %s", task_name, dag_id)


def autorca_branch_callable(branches: list[str], **_: Any) -> str | list[str]:
    """Serializable branch callable used until task-specific branch logic is configured."""

    if not branches:
        raise ValueError("Branch task has no downstream branches configured.")
    return branches[0]


def autorca_sensor_poke(**_: Any) -> bool:
    """Serializable sensor callable for generic placeholder sensors."""

    return True


def autorca_mapped_callable(x: Any) -> None:
    """Serializable callable for dynamically mapped placeholder work."""

    logger.info("Executing mapped slice %s", x)


class EmptyOperatorBuilder:
    """Builder for Airflow EmptyOperator."""

    def build(self, metadata: TaskRow) -> Any:
        """Build an EmptyOperator.

        Args:
            metadata: Task configuration metadata.

        Returns:
            Airflow EmptyOperator instance.
        """

        try:
            from airflow.providers.standard.operators.empty import EmptyOperator
        except ImportError:
            try:
                from airflow.operators.empty import EmptyOperator
            except ImportError:

                class EmptyOperator:  # type: ignore[no-redef]
                    """Mock EmptyOperator if Airflow is not present."""

                    def __init__(self, **kwargs: Any) -> None:
                        for k, v in kwargs.items():
                            setattr(self, k, v)

        kwargs = {
            "task_id": metadata.task_name,
            "trigger_rule": metadata.trigger_rule,
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return EmptyOperator(**kwargs)


class PythonOperatorBuilder:
    """Builder for Airflow PythonOperator."""

    def build(self, metadata: TaskRow) -> Any:
        """Build a PythonOperator.

        Args:
            metadata: Task configuration metadata.

        Returns:
            Airflow PythonOperator instance.
        """

        try:
            from airflow.providers.standard.operators.python import PythonOperator
        except ImportError:
            try:
                from airflow.operators.python import PythonOperator
            except ImportError:

                class PythonOperator:  # type: ignore[no-redef]
                    """Mock PythonOperator if Airflow is not present."""

                    def __init__(self, **kwargs: Any) -> None:
                        for k, v in kwargs.items():
                            setattr(self, k, v)

        kwargs = {
            "task_id": metadata.task_name,
            "python_callable": autorca_noop_callable,
            "op_kwargs": {"task_name": metadata.task_name, "dag_id": metadata.dag_id},
            "trigger_rule": metadata.trigger_rule,
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return PythonOperator(**kwargs)


class BranchPythonOperatorBuilder:
    """Builder for Airflow BranchPythonOperator."""

    def build(self, metadata: TaskRow) -> Any:
        """Build a BranchPythonOperator.

        Args:
            metadata: Task configuration metadata.

        Returns:
            Airflow BranchPythonOperator instance.
        """

        try:
            from airflow.providers.standard.operators.python import BranchPythonOperator
        except ImportError:
            try:
                from airflow.operators.python import BranchPythonOperator
            except ImportError:

                class BranchPythonOperator:  # type: ignore[no-redef]
                    """Mock BranchPythonOperator if Airflow is not present."""

                    def __init__(self, **kwargs: Any) -> None:
                        for k, v in kwargs.items():
                            setattr(self, k, v)
        kwargs = {
            "task_id": metadata.task_name,
            "python_callable": autorca_branch_callable,
            "op_kwargs": {"branches": list(metadata.downstream_tasks)},
            "trigger_rule": metadata.trigger_rule,
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return BranchPythonOperator(**kwargs)


class ExternalTaskSensorBuilder:
    """Builder for Airflow ExternalTaskSensor."""

    def build(self, metadata: TaskRow) -> Any:
        """Build an ExternalTaskSensor.

        Args:
            metadata: Task configuration metadata.

        Returns:
            Airflow ExternalTaskSensor instance.
        """

        try:
            from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
        except ImportError:
            try:
                from airflow.sensors.external_task import ExternalTaskSensor
            except ImportError:

                class ExternalTaskSensor:  # type: ignore[no-redef]
                    """Mock ExternalTaskSensor if Airflow is not present."""

                    def __init__(self, **kwargs: Any) -> None:
                        for k, v in kwargs.items():
                            setattr(self, k, v)

        params = resolve_sensor_params(metadata.task_name, metadata.dependencies)
        kwargs = {
            "task_id": metadata.task_name,
            "trigger_rule": metadata.trigger_rule,
            **params,
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return ExternalTaskSensor(**kwargs)


class SensorBuilder:
    """Builder for Sensor (reschedule mode, bounded timeout) or generic sensors."""

    def build(self, metadata: TaskRow) -> Any:
        """Build a custom sensor operator.

        Args:
            metadata: Task configuration metadata.

        Returns:
            Sensor operator instance.
        """

        try:
            from airflow.providers.standard.sensors.python import PythonSensor
        except ImportError:
            try:
                from airflow.sensors.python import PythonSensor

            except ImportError:

                class PythonSensor:  # type: ignore[no-redef]
                    """Mock sensor operator if Airflow is not present."""

                    def __init__(self, python_callable: Any, **kwargs: Any) -> None:
                        self.python_callable = python_callable
                        for k, v in kwargs.items():
                            setattr(self, k, v)

        kwargs = {
            "task_id": metadata.task_name,
            "trigger_rule": metadata.trigger_rule,
            "mode": "reschedule",
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return PythonSensor(python_callable=autorca_sensor_poke, **kwargs)


class SnowflakeOperatorBuilder:
    """Builder for Snowflake/Postgres/common SQL tasks."""

    def build(self, metadata: TaskRow) -> Any:
        """Build a SQL operator from task metadata.

        Args:
            metadata: Task configuration metadata.

        Returns:
            SQL operator instance.
        """

        try:
            from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
        except ImportError:
            try:
                from airflow.providers.standard.operators.python import PythonOperator

            except ImportError:
                try:
                    from airflow.operators.python import PythonOperator

                except ImportError:

                    class PythonOperator:  # type: ignore[no-redef]
                        """Mock PythonOperator if Airflow is not present."""

                        def __init__(self, python_callable: Any, **kwargs: Any) -> None:
                            self.python_callable = python_callable
                            for k, v in kwargs.items():
                                setattr(self, k, v)

            kwargs = {
                "task_id": metadata.task_name,
                "python_callable": autorca_noop_callable,
                "op_kwargs": {
                    "task_name": metadata.task_name,
                    "dag_id": metadata.dag_id,
                    "operator_config": metadata.operator_config,
                },
                "trigger_rule": metadata.trigger_rule,
            }
            if metadata.parallel_group:
                kwargs["pool"] = metadata.parallel_group

            return PythonOperator(**kwargs)

        conn_id = str(metadata.operator_config.get("conn_id", "snowflake_default"))
        sql = str(
            metadata.operator_config.get(
                "sql",
                f"SELECT 1 AS autorca_probe, '{metadata.dag_id}' AS dag_id, "
                f"'{metadata.task_name}' AS task_name",
            )
        )
        kwargs = {
            "task_id": metadata.task_name,
            "sql": sql,
            "conn_id": conn_id,
            "trigger_rule": metadata.trigger_rule,
        }
        if metadata.parallel_group:
            kwargs["pool"] = metadata.parallel_group

        return SQLExecuteQueryOperator(**kwargs)


class MappedPythonOperatorBuilder:
    """Builder for dynamically mapped PythonOperator tasks."""

    def build(self, metadata: TaskRow) -> Any:
        """Build a dynamically mapped PythonOperator.

        Args:
            metadata: Task configuration metadata.

        Returns:
            Mapped PythonOperator object.
        """

        try:
            from airflow.providers.standard.operators.python import PythonOperator
        except ImportError:
            try:
                from airflow.operators.python import PythonOperator
            except ImportError:

                class PythonOperator:  # type: ignore[no-redef]
                    """Mock PythonOperator supporting partial/expand calls."""

                    @classmethod
                    def partial(cls, **kwargs: Any) -> Any:
                        class PartialOperator:
                            def expand(self, **ex_kwargs: Any) -> Any:
                                return PythonOperator(**kwargs)

                        return PartialOperator()

                    def __init__(self, **kwargs: Any) -> None:
                        for k, v in kwargs.items():
                            setattr(self, k, v)

        return build_mapped_task(
            operator_class=PythonOperator,
            task_name=metadata.task_name,
            dag=None,
            trigger_rule=metadata.trigger_rule,
            pool=metadata.parallel_group,
            python_callable=autorca_mapped_callable,
        )

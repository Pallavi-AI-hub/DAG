"""Operators package to register task builders in the plugin registry."""

from autorca_platform.core.registry import get_default_registry
from autorca_platform.plugins.operators.base_operators import (
    BranchPythonOperatorBuilder,
    EmptyOperatorBuilder,
    ExternalTaskSensorBuilder,
    MappedPythonOperatorBuilder,
    PythonOperatorBuilder,
    SensorBuilder,
    SnowflakeOperatorBuilder,
)

empty_builder = EmptyOperatorBuilder()
python_builder = PythonOperatorBuilder()
branch_builder = BranchPythonOperatorBuilder()
sensor_ext_builder = ExternalTaskSensorBuilder()
sensor_generic_builder = SensorBuilder()
snowflake_builder = SnowflakeOperatorBuilder()
mapped_builder = MappedPythonOperatorBuilder()

TASK_TYPE_MAPPING = {
    "EmptyOperator": empty_builder,
    "EmptyOperator (fan-in)": empty_builder,
    "ExternalTaskSensor": sensor_ext_builder,
    "Sensor (reschedule mode, bounded timeout)": sensor_generic_builder,
    "BranchPythonOperator": branch_builder,
    "SnowflakeOperator (MERGE)": snowflake_builder,
    "SnowflakeOperator/MinIO writer": snowflake_builder,
    "PythonOperator (dynamic task mapping)": mapped_builder,
    "PythonOperator.expand (chunked, dynamic task mapping)": mapped_builder,
    "PythonOperator.expand (dynamic task mapping, dedicated pool)": mapped_builder,
    "PythonOperator.expand (dynamic task mapping, exponential backoff retries)": mapped_builder,
    "PythonOperator": python_builder,
    "PythonOperator (API/DB extract)": python_builder,
    "PythonOperator (AutoRCA anomaly hook)": python_builder,
    "PythonOperator (AutoRCA callback)": python_builder,
    "PythonOperator (AutoRCA cascade-RCA hook)": python_builder,
    "PythonOperator (AutoRCA congestion hook)": python_builder,
    "PythonOperator (AutoRCA resource-exhaustion hook)": python_builder,
    "PythonOperator (Datadog custom metric + Teams)": python_builder,
    "PythonOperator (Datadog pool.open_slots check)": python_builder,
    "PythonOperator (Teams + AutoRCA hang-detection hook)": python_builder,
    "PythonOperator (Teams Adaptive Card + RCA summary)": python_builder,
    "PythonOperator (Teams Adaptive Card)": python_builder,
    "PythonOperator (Teams Adaptive Card, P1)": python_builder,
    "PythonOperator (Teams notify)": python_builder,
    "PythonOperator (chunked fallback)": python_builder,
    "PythonOperator (circuit breaker trip)": python_builder,
    "PythonOperator (degraded-mode processing)": python_builder,
    "PythonOperator (fallback trigger)": python_builder,
    "PythonOperator (fan-in)": python_builder,
    "PythonOperator (handshake/reachability check)": python_builder,
    "PythonOperator (memory/CPU budget estimate)": python_builder,
    "PythonOperator (partition 1)": python_builder,
    "PythonOperator (partition 2)": python_builder,
    "PythonOperator (partition 3)": python_builder,
    "PythonOperator (partition extract)": python_builder,
    "PythonOperator (resource requests/limits set)": python_builder,
    "PythonOperator (scale_workers)": python_builder,
    "PythonOperator (state checkpoint)": python_builder,
    "PythonOperator/SQLOperator": python_builder,
    "PythonOperator/SQLOperator (heavy compute)": python_builder,
}


def register_operators() -> None:
    """Register all task builder mappings into the default plugin registry."""

    registry = get_default_registry()
    for task_type, builder in TASK_TYPE_MAPPING.items():
        registry.register(
            category="task_builder",
            name=task_type,
            plugin=builder,
            description=f"Task builder for {task_type}",
            replace=True,
        )


register_operators()

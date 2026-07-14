"""Dependency graph wiring and cycle detection for constructed DAGs."""

from collections import defaultdict
from typing import Any

from autorca_platform.core.exceptions import AutoRCABaseException
from autorca_platform.metadata.models import TaskRow


class DependencyCycleError(AutoRCABaseException):
    """Raised when a circular dependency is detected in the DAG structure."""


class DependencyResolver:
    """Wire task dependencies and detect circular references."""

    def detect_cycles(self, task_rows: tuple[TaskRow, ...]) -> None:
        """Scan task metadata for circular dependencies before building.

        Args:
            task_rows: Sequence of task configuration metadata.

        Raises:
            DependencyCycleError: If a cycle is detected.
        """

        graph = defaultdict(list)
        all_tasks = set()

        for row in task_rows:
            all_tasks.add(row.task_name)
            for upstream in row.upstream_tasks:
                graph[upstream].append(row.task_name)
            for downstream in row.downstream_tasks:
                graph[row.task_name].append(downstream)

        state = {node: 0 for node in all_tasks}  # 0=unvisited, 1=visiting, 2=visited
        parent: dict[str, str] = {}

        def dfs(u: str) -> list[str] | None:
            state[u] = 1
            for v in graph.get(u, []):
                if v not in all_tasks:
                    continue
                if state[v] == 1:
                    # Found a cycle, reconstruct it
                    cycle = [v, u]
                    curr = u
                    while curr != v and curr in parent:
                        curr = parent[curr]
                        cycle.append(curr)
                    cycle.reverse()
                    return cycle
                elif state[v] == 0:
                    parent[v] = u
                    cycle = dfs(v)
                    if cycle:
                        return cycle
            state[u] = 2
            return None

        for node in all_tasks:
            if state[node] == 0:
                cycle = dfs(node)
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    raise DependencyCycleError(
                        f"Circular dependency detected: {cycle_str}"
                    )

    def wire_dependencies(self, tasks: dict[str, Any], task_rows: tuple[TaskRow, ...]) -> None:
        """Establish upstream and downstream relationships between Airflow task instances.

        Args:
            tasks: Dict mapping task name to instantiated Airflow operator object.
            task_rows: Sequence of task metadata rows.
        """

        for row in task_rows:
            task = tasks.get(row.task_name)
            if not task:
                continue

            for upstream_name in row.upstream_tasks:
                upstream_task = tasks.get(upstream_name)
                if upstream_task:
                    self._link(upstream_task, task)

            for downstream_name in row.downstream_tasks:
                downstream_task = tasks.get(downstream_name)
                if downstream_task:
                    self._link(task, downstream_task)

    def _link(self, upstream_task: Any, downstream_task: Any) -> None:
        """Link two tasks, including lightweight local mocks when Airflow is absent."""

        try:
            upstream_task >> downstream_task
            return
        except TypeError:
            pass

        upstream_downstream = getattr(upstream_task, "downstream_task_ids", set())
        downstream_upstream = getattr(downstream_task, "upstream_task_ids", set())
        upstream_downstream.add(downstream_task.task_id)
        downstream_upstream.add(upstream_task.task_id)
        upstream_task.downstream_task_ids = upstream_downstream
        downstream_task.upstream_task_ids = downstream_upstream

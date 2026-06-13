"""
Workflow Engine — parses workflow DAGs, performs topological sort,
and executes nodes with parallel execution of independent nodes.
"""
import re
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, Optional

from executor_registry import ExecutorRegistry
from executors.base import WorkflowExecutionError

# Max number of parallel node executions
MAX_PARALLEL = 6


class WorkflowEngine:
    """Core engine for workflow parsing and execution with parallel support."""

    def __init__(self, registry: ExecutorRegistry):
        self.registry = registry

    def parse_workflow(self, nodes: list[dict], edges: list[dict]) -> list[str]:
        """
        Build directed graph, detect cycles via Kahn's algorithm,
        return topologically sorted node IDs.
        """
        node_ids = {n["id"] for n in nodes}
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}

        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            if src in node_ids and tgt in node_ids:
                adj[src].append(tgt)
                in_degree[tgt] += 1

        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        sorted_ids = []

        while queue:
            current = queue.popleft()
            sorted_ids.append(current)
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_ids) != len(node_ids):
            remaining = node_ids - set(sorted_ids)
            raise ValueError(
                f"Cycle detected in workflow! Nodes involved: {', '.join(sorted(remaining))}"
            )

        # Warn about isolated nodes
        has_downstream = {e["source"] for e in edges}
        has_upstream = {e["target"] for e in edges}
        for nid in node_ids:
            if nid not in has_downstream and nid not in has_upstream:
                node = next((n for n in nodes if n["id"] == nid), None)
                if node and node.get("type") not in ("schedule_trigger",):
                    print(f"WARNING: Isolated node detected: {nid} ({node.get('type')})")

        return sorted_ids

    def _get_execution_levels(self, nodes: list[dict], edges: list[dict]) -> list[list[str]]:
        """
        Group nodes into execution levels.
        Nodes in the same level have no dependencies between them and can run in parallel.
        """
        node_ids = {n["id"] for n in nodes}
        node_map = {n["id"]: n for n in nodes}

        # Build dependency graph
        deps: dict[str, set[str]] = {nid: set() for nid in node_ids}  # nid -> upstream nids
        children: dict[str, set[str]] = {nid: set() for nid in node_ids}

        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            if src in node_ids and tgt in node_ids:
                deps[tgt].add(src)
                children[src].add(tgt)

        # BFS to assign levels
        levels = []
        remaining = set(node_ids)

        while remaining:
            # Nodes with all deps satisfied (or no deps) can run now
            ready = {nid for nid in remaining if deps[nid].issubset(node_ids - remaining)}

            if not ready:
                # Should not happen if no cycles, but break to avoid infinite loop
                break

            levels.append(list(ready))
            remaining -= ready

        return levels

    def execute(
        self,
        nodes: list[dict],
        edges: list[dict],
        execution_id: int,
        log_callback: Optional[Callable] = None,
    ) -> dict:
        """
        Execute the workflow with parallel execution of independent nodes.

        Returns:
            dict with status, context, failed_node
        """
        context: dict[str, dict] = {}
        node_map = {n["id"]: n for n in nodes}

        def log(node_id: str, level: str, message: str):
            if log_callback:
                try:
                    log_callback(node_id, level, message)
                except Exception:
                    pass

        # Parse execution order
        try:
            sorted_ids = self.parse_workflow(nodes, edges)
        except ValueError as e:
            log("engine", "error", str(e))
            return {"status": "failed", "context": context, "failed_node": None, "error": str(e)}

        # Get parallel execution levels
        levels = self._get_execution_levels(nodes, edges)

        log("engine", "info",
            f"Execution plan: {len(levels)} stages, "
            f"{len(sorted_ids)} nodes (max parallel: {MAX_PARALLEL})")

        # Build upstream dependency map
        upstream_map: dict[str, list[str]] = {nid: [] for nid in node_map}
        for edge in edges:
            if edge["target"] in upstream_map:
                upstream_map[edge["target"]].append(edge["source"])

        failed_node = None

        # Execute level by level (nodes within a level run in parallel)
        for level_idx, level_nodes in enumerate(levels):
            level_name = f"Stage {level_idx + 1}/{len(levels)}"
            parallel_nodes = [nid for nid in level_nodes if nid in node_map]
            log("engine", "info",
                f"{level_name}: parallel execution of {len(parallel_nodes)} node(s): "
                f"{', '.join(parallel_nodes)}")

            if len(parallel_nodes) <= 1:
                # Sequential path — single node
                nid = parallel_nodes[0] if parallel_nodes else None
                if not nid:
                    continue
                node = node_map[nid]
                result = self._execute_one_node(
                    node, upstream_map, context, log
                )
                context[nid] = result
                if result.get("status") == "failed":
                    failed_node = nid
                    break
            else:
                # Parallel path — multiple independent nodes
                with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL, len(parallel_nodes))) as pool:
                    futures = {}
                    for nid in parallel_nodes:
                        node = node_map[nid]
                        futures[pool.submit(
                            self._execute_one_node, node, upstream_map, context, log
                        )] = nid

                    for future in futures:
                        nid = futures[future]
                        try:
                            result = future.result()
                            context[nid] = result
                            if result.get("status") == "failed":
                                failed_node = nid
                        except Exception as e:
                            context[nid] = {
                                "status": "failed",
                                "data": None,
                                "error_code": "ENGINE_ERROR",
                                "error": str(e),
                            }
                            failed_node = nid
                            log(nid, "error", f"Engine error: {e}")

                # If any node in this parallel stage failed, stop
                if failed_node:
                    break

        # Determine final status
        if failed_node:
            log("engine", "warn", f"Workflow stopped at failed node: {failed_node}")
            return {
                "status": "partial_failure" if any(
                    c.get("status") == "success" for c in context.values()
                ) else "failed",
                "context": context,
                "failed_node": failed_node,
            }

        log("engine", "info",
            f"Workflow completed successfully "
            f"({len([c for c in context.values() if c.get('status') == 'success'])}/"
            f"{len(sorted_ids)} nodes)")
        return {"status": "completed", "context": context, "failed_node": None}

    def _execute_one_node(
        self, node: dict, upstream_map: dict, context: dict, log: Callable
    ) -> dict:
        """Execute a single node with timeout support."""
        nid = node["id"]
        node_type = node.get("type", "unknown")
        node_config = node.get("config", {})
        timeout_seconds = node_config.get("_timeout", 60)

        log(nid, "info", f"[start] {node_type}")

        # Collect upstream data
        upstream_data = {}
        for upstream_id in upstream_map.get(nid, []):
            if upstream_id in context:
                upstream_data[upstream_id] = context[upstream_id]

        # Resolve config expressions
        resolved_config = self._resolve_config(node_config, context)

        # Get executor
        try:
            executor = self.registry.get(node_type)
        except KeyError:
            log(nid, "error", f"No executor for type: {node_type}")
            return {"status": "failed", "data": None, "error_code": "UNKNOWN_TYPE", "error": f"No executor for {node_type}"}

        # Execute with timeout
        start = time.time()
        try:
            # Use ThreadPoolExecutor to enforce timeout
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(executor.execute, resolved_config, upstream_data)
                try:
                    result = future.result(timeout=timeout_seconds)
                except FutureTimeout:
                    elapsed = time.time() - start
                    log(nid, "error", f"Timeout after {elapsed:.1f}s (limit: {timeout_seconds}s)")
                    return {
                        "status": "failed",
                        "data": None,
                        "error_code": "TIMEOUT",
                        "error": f"Execution timed out after {timeout_seconds}s",
                    }
        except WorkflowExecutionError as e:
            log(nid, "error", f"[{e.error_code}] {e.message}")
            return {"status": "failed", "data": None, "error_code": e.error_code, "error": e.message}
        except Exception as e:
            log(nid, "error", f"Unexpected: {e}")
            return {"status": "failed", "data": None, "error_code": "UNKNOWN", "error": str(e)}

        elapsed = time.time() - start
        if result.get("status") == "success":
            log(nid, "info", f"[done] {elapsed:.1f}s")
        else:
            log(nid, "error", f"[failed] {result.get('error', 'Unknown')}")

        return result

    def _resolve_config(self, config: dict, context: dict) -> dict:
        """Recursively resolve ${node_id.field} expressions in config values."""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_expressions(value, context)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_config(value, context)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_config(item, context) if isinstance(item, dict)
                    else self._resolve_expressions(item, context) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                resolved[key] = value
        return resolved

    def _resolve_expressions(self, value: str, context: dict) -> str:
        """Replace ${node_id.field.path} patterns with actual values from context."""
        pattern = re.compile(r'\$\{(\w+)\.(.+?)\}')

        def replacer(match):
            nid = match.group(1)
            field_path = match.group(2)
            if nid in context:
                resolved = self._get_nested(context[nid], field_path)
                if resolved is not None:
                    return str(resolved)
            return match.group(0)

        return pattern.sub(replacer, value)

    @staticmethod
    def _get_nested(data, path: str):
        """Access nested dict/list by dot/bracket path."""
        parts = re.split(r'\.|\[|\]', path)
        current = data
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part.isdigit():
                if isinstance(current, list):
                    idx = int(part)
                    if idx < len(current):
                        current = current[idx]
                    else:
                        return None
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

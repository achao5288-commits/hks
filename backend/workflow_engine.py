"""
Workflow Engine — parses workflow DAGs, performs topological sort,
and executes nodes in order with dependency data passing.
"""
import re
from collections import deque
from typing import Callable, Optional
from executor_registry import ExecutorRegistry
from executors.base import WorkflowExecutionError


class WorkflowEngine:
    """Core engine for workflow parsing and execution."""

    def __init__(self, registry: ExecutorRegistry):
        self.registry = registry

    def parse_workflow(self, nodes: list[dict], edges: list[dict]) -> list[str]:
        """
        Build a directed graph from nodes and edges, detect cycles via Kahn's algorithm,
        return topologically sorted node IDs.

        Raises ValueError if a cycle is detected.
        Prints warnings for isolated nodes.
        """
        node_ids = {n["id"] for n in nodes}

        # Build adjacency list and in-degree map
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}

        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            if src not in node_ids or tgt not in node_ids:
                continue
            adj[src].append(tgt)
            in_degree[tgt] += 1

        # Kahn's algorithm for topological sort AND cycle detection
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
            # Cycle detected
            remaining = node_ids - set(sorted_ids)
            raise ValueError(
                f"Cycle detected in workflow! Nodes involved: {', '.join(sorted(remaining))}"
            )

        # Detect isolated nodes (no upstream AND no downstream connections)
        has_upstream = {e["target"] for e in edges}
        has_downstream = {e["source"] for e in edges}
        for nid in node_ids:
            if nid not in has_upstream and nid not in has_downstream:
                node = next((n for n in nodes if n["id"] == nid), None)
                if node and node.get("type") not in ("schedule_trigger",):
                    print(f"WARNING: Isolated node detected: {nid} ({node.get('type')})")

        return sorted_ids

    def execute(
        self,
        nodes: list[dict],
        edges: list[dict],
        execution_id: int,
        log_callback: Optional[Callable] = None,
    ) -> dict:
        """
        Execute the workflow.

        Args:
            nodes: List of node definitions [{id, type, config, position}]
            edges: List of edge definitions [{id, source, target}]
            execution_id: Database execution record ID
            log_callback: Optional callback(node_id, level, message) for real-time logging

        Returns:
            dict with status, context, failed_node
        """
        context: dict[str, dict] = {}  # node_id -> execution result
        node_map = {n["id"]: n for n in nodes}

        def log(node_id: str, level: str, message: str):
            if log_callback:
                try:
                    log_callback(node_id, level, message)
                except Exception:
                    pass

        # Parse and get execution order
        try:
            sorted_ids = self.parse_workflow(nodes, edges)
        except ValueError as e:
            log("engine", "error", str(e))
            return {"status": "failed", "context": context, "failed_node": None, "error": str(e)}

        log("engine", "info", f"Execution order: {' -> '.join(sorted_ids)} ({len(sorted_ids)} nodes)")

        # Build dependency map: node_id -> list of upstream node IDs
        upstream_map: dict[str, list[str]] = {nid: [] for nid in sorted_ids}
        for edge in edges:
            if edge["target"] in upstream_map:
                upstream_map[edge["target"]].append(edge["source"])

        failed_node = None
        for node_id in sorted_ids:
            node = node_map.get(node_id)
            if not node:
                log(node_id, "warn", f"Node {node_id} not found in definition, skipping")
                continue

            node_type = node.get("type", "unknown")
            node_config = node.get("config", {})

            log(node_id, "info", f"Starting node [{node_type}]")

            # Collect upstream data
            upstream_data = {}
            for upstream_id in upstream_map.get(node_id, []):
                if upstream_id in context:
                    upstream_data[upstream_id] = context[upstream_id]

            # Resolve config expressions
            resolved_config = self._resolve_config(node_config, context)

            # Get executor and execute
            try:
                executor = self.registry.get(node_type)
            except KeyError:
                log(node_id, "error", f"No executor registered for type: {node_type}")
                failed_node = node_id
                break

            try:
                result = executor.execute(resolved_config, upstream_data)
            except WorkflowExecutionError as e:
                log(node_id, "error", f"Execution failed: [{e.error_code}] {e.message}")
                result = {"status": "failed", "data": None, "error_code": e.error_code, "error": e.message}
            except Exception as e:
                log(node_id, "error", f"Unexpected error: {str(e)}")
                result = {"status": "failed", "data": None, "error_code": "UNKNOWN", "error": str(e)}

            context[node_id] = result

            if result.get("status") == "failed":
                log(node_id, "error", f"Node failed: {result.get('error', 'Unknown error')}")
                # Check if this node should continue on failure
                continue_on_failure = node_config.get("continue_on_failure", False)
                if not continue_on_failure:
                    failed_node = node_id
                    break

            log(node_id, "info", f"Node completed successfully")

        # Determine final status
        if failed_node:
            log("engine", "warn", f"Workflow stopped at failed node: {failed_node}")
            return {
                "status": "partial_failure",
                "context": context,
                "failed_node": failed_node,
            }

        log("engine", "info", f"Workflow completed successfully ({len(sorted_ids)} nodes executed)")
        return {
            "status": "completed",
            "context": context,
            "failed_node": None,
        }

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
            node_id = match.group(1)
            field_path = match.group(2)
            if node_id in context:
                # Pass the full context entry so paths like data.items[0].title work
                resolved = self._get_nested(context[node_id], field_path)
                if resolved is not None:
                    return str(resolved)
            return match.group(0)

        return pattern.sub(replacer, value)

    @staticmethod
    def _get_nested(data, path: str):
        """Access nested dict/list by dot/bracket path like 'items[0].title'."""
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

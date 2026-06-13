"""
Base executor abstract class and custom exception.
All executors must inherit from BaseExecutor and implement execute() and get_config_schema().
"""
from abc import ABC, abstractmethod
from typing import Any


class WorkflowExecutionError(Exception):
    """Standardized exception for workflow execution failures."""

    def __init__(self, error_code: str, message: str, node_id: str = None):
        self.error_code = error_code
        self.message = message
        self.node_id = node_id
        super().__init__(f"[{error_code}] {message}")


class BaseExecutor(ABC):
    """Abstract base class for all node executors.

    Subclasses must implement:
      - execute(config, context) -> dict
      - get_config_schema() -> dict
    """

    @abstractmethod
    def execute(self, config: dict, context: dict) -> dict:
        """Execute the node's logic.

        Args:
            config: Node configuration object (from the workflow definition).
            context: Upstream data dictionary keyed by upstream node ID.

        Returns:
            dict with at minimum: {"status": "success"|"failed", "data": ...}

        Raises:
            WorkflowExecutionError: On unrecoverable failures.
        """
        ...

    @abstractmethod
    def get_config_schema(self) -> dict:
        """Return a JSON Schema describing this executor's configuration form.

        The frontend uses this to dynamically render config forms.
        Schema should include: type, properties (with title, description, type,
        default, enum if applicable), required list.
        """
        ...

    def validate_config(self, config: dict) -> bool:
        """Basic validation: check that all required fields from the schema exist."""
        schema = self.get_config_schema()
        required = schema.get("required", [])
        for field in required:
            if field not in config or config[field] is None:
                return False
        return True

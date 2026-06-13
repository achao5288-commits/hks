"""
Pydantic request/response schemas for the workflow automation API.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class PositionSchema(BaseModel):
    x: float = 0
    y: float = 0


class NodeSchema(BaseModel):
    id: str
    type: str
    config: dict = Field(default_factory=dict)
    position: PositionSchema = Field(default_factory=PositionSchema)


class EdgeSchema(BaseModel):
    id: str
    source: str
    target: str


class WorkflowCreate(BaseModel):
    name: str = "Untitled"
    description: str = ""
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str
    nodes_json: str
    edges_json: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ExecutionResponse(BaseModel):
    id: int
    workflow_id: int
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int = 0
    current_node: Optional[str] = None
    error: Optional[str] = None


class LogEntry(BaseModel):
    node_id: str
    level: str
    message: str
    timestamp: str


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class NodePresetCreate(BaseModel):
    node_type: str
    config_json: dict = Field(default_factory=dict)
    name: str


class NodePresetResponse(BaseModel):
    id: int
    node_type: str
    config_json: str
    name: str

"""
FastAPI application entry point for Workflow Automation.
Provides REST API + WebSocket endpoints for workflow CRUD, execution, and log streaming.
"""
import json
import uuid
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    create_tables, get_connection, engine,
    workflows_table, executions_table, execution_logs_table, node_presets_table,
)
from schemas import (
    WorkflowCreate, WorkflowResponse,
    TaskStatusResponse, ApiResponse,
    NodePresetCreate, NodePresetResponse,
)
from executor_registry import registry
from workflow_engine import WorkflowEngine
from ai_config import generate_config, generate_config_stream, generate_full_workflow


# ---- Application Setup ----

import asyncio as _asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global main_event_loop
    main_event_loop = _asyncio.get_running_loop()
    create_tables()
    # Insert demo presets if DB is empty
    _ensure_demo_data()
    yield
    # Cleanup
    engine.dispose()


app = FastAPI(
    title="Workflow Automation API",
    description="拖拽式工作流自动化平台 - 后端服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Global State ----

main_event_loop = None  # stored reference for cross-thread WS communication

engine_instance = WorkflowEngine(registry)
# task_id -> {status, progress, current_node, error, logs: list}
active_tasks: dict[str, dict] = {}
# task_id -> list of WebSocket connections
ws_connections: dict[str, list[WebSocket]] = {}
# Simple execution queue lock
execution_lock = threading.Lock()


# ---- Helpers ----

def _ensure_demo_data():
    """Insert demo preset data if none exists."""
    conn = get_connection()
    try:
        result = conn.execute(node_presets_table.select().limit(1))
        if result.fetchone() is None:
            presets = [
                {
                    "node_type": "web_crawler",
                    "name": "舆情新闻抓取",
                    "config_json": json.dumps({
                        "url": "http://localhost:5173/demo-news.html",
                        "selectors": [
                            {"name": "title", "selector": ".title"},
                            {"name": "summary", "selector": ".summary"},
                            {"name": "source", "selector": ".source"},
                            {"name": "time", "selector": ".time"},
                        ],
                        "wait_time": 2,
                        "scroll_to_bottom": False,
                    }),
                },
                {
                    "node_type": "data_process",
                    "name": "舆情数据清洗",
                    "config_json": json.dumps({
                        "field_mapping": {"time": "发布时间"},
                        "drop_duplicates": True,
                        "fill_missing": "N/A",
                        "sort_by": "发布时间",
                        "sort_ascending": False,
                    }),
                },
                {
                    "node_type": "excel_chart",
                    "name": "舆情日报Excel",
                    "config_json": json.dumps({
                        "sheet_name": "舆情日报",
                        "create_chart": True,
                        "chart_type": "bar",
                        "chart_title": "舆情来源统计",
                    }),
                },
                {
                    "node_type": "email_sender",
                    "name": "发送日报邮件",
                    "config_json": json.dumps({
                        "provider": "qq",
                        "subject": "舆情监控日报 - ${schedule_trigger.data.trigger_time}",
                        "body": "<h2>舆情监控日报</h2><p>以下是今日舆情汇总，详见附件。</p>",
                        "dry_run": True,
                    }),
                },
            ]
            for p in presets:
                conn.execute(node_presets_table.insert().values(**p))
            conn.commit()
            print("Demo presets inserted.")
    finally:
        conn.close()


def _row_to_dict(row):
    """Convert a SQLAlchemy Row to a dict."""
    if row is None:
        return None
    return dict(row._mapping)


def _log_execution(task_id: str, node_id: str, level: str, message: str):
    """Record a log entry for an active task."""
    now = datetime.now()
    entry = {
        "node_id": node_id,
        "level": level,
        "message": message,
        "timestamp": now,  # datetime object for DB; serialized for WS below
    }
    if task_id in active_tasks:
        active_tasks[task_id].setdefault("logs", []).append(entry)
    # Push to websocket clients (convert timestamp to string for JSON)
    if task_id in ws_connections and main_event_loop:
        ws_entry = {**entry, "timestamp": now.isoformat()}
        dead = []
        for ws in ws_connections[task_id]:
            try:
                asyncio.run_coroutine_threadsafe(ws.send_json(ws_entry), main_event_loop)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                ws_connections[task_id].remove(ws)
            except ValueError:
                pass


def _run_workflow(task_id: str, workflow_id: int, nodes: list, edges: list):
    """Background execution of a workflow (runs in a thread)."""
    with execution_lock:
        conn = get_connection()
        try:
            # Update execution status to running
            execution = conn.execute(
                executions_table.select().where(executions_table.c.task_id == task_id)
            ).fetchone()
            if not execution:
                return
            exec_id = execution._mapping["id"]
            conn.execute(
                executions_table.update()
                .where(executions_table.c.id == exec_id)
                .values(status="running", started_at=datetime.now())
            )
            conn.commit()

            active_tasks[task_id]["status"] = "running"
            active_tasks[task_id]["progress"] = 5

            # Execute
            result = engine_instance.execute(
                nodes=nodes,
                edges=edges,
                execution_id=exec_id,
                log_callback=lambda nid, level, msg: _log_execution(task_id, nid, level, msg),
            )

            # Save logs to DB
            for log_entry in active_tasks[task_id].get("logs", []):
                conn.execute(execution_logs_table.insert().values(
                    execution_id=exec_id,
                    node_id=log_entry["node_id"],
                    level=log_entry["level"],
                    message=log_entry["message"],
                    timestamp=log_entry["timestamp"],
                ))

            # Update final status
            final_status = "completed" if result["status"] == "completed" else "failed"
            conn.execute(
                executions_table.update()
                .where(executions_table.c.id == exec_id)
                .values(status=final_status, finished_at=datetime.now())
            )
            conn.commit()

            active_tasks[task_id]["status"] = final_status
            active_tasks[task_id]["progress"] = 100
            active_tasks[task_id]["current_node"] = result.get("failed_node")

        except Exception as e:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["error"] = str(e)
            active_tasks[task_id]["progress"] = 0
        finally:
            conn.close()


# ---- REST API Endpoints ----

@app.get("/api/health")
async def health_check():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}


# Workflow CRUD

@app.post("/api/workflows")
async def save_workflow(workflow: WorkflowCreate):
    """Save a workflow definition."""
    conn = get_connection()
    try:
        nodes_json = json.dumps([n.model_dump() for n in workflow.nodes], ensure_ascii=False)
        edges_json = json.dumps([e.model_dump() for e in workflow.edges], ensure_ascii=False)

        result = conn.execute(workflows_table.insert().values(
            name=workflow.name,
            description=workflow.description,
            nodes_json=nodes_json,
            edges_json=edges_json,
        ))
        conn.commit()
        workflow_id = result.inserted_primary_key[0]
        return {"code": 0, "message": "success", "data": {"id": workflow_id}}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"code": 1, "message": str(e), "data": None},
        )
    finally:
        conn.close()


@app.get("/api/workflows")
async def list_workflows():
    """List all saved workflows."""
    conn = get_connection()
    try:
        rows = conn.execute(workflows_table.select().order_by(workflows_table.c.updated_at.desc())).fetchall()
        workflows = []
        for row in rows:
            d = _row_to_dict(row)
            for date_field in ("created_at", "updated_at"):
                if d.get(date_field):
                    d[date_field] = str(d[date_field])
            workflows.append(d)
        return {"code": 0, "message": "success", "data": workflows}
    finally:
        conn.close()


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: int):
    """Get a single workflow by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            workflows_table.select().where(workflows_table.c.id == workflow_id)
        ).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"code": 1, "message": "Not found", "data": None})
        d = _row_to_dict(row)
        for date_field in ("created_at", "updated_at"):
            if d.get(date_field):
                d[date_field] = str(d[date_field])
        return {"code": 0, "message": "success", "data": d}
    finally:
        conn.close()


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: int):
    """Delete a workflow and its execution history."""
    conn = get_connection()
    try:
        row = conn.execute(
            workflows_table.select().where(workflows_table.c.id == workflow_id)
        ).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"code": 1, "message": "Not found", "data": None})

        # Delete related execution logs
        execs = conn.execute(
            executions_table.select().where(executions_table.c.workflow_id == workflow_id)
        ).fetchall()
        for ex in execs:
            ex_id = ex._mapping["id"]
            conn.execute(execution_logs_table.delete().where(execution_logs_table.c.execution_id == ex_id))
        conn.execute(executions_table.delete().where(executions_table.c.workflow_id == workflow_id))
        conn.execute(workflows_table.delete().where(workflows_table.c.id == workflow_id))
        conn.commit()
        return {"code": 0, "message": "success", "data": None}
    finally:
        conn.close()


# Workflow Execution

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: int):
    """Execute a saved workflow, returns task_id for polling."""
    conn = get_connection()
    try:
        row = conn.execute(
            workflows_table.select().where(workflows_table.c.id == workflow_id)
        ).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"code": 1, "message": "Workflow not found", "data": None})

        wf = _row_to_dict(row)
        nodes = json.loads(wf["nodes_json"])
        edges = json.loads(wf["edges_json"])

        task_id = str(uuid.uuid4())[:12]

        # Create execution record
        result = conn.execute(executions_table.insert().values(
            workflow_id=workflow_id,
            status="pending",
            task_id=task_id,
        ))
        conn.commit()

        # Initialize task state
        active_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "current_node": None,
            "error": None,
            "logs": [],
        }

        # Start background execution
        thread = threading.Thread(
            target=_run_workflow,
            args=(task_id, workflow_id, nodes, edges),
            daemon=True,
        )
        thread.start()

        return {"code": 0, "message": "success", "data": {"task_id": task_id}}
    finally:
        conn.close()


@app.get("/api/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Poll execution status by task_id."""
    task = active_tasks.get(task_id)
    if task is None:
        # Try DB lookup
        conn = get_connection()
        try:
            row = conn.execute(
                executions_table.select().where(executions_table.c.task_id == task_id)
            ).fetchone()
            if row is None:
                return JSONResponse(status_code=404, content={"code": 1, "message": "Task not found", "data": None})
            ex = _row_to_dict(row)
            return {
                "code": 0, "message": "success",
                "data": {
                    "task_id": task_id,
                    "status": ex["status"],
                    "progress": 100 if ex["status"] in ("completed", "failed") else 0,
                    "current_node": None,
                    "error": None,
                },
            }
        finally:
            conn.close()

    return {
        "code": 0, "message": "success",
        "data": {
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "current_node": task.get("current_node"),
            "error": task.get("error"),
        },
    }


# Executor Info

@app.get("/api/executors")
async def list_executors():
    """Get all registered executor types with their config schemas and display info."""
    schemas = registry.get_all_schemas()
    type_info = registry.get_type_info()
    # Merge
    result = []
    for info in type_info:
        typename = info["type"]
        info["config_schema"] = schemas.get(typename, {})
        result.append(info)
    return {"code": 0, "message": "success", "data": result}


# AI Config Generation

from pydantic import BaseModel as PydanticBaseModel

class AIConfigRequest(PydanticBaseModel):
    requirement: str
    node_type: str


@app.post("/api/ai/generate-config")
async def ai_generate_config(request: AIConfigRequest):
    """Generate node configuration from natural language requirement using AI."""
    if not request.requirement:
        return JSONResponse(status_code=400, content={"code": 1, "message": "requirement is required", "data": None})
    if not request.node_type:
        return JSONResponse(status_code=400, content={"code": 1, "message": "node_type is required", "data": None})

    schemas = registry.get_all_schemas()
    config_schema = schemas.get(request.node_type)
    if not config_schema:
        return JSONResponse(status_code=400, content={"code": 3, "message": f"Unknown node_type: {request.node_type}", "data": None})

    try:
        config = generate_config(request.requirement, request.node_type, config_schema)
        return {"code": 0, "message": "success", "data": {"config": config}}
    except ValueError as e:
        return JSONResponse(status_code=422, content={"code": 3, "message": str(e), "data": None})
    except ConnectionError as e:
        return JSONResponse(status_code=502, content={"code": 4, "message": str(e), "data": None})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 4, "message": str(e), "data": None})


@app.post("/api/ai/generate-config-stream")
async def ai_generate_config_stream(request: AIConfigRequest):
    """Streaming version — returns SSE (Server-Sent Events)."""
    from fastapi.responses import StreamingResponse

    if not request.requirement or not request.node_type:
        return JSONResponse(status_code=400, content={"code": 1, "message": "requirement and node_type are required", "data": None})

    schemas = registry.get_all_schemas()
    config_schema = schemas.get(request.node_type)
    if not config_schema:
        return JSONResponse(status_code=400, content={"code": 3, "message": f"Unknown node_type: {request.node_type}", "data": None})

    async def event_stream():
        try:
            for chunk in generate_config_stream(request.requirement, request.node_type, config_schema):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: __ERROR__{str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class AutoWorkflowRequest(PydanticBaseModel):
    requirement: str


@app.post("/api/ai/auto-workflow")
async def ai_auto_workflow(request: AutoWorkflowRequest):
    """Generate a complete workflow from natural language, save and return it."""
    if not request.requirement:
        return JSONResponse(status_code=400, content={"code": 1, "message": "requirement is required", "data": None})

    try:
        # AI generates full workflow design
        wf_design = generate_full_workflow(request.requirement)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"code": 3, "message": str(e), "data": None})
    except ConnectionError as e:
        return JSONResponse(status_code=502, content={"code": 4, "message": str(e), "data": None})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 4, "message": str(e), "data": None})

    # Convert to API format
    nodes_payload = []
    for n in wf_design.get("nodes", []):
        nodes_payload.append({
            "id": n["id"],
            "type": n["type"],
            "config": n.get("config", {}),
            "position": {"x": n.get("pos_x", 80), "y": n.get("pos_y", 120)},
        })

    edges_payload = []
    for e in wf_design.get("edges", []):
        edges_payload.append({
            "id": e.get("id", f"edge_{len(edges_payload)}"),
            "source": e["source"],
            "target": e["target"],
        })

    # Save to database
    conn = get_connection()
    try:
        result = conn.execute(workflows_table.insert().values(
            name=wf_design.get("name", "AI生成工作流"),
            description=wf_design.get("description", ""),
            nodes_json=json.dumps(nodes_payload, ensure_ascii=False),
            edges_json=json.dumps(edges_payload, ensure_ascii=False),
        ))
        conn.commit()
        wf_id = result.inserted_primary_key[0]
    finally:
        conn.close()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": wf_id,
            "name": wf_design.get("name", ""),
            "description": wf_design.get("description", ""),
            "nodes": nodes_payload,
            "edges": edges_payload,
        },
    }


# Node Presets

@app.get("/api/presets")
async def list_presets():
    """List all node configuration presets."""
    conn = get_connection()
    try:
        rows = conn.execute(node_presets_table.select()).fetchall()
        presets = [_row_to_dict(r) for r in rows]
        return {"code": 0, "message": "success", "data": presets}
    finally:
        conn.close()


@app.post("/api/presets")
async def create_preset(preset: NodePresetCreate):
    """Create a new node configuration preset."""
    conn = get_connection()
    try:
        result = conn.execute(node_presets_table.insert().values(
            node_type=preset.node_type,
            name=preset.name,
            config_json=json.dumps(preset.config_json, ensure_ascii=False),
        ))
        conn.commit()
        preset_id = result.inserted_primary_key[0]
        return {"code": 0, "message": "success", "data": {"id": preset_id}}
    finally:
        conn.close()


# WebSocket for Log Streaming

@app.websocket("/ws/tasks/{task_id}/logs")
async def websocket_logs(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time execution log streaming."""
    await websocket.accept()

    if task_id not in ws_connections:
        ws_connections[task_id] = []
    ws_connections[task_id].append(websocket)

    # Send existing logs (convert datetime to string for JSON)
    if task_id in active_tasks:
        for log_entry in active_tasks[task_id].get("logs", []):
            ts = log_entry.get("timestamp")
            ws_entry = {**log_entry, "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else ts}
            await websocket.send_json(ws_entry)

    try:
        while True:
            # Keep connection alive; logs are pushed by the execution thread
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if task_id in ws_connections:
            try:
                ws_connections[task_id].remove(websocket)
            except ValueError:
                pass  # already removed by dead-connection cleanup


# ---- Main Entry Point ----

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

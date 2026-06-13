"""
SQLAlchemy Core data models for Workflow Automation.
Uses raw SQLAlchemy Core (not ORM) for simplicity.
"""
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.sql import func
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'workflows.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
metadata = MetaData()

workflows_table = Table(
    "workflows", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False, default="Untitled"),
    Column("description", Text, default=""),
    Column("nodes_json", Text, nullable=False, default="[]"),
    Column("edges_json", Text, nullable=False, default="[]"),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

executions_table = Table(
    "executions", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("workflow_id", Integer, ForeignKey("workflows.id"), nullable=False),
    Column("status", String(32), nullable=False, default="pending"),
    Column("started_at", DateTime, nullable=True),
    Column("finished_at", DateTime, nullable=True),
    Column("task_id", String(64), unique=True, nullable=False),
)

execution_logs_table = Table(
    "execution_logs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("execution_id", Integer, ForeignKey("executions.id"), nullable=False),
    Column("node_id", String(64), nullable=False),
    Column("level", String(16), nullable=False, default="info"),
    Column("message", Text, default=""),
    Column("timestamp", DateTime, server_default=func.now()),
)

node_presets_table = Table(
    "node_presets", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("node_type", String(64), nullable=False),
    Column("config_json", Text, nullable=False, default="{}"),
    Column("name", String(255), nullable=False),
)


def create_tables():
    """Create all tables if they don't exist."""
    metadata.create_all(engine, checkfirst=True)


def get_connection():
    """Get a raw DBAPI connection for executing SQL."""
    return engine.connect()


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")

"""
SQL Executor Agent - runs validated SQL against PostgreSQL.
Enforces read-only policy: only SELECT allowed; blocks DROP, TRUNCATE, etc.
"""
from sqlmodel import Session
from sqlalchemy import text

from src.logger import agent_logger

BLOCKED_KEYWORDS = ["drop", "truncate", "alter", "insert", "update", "delete"]


class SQLExecutorAgent:
    """Executes SQL queries with safety validation and returns structured results."""

    def __init__(self, engine):
        self.engine = engine

    def execute(self, sql: str) -> dict:
        """Validate SQL, execute against database, return columns and rows."""
        self._validate_sql(sql)
        with Session(self.engine) as session:
            result = session.exec(text(sql))
            rows = result.fetchall()
            columns = result.keys()
        agent_logger.info("Executed query, returned %d rows", len(rows))
        return {
            "columns": list(columns),
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
        }

    def _validate_sql(self, sql: str) -> None:
        """Ensure SQL is read-only and single-statement."""
        normalized = sql.strip().lower()
        if not normalized.startswith("select"):
            raise ValueError("Only SELECT queries allowed.")
        if ";" in normalized[:-1]:
            raise ValueError("Multiple SQL statements detected.")
        for word in BLOCKED_KEYWORDS:
            if word in normalized:
                raise ValueError(f"Blocked keyword: {word}")

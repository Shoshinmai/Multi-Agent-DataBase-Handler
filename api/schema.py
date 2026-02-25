"""
Pydantic schemas for API request/response validation.
"""
from typing import Any, List

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Natural language query input."""

    query: str


class QueryResponse(BaseModel):
    """Structured response with SQL and result data."""

    sql: str
    columns: List[str]
    rows: List[List[Any]]
    row_count: int

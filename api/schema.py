from pydantic import BaseModel
from typing import List, Any, Optional


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    sql: str
    columns: List[str]
    rows: List[List[Any]]
    # result: Optional[dict]
    row_count: int

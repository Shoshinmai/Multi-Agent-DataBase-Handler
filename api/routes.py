"""
API routes for the natural language to SQL service.
"""
from fastapi import APIRouter, HTTPException

from api.schema import QueryRequest, QueryResponse
from graph import GraphState
from src.logger import api_logger

router = APIRouter()

# Injected at startup by main.py
graph = None


@router.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    """Execute natural language query through the agent pipeline."""
    try:
        api_logger.info("Query received: %s", request.query[:80])
        initial_state = GraphState(user_query=request.query)
        final_state = graph.invoke(initial_state)
        result = final_state.get("result")
        return QueryResponse(
            sql=final_state.get("sql"),
            columns=result["columns"],
            rows=result["rows"],
            row_count=result["row_count"],
        )
    except Exception as e:
        api_logger.exception("Query failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e

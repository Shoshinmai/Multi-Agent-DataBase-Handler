from fastapi import APIRouter, HTTPException
from api.schema import QueryRequest, QueryResponse
from graph import GraphState
# from graph import build_graph

router = APIRouter()

# graph is injected at startup
graph = None


@router.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    try:
        initial_state = GraphState(user_query=request.query)
        final_state = graph.invoke(initial_state)

        return QueryResponse(
            sql=final_state.get("sql"),
            columns=final_state.get("result")["columns"],
            rows=final_state.get("result")["rows"],
            # result=final_state.get("result"),
            row_count=final_state.get("result")['row_count'],
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

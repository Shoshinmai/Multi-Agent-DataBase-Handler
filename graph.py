"""
LangGraph pipeline: Intent → Date Resolver → SQL Generator → SQL Executor.
Orchestrates the multi-agent flow for natural language to SQL execution.
"""
from datetime import datetime, timedelta
from typing import Optional

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from src.agents.intent_agent import IntentState
from src.logger import app_logger


class GraphState(BaseModel):
    """State passed through the LangGraph pipeline."""

    user_query: str
    intent: Optional[IntentState] = None
    sql: Optional[str] = None
    result: Optional[dict] = None


def intent_node(state: GraphState, intent_agent):
    """Extract structured intent from user query using LLM."""
    intent = intent_agent.run(state.user_query)
    return state.model_copy(update={"intent": intent})


def sql_generator_node(state: GraphState, sql_generator):
    """Convert IntentState to SQL string."""
    sql = sql_generator.generate(state.intent)
    return state.model_copy(update={"sql": sql})


def sql_executor_node(state: GraphState, sql_executor):
    """Execute SQL and attach result to state."""
    result = sql_executor.execute(state.sql)
    return state.model_copy(update={"result": result})


def time_scope_resolver_node(state: GraphState) -> GraphState:
    """
    Resolve relative time expressions (LAST_MONTH, TODAY, etc.) into concrete dates.
    Mutates intent.filters in place.
    """
    if not state.intent:
        return state
    _resolve_intent(state.intent)
    return state


def _resolve_intent(intent: IntentState) -> None:
    """Recursively resolve time_scope in filters and subqueries."""
    today = datetime.today()

    for f in intent.filters:
        if f.time_scope:
            scope = f.time_scope.upper()
            if scope == "LAST_MONTH":
                first_day_this_month = today.replace(day=1)
                last_day_last_month = first_day_this_month - timedelta(days=1)
                first_day_last_month = last_day_last_month.replace(day=1)
                f.operator = "BETWEEN"
                f.value = (
                    first_day_last_month.strftime("%Y-%m-%d"),
                    last_day_last_month.strftime("%Y-%m-%d"),
                )
            elif scope == "LAST_WEEK":
                start_of_this_week = today - timedelta(days=today.weekday())
                end_of_last_week = start_of_this_week - timedelta(days=1)
                start_of_last_week = end_of_last_week - timedelta(days=6)
                f.operator = "BETWEEN"
                f.value = (
                    start_of_last_week.strftime("%Y-%m-%d"),
                    end_of_last_week.strftime("%Y-%m-%d"),
                )
            elif scope == "TODAY":
                f.operator = "="
                f.value = today.strftime("%Y-%m-%d")
            elif scope == "YESTERDAY":
                yesterday = today - timedelta(days=1)
                f.operator = "="
                f.value = yesterday.strftime("%Y-%m-%d")
            elif scope == "THIS_YEAR":
                start = today.replace(month=1, day=1)
                end = today.replace(month=12, day=31)
                f.operator = "BETWEEN"
                f.value = (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            elif scope == "LAST_7_DAYS":
                start = today - timedelta(days=7)
                f.operator = "BETWEEN"
                f.value = (start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
            f.time_scope = None

        if f.subquery:
            _resolve_intent(f.subquery)


def build_graph(intent_agent, sql_generator, sql_executor):
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(GraphState)
    graph.add_node("intent", lambda s: intent_node(s, intent_agent))
    graph.add_node("sql_generator", lambda s: sql_generator_node(s, sql_generator))
    graph.add_node("sql_executor", lambda s: sql_executor_node(s, sql_executor))
    graph.add_node("date_resolver", time_scope_resolver_node)

    graph.set_entry_point("intent")
    graph.add_edge("intent", "date_resolver")
    graph.add_edge("date_resolver", "sql_generator")
    graph.add_edge("sql_generator", "sql_executor")
    graph.add_edge("sql_executor", END)

    app_logger.info("LangGraph pipeline compiled")
    return graph.compile()

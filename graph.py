# graph/state.py
from typing import Optional
from pydantic import BaseModel
from src.agents.intent_agent import IntentState, llm
from langgraph.graph import StateGraph, END
from src.database import engine
from src.agents.intent_agent import IntentAgent
from src.agents.sql_generator import SQLGeneratorAgent
from src.agents.sql_executor import SQLExecutorAgent


class GraphState(BaseModel):
    user_query: str

    intent: Optional[IntentState] = None
    sql: Optional[str] = None
    result: Optional[dict] = None


def intent_node(state: GraphState, intent_agent):
    intent = intent_agent.run(state.user_query)
    return state.model_copy(update={"intent": intent})

# graph/nodes/sql_generator_node.py

def sql_generator_node(state: GraphState, sql_generator):
    sql = sql_generator.generate(state.intent)
    return state.model_copy(update={"sql": sql})


# graph/nodes/sql_executor_node.py

def sql_executor_node(state: GraphState, sql_executor):
    result = sql_executor.execute(state.sql)
    return state.model_copy(update={"result": result})





def build_graph(intent_agent, sql_generator, sql_executor):
    graph = StateGraph(GraphState)

    # Register nodes
    graph.add_node("intent", lambda s: intent_node(s, intent_agent))
    graph.add_node("sql_generator", lambda s: sql_generator_node(s, sql_generator))
    graph.add_node("sql_executor", lambda s: sql_executor_node(s, sql_executor))

    # Define flow
    graph.set_entry_point("intent")
    graph.add_edge("intent", "sql_generator")
    graph.add_edge("sql_generator", "sql_executor")
    graph.add_edge("sql_executor", END)

    return graph.compile()


from pprint import pprint

intent_agent = IntentAgent(llm)
sql_generator = SQLGeneratorAgent()
sql_executor = SQLExecutorAgent(engine)

# graph = build_graph(intent_agent, sql_generator, sql_executor)

# initial_state = GraphState(
#     # user_query="Show users who made more than the average purchase amount"
#     user_query="Show all the users"
# )

# final_state = graph.invoke(initial_state)
# print(final_state)
# print(final_state.get("sql"))
# pprint(final_state.get("result"))

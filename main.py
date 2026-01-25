from fastapi import FastAPI
from api.routes import router
from graph import build_graph

from src.agents.intent_agent import IntentAgent, llm
from src.agents.sql_generator import SQLGeneratorAgent
from src.agents.sql_executor import SQLExecutorAgent
from src.database import engine

# initialize agents
intent_agent = IntentAgent(llm)
sql_generator = SQLGeneratorAgent()
sql_executor = SQLExecutorAgent(engine)

# build langgraph
from api import routes
routes.graph = build_graph(
    intent_agent=intent_agent,
    sql_generator=sql_generator,
    sql_executor=sql_executor
)

app = FastAPI(title="Agentic SQL API")

app.include_router(router)

"""
FastAPI application entry point.
Wires agents, graph, and API routes for the natural language to SQL service.
"""
from fastapi import FastAPI

from api.routes import router
from graph import build_graph
from src.agents.intent_agent import IntentAgent, llm
from src.agents.sql_generator import SQLGeneratorAgent
from src.agents.sql_executor import SQLExecutorAgent
from src.database import engine
from src.schema_extractor import SchemaExtractor, format_schema_for_prompt
from src.logger import app_logger
from config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    raise ValueError(
        "Missing GEMINI_API_KEY or gemini_api_key. Set in .env (see .env.example)."
    )

# Initialize agents and schema context
sql_generator = SQLGeneratorAgent()
sql_executor = SQLExecutorAgent(engine)
schema_extractor = SchemaExtractor(engine)
schema_dict = schema_extractor.extract_schema()
schema_context = format_schema_for_prompt(schema_dict)
intent_agent = IntentAgent(llm, schema_context)

# Build LangGraph pipeline and inject into routes
from api import routes

routes.graph = build_graph(
    intent_agent=intent_agent,
    sql_generator=sql_generator,
    sql_executor=sql_executor,
)

app = FastAPI(title="Agentic SQL API")

app.include_router(router)


@app.get("/health")
def health():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "ok"}


@app.on_event("startup")
def startup_event():
    """Log application startup."""
    app_logger.info("Agentic SQL API started")

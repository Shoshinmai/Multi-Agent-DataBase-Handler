"""
Extracts database schema from PostgreSQL for LLM context.
Provides table and column metadata in a format suitable for prompt injection.
"""
from sqlmodel import Session
from sqlalchemy import text

from src.logger import agent_logger


class SchemaExtractor:
    """Extracts structured schema info from the database for intent extraction."""

    def __init__(self, engine):
        self.engine = engine

    def extract_schema(self) -> dict:
        """
        Returns structured schema: {table_name: {columns: [{name, type}, ...]}, ...}
        Queries information_schema for tables and columns in the public schema.
        """
        schema = {}
        with Session(self.engine) as session:
            tables_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """
            tables = session.exec(text(tables_query)).fetchall()

            for (table_name,) in tables:
                columns_query = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = :table;
                """
                stmt = text(columns_query).bindparams(table=table_name)
                columns = session.exec(stmt).fetchall()
                schema[table_name] = {
                    "columns": [{"name": col[0], "type": col[1]} for col in columns]
                }

        agent_logger.debug("Extracted schema for %d tables", len(schema))
        return schema


def format_schema_for_prompt(schema: dict) -> str:
    """Format schema dict as human-readable string for LLM prompts."""
    formatted = "Database Schema:\n\n"
    for table, info in schema.items():
        formatted += f"Table: {table}\n"
        for column in info["columns"]:
            formatted += f"- {column['name']} ({column['type']})\n"
        formatted += "\n"
    return formatted

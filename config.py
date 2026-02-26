"""
Application configuration loaded from environment variables.
Validates required settings at startup for production readiness.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_env(key: str, default: str | None = None, required: bool = True) -> str:
    """Get environment variable with optional validation."""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value or ""


# Database
DATABASE_URL = get_env("DATABASE_URL", required=False) or (
    "postgresql+psycopg2://postgres:2416@localhost:5432/sql-handler"
)
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# LLM (supports both GEMINI_API_KEY and gemini_api_key for backward compatibility)
GEMINI_API_KEY = get_env("GEMINI_API_KEY", required=False) or get_env(
    "gemini_api_key", required=False
)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

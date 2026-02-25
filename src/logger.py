"""
Centralized logging configuration for the application.
Provides structured logging with configurable levels for monitoring and debugging.
"""
import logging
import sys
from pathlib import Path

from config import LOG_LEVEL, LOG_FORMAT

# Log directory for file output
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Create and configure a logger with console and optional file output.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    formatter = logging.Formatter(LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler for persistence (app.log)
    if log_file is None:
        log_file = "app.log"
    file_path = LOG_DIR / log_file
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Module-level loggers for easy import
app_logger = setup_logger("app")
api_logger = setup_logger("api", "api.log")
agent_logger = setup_logger("agents", "agents.log")

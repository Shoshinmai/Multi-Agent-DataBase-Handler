"""
PostgreSQL database engine and session management.
Uses SQLModel (SQLAlchemy) for ORM and raw SQL execution.
"""
from sqlmodel import create_engine, SQLModel, Session

from config import DATABASE_URL, SQL_ECHO

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)


def init_db() -> None:
    """Create all tables defined in SQLModel metadata."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session for dependency injection."""
    with Session(engine) as session:
        yield session

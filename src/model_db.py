"""
SQLModel table definitions for the application.
User and Purchase models with proper relationships.
"""
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User table - stores customer information."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Purchase(SQLModel, table=True):
    """Purchase table - links to User via user_id foreign key."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    amount: float = Field(nullable=False)
    purchase_date: date = Field(nullable=False)

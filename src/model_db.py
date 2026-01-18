from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Purchase(SQLModel, table=True):   
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable= False)
    amount: float = Field(nullable=False)
    purchase_date: date = Field(nullable=False)

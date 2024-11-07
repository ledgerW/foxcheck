from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import AnyHttpUrl, validator
from datetime import datetime
import json
import os

from schemas import Reference


# Determine environment and set prefix
is_production = os.getenv("REPLIT_DEPLOYMENT") == "1"
print(f"Is production: {is_production}")
table_prefix = "prod_" if is_production else "dev_"
print(f"Table prefix: {table_prefix}")

def get_table_name(model_name: str) -> str:
    is_production = os.getenv("REPLIT_DEPLOYMENT") == "1"
    table_prefix = "prod_" if is_production else "dev_"
    return f"{table_prefix}{model_name}"


class User(SQLModel, table=True):
    __tablename__ = f"{table_prefix}user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)  # Added is_admin field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    articles: List["Article"] = Relationship(back_populates="user")


class Statement(SQLModel, table=True):
    __tablename__ = f"{table_prefix}statement"
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
    verdict: Optional[str] = Field(default=None)
    explanation: Optional[str] = Field(default=None)
    references: Optional[str] = Field(default="[]")  # Store as JSON string in the database
    created_at: datetime = Field(default_factory=datetime.utcnow)
    article_id: Optional[int] = Field(default=None, foreign_key=f"{get_table_name('article')}.id")
    user_id: Optional[int] = Field(default=None, foreign_key=f"{get_table_name('user')}.id")

    article: Optional["Article"] = Relationship(back_populates="statements")

    @validator("references", pre=True, always=True)
    def parse_references(cls, v):
        # If references is a JSON string, parse it to a list
        if isinstance(v, str):
            try:
                return json.loads(v)  # Convert JSON string to list
            except json.JSONDecodeError:
                return []  # Return empty list if JSON parsing fails
        return v or []

    def set_references(self, references: List[dict]) -> None:
        # Converts a list of dictionaries to a JSON string for storage
        if references is None:
            self.references = '[]'
        else:
            try:
                self.references = json.dumps(references)
            except (TypeError, ValueError):
                self.references = '[]'


class Article(SQLModel, table=True):
    __tablename__ = f"{table_prefix}article"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    text: str
    date: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key=f"{get_table_name('user')}.id")
    is_active: bool = Field(default=True)
    domain: Optional[str] = Field(max_length=500, unique=True, index=True)
    links: Optional[str] = Field(default="[]")  # Store as JSON string
    authors: Optional[str] = Field(max_length=1000)
    publication_date: Optional[datetime]
    extraction_date: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="articles")
    statements: List[Statement] = Relationship(back_populates="article", sa_relationship_kwargs={"lazy": "joined"})
    
    @validator("links", pre=True, always=True)
    def parse_links(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    def set_links(self, links: List[str]) -> None:
        if links is None:
            self.links = '[]'
        else:
            try:
                self.links = json.dumps(links)
            except (TypeError, ValueError):
                self.links = '[]'

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import json

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Statement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
    verdict: Optional[str] = Field(default=None)
    explanation: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    article_id: Optional[int] = Field(default=None, foreign_key="article.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    article: Optional["Article"] = Relationship(back_populates="statements")
    references: List["Reference"] = Relationship(back_populates="statement")

class Article(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    text: str
    date: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")
    is_approved: bool = Field(default=False)
    domain: Optional[str] = Field(max_length=500)
    links: Optional[str]  # Stores JSON
    authors: Optional[str] = Field(max_length=1000)
    publication_date: Optional[datetime]
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    
    statements: List[Statement] = Relationship(back_populates="article")
    references: List["Reference"] = Relationship(back_populates="article")

    def set_links(self, links: List[str]) -> None:
        self.links = json.dumps(links)

    def get_links(self) -> List[str]:
        return json.loads(self.links) if self.links else []

class Reference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    title: Optional[str]
    content: str
    context: Optional[str]
    article_id: Optional[int] = Field(default=None, foreign_key="article.id")
    statement_id: Optional[int] = Field(default=None, foreign_key="statement.id")
    
    article: Optional[Article] = Relationship(back_populates="references")
    statement: Optional[Statement] = Relationship(back_populates="references")

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
    articles: List["Article"] = Relationship(back_populates="user")

class Statement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)
    verdict: Optional[str] = Field(default=None)
    explanation: Optional[str] = Field(default=None)
    references: Optional[str] = Field(default=None)  # Stores JSON list of references
    created_at: datetime = Field(default_factory=datetime.utcnow)
    article_id: Optional[int] = Field(default=None, foreign_key="article.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    article: Optional["Article"] = Relationship(back_populates="statements")

    def get_references(self) -> List[dict]:
        """Get the list of references from JSON string"""
        if not self.references:
            return []
        return json.loads(self.references)

    def set_references(self, references: List[dict]) -> None:
        """Set references as JSON string"""
        self.references = json.dumps(references) if references else None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: str}

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
    
    user: Optional[User] = Relationship(back_populates="articles")
    statements: List[Statement] = Relationship(back_populates="article")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: str}

    def set_links(self, links: List[str]) -> None:
        self.links = json.dumps(links)

    def get_links(self) -> List[str]:
        return json.loads(self.links) if self.links else []

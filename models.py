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
    references: Optional[str] = Field(default=None)  # JSON string field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    article_id: Optional[int] = Field(default=None, foreign_key="article.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    article: Optional["Article"] = Relationship(back_populates="statements")

    def get_references(self) -> List[dict]:
        if not self.references:
            return []
        try:
            return json.loads(self.references) if isinstance(self.references, str) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def set_references(self, references: List[dict]) -> None:
        if references is None:
            self.references = None
        else:
            try:
                # Ensure each reference has the required fields
                formatted_refs = []
                for ref in references:
                    formatted_ref = {
                        'title': ref.get('title', ''),
                        'source': ref.get('source', ''),
                        'summary': ref.get('summary', '')
                    }
                    formatted_refs.append(formatted_ref)
                self.references = json.dumps(formatted_refs)
            except (TypeError, ValueError):
                self.references = None

class Article(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    text: str
    date: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")
    is_active: bool = Field(default=True)  # Added is_active field
    domain: Optional[str] = Field(max_length=500)
    links: Optional[str] = Field(default=None)
    authors: Optional[str] = Field(max_length=1000)
    publication_date: Optional[datetime]
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="articles")
    statements: List[Statement] = Relationship(back_populates="article")

    def get_links(self) -> List[str]:
        if not self.links:
            return []
        try:
            return json.loads(self.links) if isinstance(self.links, str) else []
        except json.JSONDecodeError:
            return []

    def set_links(self, links: List[str]) -> None:
        if links is None:
            self.links = None
        else:
            self.links = json.dumps(links)

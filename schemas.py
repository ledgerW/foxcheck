from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Existing code remains the same
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# New schemas for Article, Statement, and Reference
class ReferenceBase(BaseModel):
    url: str
    title: Optional[str] = None
    content: str
    context: Optional[str] = None

class ReferenceCreate(ReferenceBase):
    pass

class ReferenceRead(ReferenceBase):
    id: int
    article_id: Optional[int]
    statement_id: Optional[int]

class StatementBase(BaseModel):
    content: str
    verdict: Optional[str] = None
    explanation: Optional[str] = None

class StatementCreate(StatementBase):
    pass

class StatementRead(StatementBase):
    id: int
    created_at: datetime
    article_id: Optional[int]
    user_id: Optional[int]
    references: List[ReferenceRead] = []

class ArticleBase(BaseModel):
    title: str
    text: str
    domain: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[datetime] = None

class ArticleCreate(ArticleBase):
    links: Optional[List[str]] = None

class ArticleRead(ArticleBase):
    id: int
    date: datetime
    user_id: int
    is_approved: bool
    extraction_date: datetime
    statements: List[StatementRead] = []
    references: List[ReferenceRead] = []
    links: Optional[List[str]] = None

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    domain: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[datetime] = None
    is_approved: Optional[bool] = None
    links: Optional[List[str]] = None

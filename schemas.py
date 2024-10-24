from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
import json

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = False

# Reference schema (used within Statement)
class Reference(BaseModel):
    title: Optional[str] = None
    source: str
    summary: str

# Statement schemas
class StatementBase(BaseModel):
    content: str
    verdict: Optional[str] = None
    explanation: Optional[str] = None
    references: Optional[List[Reference]] = None

class StatementCreate(StatementBase):
    pass

class StatementRead(StatementBase):
    id: int
    created_at: datetime
    article_id: int
    user_id: int
    references: Optional[List[Reference]] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('references', pre=True)
    def parse_references(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

# Article schemas
class ArticleBase(BaseModel):
    title: str
    text: str
    domain: Optional[str] = Field(None, max_length=500)
    authors: Optional[str] = Field(None, max_length=1000)
    publication_date: Optional[datetime] = None

class ArticleCreate(ArticleBase):
    links: Optional[List[str]] = []
    is_active: bool = True

class ArticleRead(ArticleBase):
    id: int
    date: datetime
    user_id: int
    is_active: bool = True
    extraction_date: Optional[datetime] = None
    statements: List[StatementRead] = []
    links: Optional[List[str]] = []
    user: Optional[UserRead] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('statements', pre=True)
    def ensure_list_statements(cls, v):
        if v is None:
            return []
        return v

    @validator('links', pre=True)
    def parse_links(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    domain: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    links: Optional[List[str]] = None

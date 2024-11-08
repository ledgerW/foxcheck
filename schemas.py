from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Any, Union
from typing_extensions import TypedDict
from datetime import datetime
from dateutil import parser
import json

# User schemas
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
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Reference schema (used within Statement)
class Reference(TypedDict):
    title: str
    source: str
    summary: str

# Statement schemas
class StatementBase(BaseModel):
    content: str
    verdict: Optional[str] = None
    explanation: Optional[str] = None
    references: Optional[List[Reference]] = None

class StatementRequest(BaseModel):
    statement: str

class StatementCreate(StatementBase):
    pass

class Reference(BaseModel):
    title: str
    source: str
    summary: Optional[str] = None

class StatementUpdate(BaseModel):
    content: Optional[str] = None
    verdict: Optional[str] = None
    explanation: Optional[str] = None
    references: Optional[List[Reference]] = None

class StatementRead(BaseModel):
    id: int
    content: str
    verdict: Optional[str] = None
    explanation: Optional[str] = None
    references: List[Reference] = []  # Expect this as a list in the response
    created_at: datetime
    article_id: Optional[int] = None
    user_id: Optional[int] = None

    @validator("references", pre=True)
    def parse_references(cls, v):
        if isinstance(v, str):  # Parse JSON string to list
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

# Article schemas
class ArticleBase(BaseModel):
    title: str
    text: str
    domain: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[Union[str, datetime]] = None


class ArticleCreate(ArticleBase):
    links: Optional[List[str]] = []

    @validator("publication_date", pre=True)
    def parse_publication_date(cls, v):
        if isinstance(v, str):
            try:
                return parser.parse(v)
            except (ValueError, TypeError):
                raise ValueError("Invalid date format for publication_date")
        return v


class ArticleRead(BaseModel):
    id: int
    title: str
    text: str
    domain: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[datetime] = None
    date: datetime
    user_id: int
    is_active: bool = True
    extraction_date: Optional[datetime] = None
    statements: List[StatementRead] = []  # Use StatementRead to ensure correct parsing
    links: List[str] = []

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

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

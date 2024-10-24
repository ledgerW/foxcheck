from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import update, delete, func
from typing import Optional, List
from models import User, Article, Statement
from schemas import UserCreate, UserUpdate, ArticleCreate, ArticleUpdate, StatementCreate
from auth import get_password_hash
import json

# User CRUD operations
async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_admin=user.is_admin if user.is_admin is not None else False
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: int):
    return await db.get(User, user_id)

async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).filter(User.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_user(db: AsyncSession, user: User, user_update: UserUpdate):
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user: User):
    await db.delete(user)
    await db.commit()

# Article CRUD operations
async def create_article(db: AsyncSession, article: ArticleCreate, user_id: int):
    links_json = json.dumps(article.links) if article.links else "[]"
    db_article = Article(
        title=article.title,
        text=article.text,
        domain=article.domain,
        authors=article.authors,
        publication_date=article.publication_date,
        user_id=user_id,
        links=links_json,
        is_active=True
    )
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    
    # Parse links back to list for response
    db_article.links = json.loads(db_article.links)
    return db_article

async def get_article(db: AsyncSession, article_id: int):
    stmt = (
        select(Article)
        .options(
            joinedload('user'),
            joinedload('statements')
        )
        .filter(Article.id == article_id)
    )
    result = await db.execute(stmt)
    article = result.unique().scalar_one_or_none()
    
    if article:
        # Ensure is_active is set
        if article.is_active is None:
            article.is_active = True
            await db.commit()
        
        # Parse links
        try:
            article.links = json.loads(article.links) if article.links else []
        except json.JSONDecodeError:
            article.links = []
        
        # Parse references in statements
        if article.statements:
            for statement in article.statements:
                try:
                    statement.references = json.loads(statement.references) if statement.references else []
                except json.JSONDecodeError:
                    statement.references = []
    
    return article

async def get_articles(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = (
        select(Article)
        .options(
            joinedload('user'),
            joinedload('statements')
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.unique().scalars().all()
    
    for article in articles:
        # Ensure is_active is set
        if article.is_active is None:
            article.is_active = True
        
        # Parse links
        try:
            article.links = json.loads(article.links) if article.links else []
        except json.JSONDecodeError:
            article.links = []
        
        # Parse references in statements
        if article.statements:
            for statement in article.statements:
                try:
                    statement.references = json.loads(statement.references) if statement.references else []
                except json.JSONDecodeError:
                    statement.references = []
    
    await db.commit()
    return articles

async def update_article(db: AsyncSession, article: Article, article_update: ArticleUpdate):
    update_data = article_update.dict(exclude_unset=True)
    
    if 'links' in update_data:
        update_data['links'] = json.dumps(update_data['links'] or [])
    
    for key, value in update_data.items():
        setattr(article, key, value)
    
    await db.commit()
    await db.refresh(article)
    
    # Parse links back to list for response
    try:
        article.links = json.loads(article.links) if article.links else []
    except json.JSONDecodeError:
        article.links = []
    
    return article

async def delete_article(db: AsyncSession, article: Article):
    await db.delete(article)
    await db.commit()

# Statement CRUD operations
async def create_statement(db: AsyncSession, statement: StatementCreate, article_id: int, user_id: int):
    references_json = "[]"
    if statement.references:
        try:
            formatted_refs = []
            for ref in statement.references:
                formatted_ref = {
                    'title': str(ref.title) if ref.title else '',
                    'source': str(ref.source),
                    'summary': str(ref.summary)
                }
                formatted_refs.append(formatted_ref)
            references_json = json.dumps(formatted_refs)
        except (AttributeError, ValueError):
            references_json = "[]"

    db_statement = Statement(
        content=statement.content,
        verdict=statement.verdict,
        explanation=statement.explanation,
        references=references_json,
        article_id=article_id,
        user_id=user_id
    )
    db.add(db_statement)
    await db.commit()
    await db.refresh(db_statement)
    
    # Parse references back to list for response
    try:
        db_statement.references = json.loads(db_statement.references)
    except json.JSONDecodeError:
        db_statement.references = []
    
    return db_statement

async def get_statement(db: AsyncSession, statement_id: int):
    stmt = select(Statement).filter(Statement.id == statement_id)
    result = await db.execute(stmt)
    statement = result.scalar_one_or_none()
    
    if statement:
        try:
            statement.references = json.loads(statement.references) if statement.references else []
        except json.JSONDecodeError:
            statement.references = []
    
    return statement

async def get_statements(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Statement).offset(skip).limit(limit)
    result = await db.execute(stmt)
    statements = result.scalars().all()
    
    for statement in statements:
        try:
            statement.references = json.loads(statement.references) if statement.references else []
        except json.JSONDecodeError:
            statement.references = []
    
    return statements

async def get_article_statements(db: AsyncSession, article_id: int):
    stmt = select(Statement).filter(Statement.article_id == article_id)
    result = await db.execute(stmt)
    statements = result.scalars().all()
    
    for statement in statements:
        try:
            statement.references = json.loads(statement.references) if statement.references else []
        except json.JSONDecodeError:
            statement.references = []
    
    return statements

async def update_statement(db: AsyncSession, statement: Statement, verdict: str, explanation: str, references: Optional[List[dict]] = None):
    statement.verdict = verdict
    statement.explanation = explanation
    
    if references is not None:
        try:
            formatted_refs = []
            for ref in references:
                formatted_ref = {
                    'title': str(ref.get('title', '')),
                    'source': str(ref.get('source', '')),
                    'summary': str(ref.get('summary', ''))
                }
                formatted_refs.append(formatted_ref)
            statement.references = json.dumps(formatted_refs)
        except (AttributeError, ValueError):
            statement.references = "[]"
    
    await db.commit()
    await db.refresh(statement)
    
    # Parse references back to list for response
    try:
        statement.references = json.loads(statement.references)
    except json.JSONDecodeError:
        statement.references = []
    
    return statement

async def delete_statement(db: AsyncSession, statement: Statement):
    await db.delete(statement)
    await db.commit()

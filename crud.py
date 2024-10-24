from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import update, delete
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
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: int):
    return await db.get(User, user_id)

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(User)
        .where(User.email == email)
    )
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def update_user(db: AsyncSession, user: User, user_update: UserUpdate):
    for key, value in user_update.dict(exclude_unset=True).items():
        if key == "password":
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user: User):
    await db.delete(user)
    await db.commit()

# Article CRUD operations
async def create_article(db: AsyncSession, article: ArticleCreate, user_id: int):
    links_json = json.dumps(article.links) if article.links else None
    db_article = Article(
        title=article.title,
        text=article.text,
        domain=article.domain,
        authors=article.authors,
        publication_date=article.publication_date,
        user_id=user_id,
        links=links_json,
        is_active=article.is_active
    )
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    return db_article

async def get_article(db: AsyncSession, article_id: int):
    stmt = (
        select(Article)
        .options(
            selectinload(Article.user),
            selectinload(Article.statements)
        )
        .where(Article.id == article_id)
    )
    result = await db.execute(stmt)
    article = result.unique().scalar_one_or_none()
    
    if article and article.is_active is None:
        article.is_active = True
        await db.commit()
    
    return article

async def get_articles(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = (
        select(Article)
        .options(
            selectinload(Article.user),
            selectinload(Article.statements)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    articles = result.unique().scalars().all()
    
    # Set default values if needed
    for article in articles:
        if article.is_active is None:
            article.is_active = True
        if not hasattr(article, 'statements'):
            article.statements = []
            
    await db.commit()
    return articles

async def update_article(db: AsyncSession, article: Article, article_update: ArticleUpdate):
    update_data = article_update.dict(exclude_unset=True)
    
    if 'links' in update_data:
        update_data['links'] = json.dumps(update_data['links'])
    
    for key, value in update_data.items():
        setattr(article, key, value)
    
    await db.commit()
    await db.refresh(article)
    return article

async def delete_article(db: AsyncSession, article: Article):
    await db.delete(article)
    await db.commit()

# Statement CRUD operations
async def create_statement(db: AsyncSession, statement: StatementCreate, article_id: int, user_id: int):
    references_json = json.dumps(statement.references) if hasattr(statement, 'references') else None
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
    return db_statement

async def get_statement(db: AsyncSession, statement_id: int):
    stmt = select(Statement).where(Statement.id == statement_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_statements(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Statement).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_article_statements(db: AsyncSession, article_id: int):
    stmt = select(Statement).where(Statement.article_id == article_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_statement(db: AsyncSession, statement: Statement, verdict: str, explanation: str, references: List[dict] = None):
    statement.verdict = verdict
    statement.explanation = explanation
    if references is not None:
        statement.set_references(references)
    await db.commit()
    await db.refresh(statement)
    return statement

async def delete_statement(db: AsyncSession, statement: Statement):
    await db.delete(statement)
    await db.commit()

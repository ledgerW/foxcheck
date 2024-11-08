from pydantic import AnyHttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import update, delete
from typing import Optional, List
from models import User, Article, Statement
from schemas import UserCreate, UserUpdate, ArticleCreate, ArticleUpdate, StatementCreate, Reference
from auth import get_password_hash
import json
from sqlalchemy.exc import IntegrityError

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
async def check_domain_exists(db: AsyncSession, domain: AnyHttpUrl) -> bool:
    if domain:
        result = await db.execute(
            select(Article).where(Article.domain == domain)
        )
        return result.scalar_one_or_none() is not None
    return False


async def create_article(db: AsyncSession, article: ArticleCreate, user_id: int):
    # Check for existing domain if provided
    if article.domain and await check_domain_exists(db, article.domain):
        raise ValueError(f"An article with domain '{article.domain}' already exists")

    # Convert links to JSON string if provided
    links_json = json.dumps(article.links) if article.links else "[]"

    db_article = Article(
        title=article.title,
        text=article.text,
        domain=article.domain,
        authors=article.authors,
        publication_date=article.publication_date,
        user_id=user_id,
        links=links_json,  # Pass JSON string instead of list
        is_active=True
    )

    try:
        db.add(db_article)
        await db.commit()
        await db.refresh(db_article)

        # Explicitly load relationships
        stmt = select(Article).options(
            joinedload(Article.statements)
        ).where(Article.id == db_article.id)
        result = await db.execute(stmt)
        return result.unique().scalar_one()
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key value violates unique constraint" in str(e):
            raise ValueError(f"An article with domain '{article.domain}' already exists")
        raise


async def get_article(db: AsyncSession, article_id: int):
    stmt = (
        select(Article)
        .options(
            joinedload(Article.user),
            joinedload(Article.statements)
        )
        .where(Article.id == article_id)
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_article_by_url(db: AsyncSession, article_url: str):
    stmt = (
        select(Article)
        .options(
            joinedload(Article.user),
            joinedload(Article.statements)
        )
        .where(Article.domain == article_url)
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_articles(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = (
        select(Article)
        .options(
            joinedload(Article.user),
            joinedload(Article.statements)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.unique().scalars().all()


async def update_article(db: AsyncSession, article: Article, article_update: ArticleUpdate):
    update_data = article_update.dict(exclude_unset=True)
    if 'links' in update_data:
        update_data['links'] = json.dumps(update_data['links'])
    
    for key, value in update_data.items():
        setattr(article, key, value)
    
    try:
        await db.commit()
        await db.refresh(article)
        return article
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key value violates unique constraint" in str(e):
            raise ValueError(f"An article with domain '{article_update.domain}' already exists")
        raise


async def delete_article(db: AsyncSession, article: Article):
    await db.delete(article)
    await db.commit()


# Statement CRUD operations
async def create_statement(db: AsyncSession, statement: Statement, article_id: int, user_id: int):
    # Set the article_id and user_id for the statement
    statement.article_id = article_id
    statement.user_id = user_id

    # Add and commit the statement to the database
    db.add(statement)
    await db.commit()
    await db.refresh(statement)
    return statement

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

async def update_statement(db: AsyncSession, statement: Statement, verdict: str, explanation: str, references: List[Reference] = None):
    statement.verdict = verdict
    statement.explanation = explanation
    statement.references = references
    #if references is not None:
    #    statement.set_references(references)
    await db.commit()
    await db.refresh(statement)
    return statement

async def delete_statement(db: AsyncSession, statement: Statement):
    await db.delete(statement)
    await db.commit()

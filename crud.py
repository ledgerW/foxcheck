from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, and_
from typing import Optional, List
from models import User, Article, Statement
from schemas import UserCreate, UserUpdate, ArticleCreate, ArticleUpdate, StatementCreate
from auth import get_password_hash
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
    stmt = select(User).where(User.email == email)
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

async def create_article(db: AsyncSession, article: ArticleCreate, user_id: int):
    try:
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
        
        # Parse links for response
        db_article.links = json.loads(db_article.links) if db_article.links else []
        return db_article
    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        await db.rollback()
        raise

async def get_article(db: AsyncSession, article_id: int):
    try:
        stmt = select(Article).where(Article.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if article:
            # Set defaults
            if article.is_active is None:
                article.is_active = True
            
            # Handle links
            try:
                article.links = json.loads(article.links) if article.links else []
            except json.JSONDecodeError:
                article.links = []
            
            # Load statements
            stmt = select(Statement).where(Statement.article_id == article_id)
            result = await db.execute(stmt)
            article.statements = result.scalars().all()
            
            # Parse references in statements
            for statement in article.statements:
                try:
                    statement.references = json.loads(statement.references) if statement.references else []
                except json.JSONDecodeError:
                    statement.references = []

        return article
    except Exception as e:
        logger.error(f"Error getting article {article_id}: {str(e)}")
        raise

async def get_articles(db: AsyncSession, skip: int = 0, limit: int = 100):
    try:
        # Simple query without relationships first
        stmt = select(Article).offset(skip).limit(limit)
        result = await db.execute(stmt)
        articles = result.scalars().all()
        
        # Set defaults for required fields
        for article in articles:
            if article.is_active is None:
                article.is_active = True
            
            # Handle links
            if not hasattr(article, 'links') or article.links is None:
                article.links = []
            elif isinstance(article.links, str):
                try:
                    article.links = json.loads(article.links)
                except json.JSONDecodeError:
                    article.links = []
            
            # Initialize empty statements list
            if not hasattr(article, 'statements'):
                article.statements = []
        
        return articles
    except Exception as e:
        logger.error(f"Error in get_articles: {str(e)}")
        raise

async def update_article(db: AsyncSession, article: Article, article_update: ArticleUpdate):
    try:
        update_data = article_update.dict(exclude_unset=True)
        
        if 'links' in update_data:
            update_data['links'] = json.dumps(update_data['links']) if update_data['links'] else "[]"
        
        for key, value in update_data.items():
            setattr(article, key, value)
        
        await db.commit()
        await db.refresh(article)
        
        # Parse links for response
        article.links = json.loads(article.links) if article.links else []
        return article
    except Exception as e:
        logger.error(f"Error updating article: {str(e)}")
        await db.rollback()
        raise

async def delete_article(db: AsyncSession, article: Article):
    try:
        await db.delete(article)
        await db.commit()
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        await db.rollback()
        raise

# Statement CRUD operations remain unchanged...

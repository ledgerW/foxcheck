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
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            is_admin=user.is_admin if user.is_admin is not None else False
        )
        async with db.begin():
            db.add(db_user)
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise

async def get_user(db: AsyncSession, user_id: int):
    try:
        async with db.begin():
            return await db.get(User, user_id)
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise

async def get_user_by_email(db: AsyncSession, email: str):
    try:
        stmt = select(User).where(User.email == email)
        async with db.begin():
            result = await db.execute(stmt)
            return result.scalars().first()
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        raise

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    try:
        stmt = select(User).offset(skip).limit(limit)
        async with db.begin():
            result = await db.execute(stmt)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise

async def update_user(db: AsyncSession, user: User, user_update: UserUpdate):
    try:
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        for key, value in update_data.items():
            setattr(user, key, value)
        async with db.begin():
            await db.merge(user)
        await db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise

async def delete_user(db: AsyncSession, user: User):
    try:
        async with db.begin():
            await db.delete(user)
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise

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
        async with db.begin():
            db.add(db_article)
        await db.refresh(db_article)
        
        # Parse links for response
        db_article.links = json.loads(db_article.links) if db_article.links else []
        return db_article
    except Exception as e:
        logger.error(f"Error creating article: {str(e)}")
        raise

async def get_article(db: AsyncSession, article_id: int):
    try:
        stmt = select(Article).where(Article.id == article_id)
        async with db.begin():
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
                article.statements = list(result.scalars().all())
                
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
        # Simple query without joins
        stmt = select(Article).offset(skip).limit(limit)
        async with db.begin():
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
        
        async with db.begin():
            await db.merge(article)
        await db.refresh(article)
        
        # Parse links for response
        article.links = json.loads(article.links) if article.links else []
        return article
    except Exception as e:
        logger.error(f"Error updating article: {str(e)}")
        raise

async def delete_article(db: AsyncSession, article: Article):
    try:
        async with db.begin():
            await db.delete(article)
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        raise

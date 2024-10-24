from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging
from database import get_session
from schemas import ArticleCreate, ArticleRead, ArticleUpdate
from models import User, Article
from crud import create_article, get_article, get_articles, update_article, delete_article
from auth import get_current_active_user, get_current_admin_user
import json

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("", response_model=ArticleRead)
async def create_new_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Creating new article with title: {article.title}")
        db_article = await create_article(db=db, article=article, user_id=current_user.id)
        logger.info(f"Successfully created article with id: {db_article.id}")
        return db_article
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError while creating article: {str(e)}")
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=400,
                detail="An article with this domain already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ArticleRead])
async def read_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_session)
):
    try:
        logger.info("Fetching articles from database")
        articles = await get_articles(db, skip=skip, limit=limit)
        
        logger.info(f"Found {len(articles)} articles")
        
        # Filter out inactive articles for public view
        if not include_inactive:
            articles = [article for article in articles if article.is_active]
            logger.info(f"After filtering inactive: {len(articles)} articles")
            
        return articles
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{article_id}", response_model=ArticleRead)
async def read_article(
    article_id: int,
    db: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"Fetching article with id: {article_id}")
        article = await get_article(db, article_id=article_id)
        if article is None or not article.is_active:
            logger.warning(f"Article {article_id} not found or inactive")
            raise HTTPException(status_code=404, detail="Article not found")
        logger.info(f"Successfully retrieved article: {article.title}")
        return article
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching article {article_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{article_id}", response_model=ArticleRead)
async def update_existing_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Updating article {article_id}")
        article = await get_article(db, article_id=article_id)
        if article is None:
            logger.warning(f"Article {article_id} not found")
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Allow update if user is admin or the article owner
        if not current_user.is_admin and article.user_id != current_user.id:
            logger.warning(f"User {current_user.id} not authorized to update article {article_id}")
            raise HTTPException(status_code=403, detail="Not authorized to update this article")
        
        updated_article = await update_article(db=db, article=article, article_update=article_update)
        logger.info(f"Successfully updated article {article_id}")
        return updated_article
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError while updating article {article_id}: {str(e)}")
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=400,
                detail="An article with this domain already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{article_id}")
async def delete_existing_article(
    article_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    try:
        logger.info(f"Attempting to delete article {article_id}")
        article = await get_article(db, article_id=article_id)
        if article is None:
            logger.warning(f"Article {article_id} not found")
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Allow deletion if user is admin or the article owner
        if not current_user.is_admin and article.user_id != current_user.id:
            logger.warning(f"User {current_user.id} not authorized to delete article {article_id}")
            raise HTTPException(status_code=403, detail="Not authorized to delete this article")
        
        await delete_article(db=db, article=article)
        logger.info(f"Successfully deleted article {article_id}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin-specific routes
@router.get("/admin/all", response_model=List[ArticleRead])
async def read_all_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    db: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user)
):
    try:
        logger.info("Admin: Fetching all articles")
        articles = await get_articles(db, skip=skip, limit=limit)
        logger.info(f"Admin: Found {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"Admin: Error fetching articles: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

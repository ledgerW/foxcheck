from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from database import get_session
from schemas import ArticleCreate, ArticleRead, ArticleUpdate, Reference
from models import User, Article
from crud import create_article, get_article, get_articles, update_article, delete_article
from auth import get_current_active_user, get_current_user
import json

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("", response_model=ArticleRead)
async def create_new_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    try:
        db_article = await create_article(db=db, article=article, user_id=current_user.id)
        await db.refresh(db_article)  # Ensure relationships are loaded
        return db_article
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=400,
                detail="An article with this domain already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ArticleRead])
async def read_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_session)
):
    try:
        articles = await get_articles(db, skip=skip, limit=limit)
        
        # Filter out inactive articles
        if not include_inactive:
            articles = [article for article in articles if article.is_active]
            
        # Ensure relationships are loaded
        for article in articles:
            await db.refresh(article)
        
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{article_id}", response_model=ArticleRead)
async def read_article(
    article_id: int,
    db: AsyncSession = Depends(get_session)
):
    try:
        article = await get_article(db, article_id=article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check if article is inactive
        if not article.is_active:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Ensure relationships are loaded
        await db.refresh(article)
        
        return article
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{article_id}", response_model=ArticleRead)
async def update_existing_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    try:
        article = await get_article(db, article_id=article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Allow update if user is admin or the article owner
        if not current_user.is_admin and article.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this article")
        
        updated_article = await update_article(db=db, article=article, article_update=article_update)
        await db.refresh(updated_article)  # Ensure relationships are loaded
        return updated_article
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=400,
                detail="An article with this domain already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{article_id}")
async def delete_existing_article(
    article_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    try:
        article = await get_article(db, article_id=article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Allow deletion if user is admin or the article owner
        if not current_user.is_admin and article.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this article")
        
        await delete_article(db=db, article=article)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

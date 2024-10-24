from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import get_session
from schemas import ArticleCreate, ArticleRead, ArticleUpdate, Reference
from models import User, Article
from crud import create_article, get_article, get_articles, update_article, delete_article
from auth import get_current_active_user
import json

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("", response_model=ArticleRead)
async def create_new_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    try:
        db_article = await create_article(db=db, article=article, user_id=current_user.id)
        return db_article
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[ArticleRead])
async def read_articles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    db: AsyncSession = Depends(get_session)
):
    articles = await get_articles(db, skip=skip, limit=limit)
    return articles

@router.get("/{article_id}", response_model=ArticleRead)
async def read_article(
    article_id: int,
    db: AsyncSession = Depends(get_session)
):
    article = await get_article(db, article_id=article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.put("/{article_id}", response_model=ArticleRead)
async def update_existing_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    try:
        article = await get_article(db, article_id=article_id)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        if article.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this article")
        return await update_article(db=db, article=article, article_update=article_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

@router.delete("/{article_id}")
async def delete_existing_article(
    article_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    article = await get_article(db, article_id=article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this article")
    await delete_article(db=db, article=article)
    return {"ok": True}

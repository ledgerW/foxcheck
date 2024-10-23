from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import get_session
from schemas import ArticleCreate, ArticleRead, ArticleUpdate, StatementCreate, StatementRead
from models import User, Article, Statement
from crud import (
    create_article, get_article, get_articles, update_article, delete_article,
    create_statement, get_statement, get_statements, get_article_statements,
    update_statement, delete_statement
)
from auth import get_current_active_user

router = APIRouter(prefix="/articles", tags=["articles"])

@router.post("", response_model=ArticleRead)
async def create_new_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    return await create_article(db=db, article=article, user_id=current_user.id)

@router.get("", response_model=List[ArticleRead])
async def read_articles(
    skip: int = 0,
    limit: int = 100,
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
    article = await get_article(db, article_id=article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this article")
    return await update_article(db=db, article=article, article_update=article_update)

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

# Statement routes
@router.post("/{article_id}/statements", response_model=StatementRead)
async def create_article_statement(
    article_id: int,
    statement: StatementCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    article = await get_article(db, article_id=article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return await create_statement(
        db=db,
        statement=statement,
        article_id=article_id,
        user_id=current_user.id
    )

@router.get("/{article_id}/statements", response_model=List[StatementRead])
async def read_article_statements(
    article_id: int,
    db: AsyncSession = Depends(get_session)
):
    article = await get_article(db, article_id=article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return await get_article_statements(db, article_id=article_id)

@router.put("/{article_id}/statements/{statement_id}", response_model=StatementRead)
async def update_article_statement(
    article_id: int,
    statement_id: int,
    verdict: str,
    explanation: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    statement = await get_statement(db, statement_id=statement_id)
    if statement is None or statement.article_id != article_id:
        raise HTTPException(status_code=404, detail="Statement not found")
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this statement")
    return await update_statement(db=db, statement=statement, verdict=verdict, explanation=explanation)

@router.delete("/{article_id}/statements/{statement_id}")
async def delete_article_statement(
    article_id: int,
    statement_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    statement = await get_statement(db, statement_id=statement_id)
    if statement is None or statement.article_id != article_id:
        raise HTTPException(status_code=404, detail="Statement not found")
    if statement.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this statement")
    await delete_statement(db=db, statement=statement)
    return {"ok": True}

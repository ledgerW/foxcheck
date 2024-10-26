from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import get_session
from schemas import ArticleCreate, ArticleRead, ArticleUpdate, StatementRequest
from models import User, Article, Statement
from crud import (
    create_article,
    get_article,
    get_articles,
    update_article,
    delete_article,
    create_statement
)
from auth import get_current_active_user
from routers.api import get_statements, check_statement
import json
import asyncio

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("", response_model=ArticleRead)
async def create_new_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    #try:
    db_article = await create_article(db=db, article=article, user_id=current_user.id)

    statements = await get_statements(article.text)
    statements = [st for st in statements if st]

    check_tasks = [check_statement(StatementRequest(statement=st)) for st in statements]
    verdicts = await asyncio.gather(*check_tasks)

    #all_statements = []
    for statement, verdict in zip(statements, verdicts):
        statement_create = Statement(
            content=statement,
            verdict=verdict.verdict,
            explanation=verdict.explanation
        )
        statement_create.references = json.dumps(verdict.references)
        db_statement = await create_statement(
            db=db,
            statement=statement_create, 
            article_id=db_article.id, 
            user_id=current_user.id
        )
        
    return db_article
    #except ValueError as e:
    #    # Return JSON response instead of raising exception
    #    return JSONResponse(
    #        status_code=status.HTTP_409_CONFLICT,
    #        content={'status': 'error', 'message': str(e)}
    #    )
    #except Exception as e:
    #    await db.rollback()
    #    return JSONResponse(
    #        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #        content={'status': 'error', 'message': str(e)}
    #    )

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
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={'status': 'error', 'message': str(e)}
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

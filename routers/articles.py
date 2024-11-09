from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
from database import get_session
from schemas import ArticleCreate, ArticleRead, ArticleUpdate, StatementRequest
from models import User, Article, Statement
from crud import (
    create_article,
    get_article,
    get_article_by_url,
    get_articles,
    update_article,
    delete_article,
    create_statement
)
from auth import get_current_active_user
from routers.api import get_statements, check_statement
from chains.article_metadata_chain import chain as metadata_chain
from langchain_community.retrievers import TavilySearchAPIRetriever
import json
import asyncio

router = APIRouter(prefix="/api/articles", tags=["articles"])

@router.post("", response_model=ArticleRead)
async def create_new_article(
    article: ArticleCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    db_article = await create_article(db=db, article=article, user_id=current_user.id)

    statements = await get_statements(article.text)
    statements = [st for st in statements if st]

    check_tasks = [check_statement(StatementRequest(statement=st)) for st in statements]
    verdicts = await asyncio.gather(*check_tasks)

    for statement, verdict in zip(statements, verdicts):
        if verdict:
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

@router.get("/from_url", response_model=Union[ArticleRead, None])
async def get_article_from_url(
    url: str = Query(..., description="The URL of the article to analyze"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    domain = url.split('//')[1].split('/')[0]
    domain = 'https://' + domain

    search = TavilySearchAPIRetriever(k=3, include_raw_content=True, include_domains=[domain])

    try:
        res = await search.ainvoke(url)

        doc = [doc for doc in res if doc.metadata['source']==url]
        if doc:
            print("Search url found")
            doc = doc[0]
        else:
            print('Search url not found, using closest article')
            doc = res[0]

        result = {
            'title': doc.metadata['title'],
            'domain': url,
            'text': doc.page_content
        }
    except Exception as e:
        print(e)
        result = None

    if result:
        metadata = await metadata_chain.ainvoke(result['text'])
        result = result | metadata.dict()
        db_article = await create_new_article(article=ArticleCreate(**result), db=db, current_user=current_user)
        return db_article
    else:
        return None

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

@router.get("/url/{article_url}", response_model=ArticleRead)
async def read_article_by_url(
    article_url: str,
    db: AsyncSession = Depends(get_session)
):
    article = await get_article_by_url(db, article_url=article_url)
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

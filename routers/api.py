from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Dict
from database import get_session
from models import User, Article, Statement
from auth import get_current_admin_user, get_current_active_user

from pydantic import BaseModel
from typing import List
from typing_extensions import TypedDict
import json
from chains.statement_chain import get_statements as _get_statements
from chains.wikipedia_chain import retriever as wiki_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.adjudicator_chain import chain as judge_chain, Verdict
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter


class Statement(BaseModel):
    statement: str

class Statements(TypedDict):
    statements: List[str]

class Content(BaseModel):
    content: str


router = APIRouter(prefix="/api", tags=["api"])


@router.post("/check_statement")
async def check_statement(
    statement: Statement,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> Verdict:
    try:
        statement = statement.statement
        print(f"Statement: {statement}")
        fact_check_chain = (
            {"statement": RunnablePassthrough(), "wiki": wiki_retriever, 'web': web_retriever, 'arxiv': arxiv_retriever}
            | RunnablePassthrough.assign(
                statement=itemgetter('statement'),
                wiki=itemgetter('wiki'),
                web=itemgetter('web'),
                arxiv=itemgetter('arxiv')
            )
            | judge_chain
        )
        verdict = await fact_check_chain.ainvoke(statement)
        return verdict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_statements")
async def get_statements(
    content: Content,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
) -> Statements:
    try:
        content = content.content
        _statements = await _get_statements(content)
        statements: Statements = {'statements': _statements}
        return statements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/stats", response_model=Dict[str, int])
async def get_admin_stats(
    db: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user)
):
    """Get admin dashboard statistics"""
    try:
        # Get total users
        users_result = await db.execute(select(func.count()).select_from(User))
        total_users = users_result.scalar()

        # Get total articles
        articles_result = await db.execute(select(func.count()).select_from(Article))
        total_articles = articles_result.scalar()

        # Get total statements
        statements_result = await db.execute(select(func.count()).select_from(Statement))
        total_statements = statements_result.scalar()

        return {
            "total_users": total_users,
            "total_articles": total_articles,
            "total_statements": total_statements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

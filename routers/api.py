from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User
from auth import get_current_active_user

import json
from chains.statement_chain import get_statements as _get_statements
from chains.wikipedia_chain import retriever as wiki_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.adjudicator_chain import chain as judge_chain

from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

router = APIRouter(prefix="/api", tags=["api"])

@router.post("/check_statement")
async def check_statement(
    statement: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    try:
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
        print(json.loads(verdict.model_dump_json()))
        return json.loads(verdict.model_dump_json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_statements")
async def get_statements(
    content: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        statements = await _get_statements(content)
        return {'statements': statements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

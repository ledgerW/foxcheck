from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User
from auth import get_current_active_user
from pydantic import BaseModel
from typing import List
from typing_extensions import TypedDict

from schemas import StatementRequest
from chains.statement_chain import get_statements as _get_statements
from chains.wikipedia_chain import retriever as wiki_retriever
from chains.tavily_chain import retriever as web_retriever
from chains.arxiv_chain import retriever as arxiv_retriever
from chains.adjudicator_chain import chain as judge_chain, Verdict
from chains.fact_check_chain import multi_hop_fact_check as fact_check_chain

from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

router = APIRouter(prefix="/api", tags=["api"])


#class Statement(BaseModel):
#    statement: str


@router.post("/check_statement", response_model=Verdict)
async def check_statement(
    statement: StatementRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    #try:
    _statement = statement.statement
    verdict = await fact_check_chain.ainvoke({'statement': _statement})
    return verdict
        #print(json.loads(verdict.model_dump_json()))
        #return json.loads(verdict.model_dump_json())
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_statements", response_model=List[str])
async def get_statements(
    content: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    #try:
    statements = await _get_statements(content)
    return statements
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))

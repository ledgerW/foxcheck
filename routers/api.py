from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User
from auth import get_current_active_user
from typing import List

from schemas import StatementRequest
from chains.statement_chain import get_statements as _get_statements
from chains.adjudicator_chain import Verdict
from chains.fact_check_chain import multi_hop_fact_check as fact_check_chain


router = APIRouter(prefix="/api", tags=["api"])


@router.post("/check_statement", response_model=Verdict)
async def check_statement(
    statement: StatementRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        _statement = statement.statement
        verdict = await fact_check_chain.ainvoke({'statement': _statement})
        return verdict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_statements", response_model=List[str])
async def get_statements(
    content: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        statements = await _get_statements(content)
        return statements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User
from auth import get_current_active_user
from ai.chainlit_interface import process_chainlit_request
from ai.langchain_interface import process_langchain_request

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/chainlit")
async def chainlit_endpoint(
    message: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        response = await process_chainlit_request(message, current_user)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/langchain")
async def langchain_endpoint(
    query: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session)
):
    try:
        response = await process_langchain_request(query, current_user)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

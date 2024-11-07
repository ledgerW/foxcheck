from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from schemas import UserCreate, UserRead, Token
from models import User
from crud import create_user, get_users
from auth import authenticate_user, create_access_token
from config import settings

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserRead)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_session)):
    return await create_user(db=db, user=user)

@router.get("", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    users = await get_users(db, skip=skip, limit=limit)
    return users

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer"}

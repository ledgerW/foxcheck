from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User, Article, Statement
from auth import get_current_active_user
from sqlalchemy import select
from typing import List
from sqlalchemy.orm import selectinload

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have admin privileges"
        )
    return current_user

# Admin dashboard pages
@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_user: User = Depends(get_admin_user)):
    try:
        return templates.TemplateResponse("admin/dashboard.html", {
            "request": request,
            "user": admin_user
        })
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login")
        raise

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, admin_user: User = Depends(get_admin_user)):
    try:
        return templates.TemplateResponse("admin/users.html", {
            "request": request,
            "user": admin_user
        })
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login")
        raise

@router.get("/admin/articles", response_class=HTMLResponse)
async def admin_articles(request: Request, admin_user: User = Depends(get_admin_user)):
    try:
        return templates.TemplateResponse("admin/articles.html", {
            "request": request,
            "user": admin_user
        })
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login")
        raise

@router.get("/admin/statements", response_class=HTMLResponse)
async def admin_statements(request: Request, admin_user: User = Depends(get_admin_user)):
    try:
        return templates.TemplateResponse("admin/statements.html", {
            "request": request,
            "user": admin_user
        })
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/login")
        raise

# Admin API endpoints
@router.get("/api/admin/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    users_count = await db.execute(select(User).count())
    articles_count = await db.execute(select(Article).count())
    statements_count = await db.execute(select(Statement).count())
    
    return {
        "users_count": users_count.scalar(),
        "articles_count": articles_count.scalar(),
        "statements_count": statements_count.scalar()
    }

@router.get("/api/admin/users")
async def get_admin_users(
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.put("/api/admin/users/{user_id}")
async def update_user_admin(
    user_id: int,
    user_data: dict,
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    await db.commit()
    return user

@router.get("/api/admin/articles")
async def get_admin_articles(
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    stmt = select(Article).options(selectinload(Article.user))
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return articles

@router.put("/api/admin/articles/{article_id}")
async def update_article_admin(
    article_id: int,
    article_data: dict,
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    for key, value in article_data.items():
        if hasattr(article, key):
            setattr(article, key, value)
    
    await db.commit()
    return article

@router.get("/api/admin/statements")
async def get_admin_statements(
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    stmt = select(Statement).options(selectinload(Statement.article))
    result = await db.execute(stmt)
    statements = result.scalars().all()
    return statements

@router.put("/api/admin/statements/{statement_id}")
async def update_statement_admin(
    statement_id: int,
    statement_data: dict,
    db: AsyncSession = Depends(get_session),
    admin_user: User = Depends(get_admin_user)
):
    statement = await db.get(Statement, statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    for key, value in statement_data.items():
        if hasattr(statement, key):
            setattr(statement, key, value)
    
    await db.commit()
    return statement

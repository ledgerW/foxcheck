from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from models import User, Article, Statement
from auth import get_current_active_user
from sqlalchemy import select, func
from typing import List
from sqlalchemy.orm import selectinload

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    print(f"Admin access attempt - Headers: {dict(request.headers)}")
    print(f"Current user: {current_user.username} (admin: {current_user.is_admin})")
    
    if not current_user.is_admin:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": current_user
    })

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": current_user
    })

@router.get("/admin/articles", response_class=HTMLResponse)
async def admin_articles(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("admin/articles.html", {
        "request": request,
        "user": current_user
    })

@router.get("/admin/statements", response_class=HTMLResponse)
async def admin_statements(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("admin/statements.html", {
        "request": request,
        "user": current_user
    })

# Admin API endpoints
@router.get("/api/admin/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin stats"
        )
    
    users_count = await db.scalar(select(func.count(User.id)))
    articles_count = await db.scalar(select(func.count(Article.id)))
    statements_count = await db.scalar(select(func.count(Statement.id)))
    
    return {
        "users_count": users_count,
        "articles_count": articles_count,
        "statements_count": statements_count
    }

@router.get("/api/admin/users")
async def get_admin_users(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access user management"
        )
    
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.put("/api/admin/users/{user_id}")
async def update_user_admin(
    user_id: int,
    user_data: dict,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update users"
        )
    
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
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access article management"
        )
    
    result = await db.execute(select(Article).options(selectinload(Article.user)))
    articles = result.scalars().unique()
    return articles

@router.put("/api/admin/articles/{article_id}")
async def update_article_admin(
    article_id: int,
    article_data: dict,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update articles"
        )
    
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
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access statement management"
        )
    
    result = await db.execute(select(Statement).options(selectinload(Statement.article)))
    statements = result.scalars().all()
    return statements

@router.put("/api/admin/statements/{statement_id}")
async def update_statement_admin(
    statement_id: int,
    statement_data: dict,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update statements"
        )
    
    statement = await db.get(Statement, statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    for key, value in statement_data.items():
        if hasattr(statement, key):
            setattr(statement, key, value)
    
    await db.commit()
    return statement

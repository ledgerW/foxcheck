import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import users, api, articles
from database import init_db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from auth import get_current_active_user, get_current_admin_user
from pydantic import BaseModel
from typing import List

limiter = Limiter(key_func=get_remote_address)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app = FastAPI(title="Statement Checker")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(users.router)
app.include_router(api.router)
app.include_router(articles.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def on_startup():
    await init_db()

# Public routes
@app.get("/")
@limiter.limit("20/minute")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/statement_checker")
@limiter.limit("20/minute")
async def statement_checker(request: Request):
    return templates.TemplateResponse("statement_checker.html", {"request": request})

@app.get("/articles/{article_id}")
async def article_page(request: Request, article_id: int):
    return templates.TemplateResponse("article.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Admin routes
@app.get("/admin")
async def admin_page(request: Request, current_user: dict = Depends(get_current_admin_user)):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@app.get("/api/auth/status")
async def auth_status(current_user: dict = Depends(get_current_active_user)):
    return {
        "authenticated": True,
        "username": current_user.username,
        "is_admin": current_user.is_admin
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import users, api
from database import create_db_and_tables
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from auth import get_current_active_user
from pydantic import BaseModel, Field
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

# CORS middleware setup
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

@app.get("/")
@limiter.limit("20/minute")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

class StatementRequest(BaseModel):
    statement: str = Field(..., min_length=1, max_length=1000, description="The statement to be checked")

class Reference(BaseModel):
    title: str
    source_url: str
    summary: str

class StatementResponse(BaseModel):
    verdict: str
    explanation: str
    references: List[Reference]

@app.post("/api/check_statement", response_model=StatementResponse)
@limiter.limit("10/minute")
async def check_statement(request: StatementRequest, current_user: dict = Depends(get_current_active_user)):
    try:
        # For demonstration purposes, we'll return a mock result.
        mock_result = StatementResponse(
            verdict="Partially True",
            explanation=f"The statement '{request.statement}' is partially true based on our analysis.",
            references=[
                Reference(
                    title="Fact-Checking Source 1",
                    source_url="https://example.com/fact-check1",
                    summary="This source provides context for part of the statement."
                ),
                Reference(
                    title="Fact-Checking Source 2",
                    source_url="https://example.com/fact-check2",
                    summary="This source contradicts a portion of the statement."
                )
            ]
        )
        return mock_result
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/api/auth/status")
async def auth_status(current_user: dict = Depends(get_current_active_user)):
    return {"authenticated": True, "username": current_user.username}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

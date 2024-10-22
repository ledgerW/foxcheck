import uvicorn
from fastapi import FastAPI, Request
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

limiter = Limiter(key_func=get_remote_address)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app = FastAPI(title="AI-Powered Search")

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

@app.post("/api/search")
@limiter.limit("10/minute")
async def search(request: Request):
    data = await request.json()
    query = data.get("query")
    if not query:
        return JSONResponse(status_code=400, content={"error": "Missing query parameter"})

    # For demonstration purposes, we'll return a mock result.
    mock_results = [
        {
            "title": "Search Result 1",
            "snippet": f"This is a mock result for the query: {query}",
            "link": "https://example.com/result1"
        },
        {
            "title": "Search Result 2",
            "snippet": f"Another mock result for: {query}",
            "link": "https://example.com/result2"
        }
    ]
    return JSONResponse(content=mock_results)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

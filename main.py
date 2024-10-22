import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, ai
from database import create_db_and_tables

app = FastAPI(title="AI-Powered FastAPI Application")

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(ai.router)

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to the AI-Powered FastAPI Application"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

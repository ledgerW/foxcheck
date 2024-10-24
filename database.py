from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from models import User, Article, Statement
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Update the connection string to use asyncpg and remove sslmode
DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
DATABASE_URL = re.sub(r'\?sslmode=\w+', '', DATABASE_URL)

# Create engine with optimized connection pooling and future flag
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_use_lifo=True,
    echo_pool=True
)

# Create async session factory with updated settings
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

@asynccontextmanager
async def get_session() -> AsyncSession:
    """Async context manager for database sessions"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database with retries"""
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _init_db():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        async with async_session_maker() as session:
            await create_admin_user(session)
            await seed_sample_articles(session)
    
    try:
        await _init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def create_admin_user(session: AsyncSession):
    """Create admin user if not exists"""
    try:
        from auth import get_password_hash
        
        # Check if admin user exists
        result = await session.execute(
            text("SELECT id FROM \"user\" WHERE username = :username AND is_admin = true"),
            {"username": "admin"}
        )
        admin_exists = result.scalar()
        
        if not admin_exists:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )
            session.add(admin_user)
            await session.commit()
            logger.info("Admin user created successfully")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        await session.rollback()
        raise

async def seed_sample_articles(session: AsyncSession):
    """Seed sample articles with admin and test user"""
    try:
        from auth import get_password_hash
        
        # Create test user if not exists
        result = await session.execute(
            text("SELECT id FROM \"user\" WHERE username = :username"),
            {"username": "testuser"}
        )
        user_id = result.scalar()
        
        if not user_id:
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpass123"),
                is_active=True
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            user_id = test_user.id

        # Check if articles exist
        result = await session.execute(text("SELECT COUNT(*) FROM article"))
        if result.scalar() > 0:
            logger.info("Articles already exist, skipping seed data")
            return

        # Sample article data
        article = Article(
            title="Climate Change Impact on Ocean Levels",
            text="Recent studies show significant changes in ocean levels across the globe.",
            domain="climate-science.org",
            authors="Dr. Jane Smith, Dr. John Doe",
            user_id=user_id,
            is_active=True,
            publication_date=datetime.utcnow() - timedelta(days=5)
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)

        # Add statement
        statement = Statement(
            content="Global sea levels have risen by 8-9 inches since 1880.",
            verdict="True",
            explanation="This statement is supported by multiple scientific studies.",
            article_id=article.id,
            user_id=user_id,
            references=json.dumps([{
                "title": "Ocean Level Study 2024",
                "source": "https://climate-science.org/ocean-study-2024",
                "summary": "Comprehensive analysis of global sea level changes"
            }])
        )
        session.add(statement)
        await session.commit()

        logger.info("Sample articles seeded successfully")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error seeding sample articles: {e}")
        raise

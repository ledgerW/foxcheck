from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from config import settings
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Update the connection string to use asyncpg and remove sslmode
DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
DATABASE_URL = re.sub(r'\?sslmode=\w+', '', DATABASE_URL)

# Create engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=0,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800  # Recycle connections after 30 minutes
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def create_db_and_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

@asynccontextmanager
async def get_session_context():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def get_session():
    """Dependency that yields database sessions with retry logic"""
    async with get_session_context() as session:
        yield session

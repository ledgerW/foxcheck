from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text
from config import settings
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from models import User, Article, Statement

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
    pool_recycle=1800
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def drop_and_recreate_tables():
    """Drop and recreate all database tables"""
    try:
        async with engine.begin() as conn:
            # Drop all tables with CASCADE
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            # Create all tables
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables recreated successfully")
    except Exception as e:
        logger.error(f"Error in database reset: {e}")
        raise

async def seed_sample_articles(session: AsyncSession):
    """Seed the database with sample articles and related data."""
    try:
        # Import get_password_hash here to avoid circular import
        from auth import get_password_hash
        
        # Create a test user if not exists
        result = await session.execute(
            text("SELECT id FROM \"user\" WHERE username = :username"),
            {"username": "testuser"}
        )
        existing_user = result.scalar()
        
        if not existing_user:
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
        else:
            user_id = existing_user

        # Check if articles already exist
        result = await session.execute(text("SELECT COUNT(*) FROM article"))
        article_count = result.scalar()
        
        if article_count and article_count > 0:
            logger.info("Articles already exist, skipping seed data")
            return

        # Sample articles data
        articles_data = [
            {
                "title": "Climate Change Impact on Ocean Levels",
                "text": "Recent studies show significant changes in ocean levels across the globe.",
                "domain": "climate-science.org",
                "authors": "Dr. Jane Smith, Dr. John Doe",
                "publication_date": datetime.utcnow() - timedelta(days=5),
                "statements": [
                    {
                        "content": "Global sea levels have risen by 8-9 inches since 1880.",
                        "verdict": "True",
                        "explanation": "This statement is supported by multiple scientific studies.",
                        "references": [
                            {
                                'title': 'Ocean Level Study 2024',
                                'source': 'https://climate-science.org/ocean-study-2024',
                                'summary': 'Comprehensive analysis of global sea level changes'
                            }
                        ]
                    }
                ]
            }
        ]

        # Create articles with their statements
        for article_data in articles_data:
            statements_data = article_data.pop("statements")
            
            article = Article(**article_data, user_id=user_id)
            session.add(article)
            await session.commit()
            await session.refresh(article)

            # Add statements with references
            for stmt_data in statements_data:
                references = stmt_data.pop("references")
                statement = Statement(**stmt_data, article_id=article.id, user_id=user_id)
                statement.set_references(references)
                session.add(statement)

            await session.commit()

        logger.info("Sample articles seeded successfully")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error seeding sample articles: {e}")
        raise

async def create_db_and_tables():
    try:
        await drop_and_recreate_tables()
            
        # Seed sample articles after creating tables
        async with async_session_maker() as session:
            await seed_sample_articles(session)
            
    except Exception as e:
        logger.error(f"Error in database initialization: {e}")
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
    """Dependency that yields database sessions"""
    async with get_session_context() as session:
        yield session

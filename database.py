from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text
from config import settings
import os
import re
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from models import User, Article, Statement, get_table_name

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

async def init_db():
    """Drop and recreate all database tables"""
    # Only drop and recreate tables if not in production
    is_production = os.getenv("REPLIT_DEPLOYMENT") == "1"
    try:
        if is_production:
            print("Production mode - skipping table drop/recreate to protect user data.")
            # Optionally, create tables if they don’t exist without dropping existing ones
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all, checkfirst=True)
            #SQLModel.metadata.create_all(engine, checkfirst=True)
        else:
            async with engine.begin() as conn:
                # Drop all tables with CASCADE
                await conn.run_sync(SQLModel.metadata.drop_all)
                # Create all tables
                await conn.run_sync(SQLModel.metadata.create_all)
                logger.info("Database tables recreated successfully")
    except Exception as e:
        logger.error(f"Error in database reset: {e}")
        raise

async def update_admin_user(session: AsyncSession):
    """Update the test user to have admin privileges"""
    try:
        result = await session.execute(
            text(f"SELECT id FROM \"{get_table_name('user')}\" WHERE username = :username"),
            {"username": "ledger"}
        )
        user_id = result.scalar()
        
        if user_id:
            await session.execute(
                text(f"UPDATE \"{get_table_name('user')}\" SET is_admin = TRUE WHERE id = :user_id"),
                {"user_id": user_id}
            )
            await session.commit()
            logger.info("Admin user updated successfully")
    except Exception as e:
        logger.error(f"Error updating admin user: {e}")
        await session.rollback()
        raise

async def seed_admin_and_sample_articles(session: AsyncSession, sample_articles: bool=False):
    """Seed the database with sample articles and related data."""
    try:
        # Import get_password_hash here to avoid circular import
        from auth import get_password_hash
        
        # Create a test user if not exists
        result = await session.execute(
            text(f"SELECT id FROM \"{get_table_name('user')}\" WHERE username = :username"),
            {"username": "ledger"}
        )
        existing_user = result.scalar()
        
        if not existing_user:
            test_user = User(
                username="ledger",
                email="ledger.west@gmail.com",
                hashed_password=get_password_hash("ledger2134"),
                is_active=True,
                is_admin=True  # Set is_admin to True for the test user
            )
            session.add(test_user)
            await session.commit()
            await session.refresh(test_user)
            user_id = test_user.id
        else:
            user_id = existing_user
            # Update existing test user to be admin
            await update_admin_user(session)

        if sample_articles:
            # Check if articles already exist
            result = await session.execute(text(f"SELECT COUNT(*) FROM {get_table_name('article')}"))
            article_count = result.scalar()
            
            if article_count and article_count > 0:
                logger.info("Articles already exist, skipping seed data")
                return
    
            # Sample articles data
            articles_data = [
                {
                    "title": "Climate Change Impact on Ocean Levels",
                    "text": "Recent studies show significant changes in ocean levels across the globe.",
                    "domain": "http://climate-science.org/climate-change-impact-on-ocean",
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
        await init_db()
            
        # Seed sample articles after creating tables
        async with async_session_maker() as session:
            await seed_admin_and_sample_articles(session)
            
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

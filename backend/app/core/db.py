from app.core.config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_async_engine(
    settings.database_url, echo=settings.debug, pool_pre_ping=True
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def check_database() -> None:
    """Verify the database connection on startup."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def ensure_telegram_tables() -> None:
    """Create helper tables for Telegram idempotency and thread storage."""
    ddl_updates = text(
        """
        CREATE TABLE IF NOT EXISTS processed_updates (
            update_id BIGINT PRIMARY KEY,
            processed_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )
    ddl_users = text(
        """
        CREATE TABLE IF NOT EXISTS telegram_users (
            chat_id BIGINT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    )

    async with engine.begin() as conn:
        await conn.execute(ddl_updates)
        await conn.execute(ddl_users)

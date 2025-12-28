import logging
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import UUID, Column, DateTime, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from alembic import command
from alembic.config import Config

load_dotenv()

# 默认使用异步 sqlite 驱动 aiosqlite
_DEFAULT_SQLITE = "sqlite+aiosqlite:///./data/app.sqlite"

# 支持通过环境变量 `DATABASE_URL` 切换为 Postgres（推荐带 asyncpg 驱动）
# 如果用户提供常见的 postgres URI（postgres:// 或 postgresql://），
# 会自动把 scheme 转换为 `postgresql+asyncpg://` 以使用 asyncpg
raw_db_url = os.getenv("DATABASE_URL", "").strip()
if raw_db_url:
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    DATABASE_URL = raw_db_url
else:
    DATABASE_URL = _DEFAULT_SQLITE

# 对 sqlite 使用特定 connect_args（aiosqlite 的 check_same_thread）
if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_size=20,  # 增加连接池大小
        max_overflow=40,  # 允许超出连接池的额外连接数
        pool_pre_ping=True,  # 连接前ping确保连接有效
        pool_recycle=3600,  # 1小时后回收连接
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=20,  # 增加连接池大小
        max_overflow=40,  # 允许超出连接池的额外连接数
        pool_pre_ping=True,  # 连接前ping确保连接有效
        pool_recycle=3600,  # 1小时后回收连接
    )

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


logger = logging.getLogger(__name__)


def run_migrations():
    try:
        logger.info("Running database migrations...")
        # Assuming alembic.ini is in the current working directory or parent directory
        # We can try to locate it
        alembic_ini_path = "alembic.ini"
        if not os.path.exists(alembic_ini_path):
            # Try looking one level up if we are running from app/
            alembic_ini_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "alembic.ini",
            )

        if not os.path.exists(alembic_ini_path):
            logger.warning("alembic.ini not found, skipping migrations.")
            return

        alembic_cfg = Config(alembic_ini_path)
        # Ensure script_location is absolute or correct relative to CWD
        # If alembic.ini has script_location = alembic, it expects alembic folder in CWD.
        # If we are in api/, it works.

        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        # Re-raise to fail startup if migration fails
        raise e

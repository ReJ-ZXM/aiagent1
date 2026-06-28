"""FastAPI 依赖注入"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db as _get_db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session

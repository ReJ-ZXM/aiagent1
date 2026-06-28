"""FastAPI 依赖注入"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db as _get_db
from app.services.auth_service import decode_token

security = HTTPBearer(auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> str | None:
    """可选认证：有 token 返回 user_id，没有返回 None"""
    if credentials:
        uid = decode_token(credentials.credentials)
        if uid:
            return uid
    return None

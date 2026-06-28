"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials
from app.api.deps import get_db, get_current_user, security
from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_token, decode_token

router = APIRouter(tags=["auth"])

class RegisterReq(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    email: str = Field(default="")
    home_city: str = Field(default="上海")

class LoginReq(BaseModel):
    username: str
    password: str

class AuthResp(BaseModel):
    token: str
    user: dict

@router.post("/auth/register")
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.username == req.username))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "用户名已存在")
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        home_city=req.home_city,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_token(user.id)
    return AuthResp(token=token, user={"id": user.id, "username": user.username, "home_city": user.home_city})

@router.post("/auth/login")
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.username == req.username))).scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = create_token(user.id)
    return AuthResp(token=token, user={"id": user.id, "username": user.username, "home_city": user.home_city})

@router.get("/auth/me")
async def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """从 JWT token 恢复用户信息"""
    if not credentials:
        raise HTTPException(401, "未登录")
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(401, "token 无效或已过期")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    return {"user": {"id": user.id, "username": user.username, "home_city": user.home_city}}

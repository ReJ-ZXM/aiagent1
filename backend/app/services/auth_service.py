"""认证服务 — JWT + 密码哈希"""
import hashlib
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.config import settings

SECRET = settings.secret_key
ALGORITHM = "HS256"

def hash_password(pw: str) -> str:
    salt = os.urandom(32).hex()
    h = hashlib.sha256((pw + salt).encode()).hexdigest()
    return f"{salt}${h}"

def verify_password(pw: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split("$", 1)
        return hashlib.sha256((pw + salt).encode()).hexdigest() == h
    except Exception:
        return False

def create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=30)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

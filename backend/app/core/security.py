from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

import hashlib

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    # 支持 sha256 盐值与简单匹配
    if hashed_password.startswith("sha256$"):
        _, salt, h = hashed_password.split("$")
        check = hashlib.sha256((salt + plain_password).encode('utf-8')).hexdigest()
        return check == h
    try:
        return pwd_context.verify(plain_password[:72], hashed_password)
    except Exception:
        return plain_password == hashed_password

def get_password_hash(password: str) -> str:
    salt = "exam_salt_2026"
    h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"sha256${salt}${h}"

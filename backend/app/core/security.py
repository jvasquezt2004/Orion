"""Password hashing and JWT utilities.

Note: pwdlib is FastAPI's current recommendation for password hashing
but is classified as "4 - Beta" (see https://pypi.org/project/pwdlib/).
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import config

# Argon2id via pwdlib — verify(plain, hashed) arg order
pwd_context = PasswordHash.recommended()


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, key=config.secret_key, algorithm=config.algorithm)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=config.refresh_token_expire_days)
    payload = {"sub": user_id, "jti": jti, "exp": expire}
    token = jwt.encode(payload, key=config.secret_key, algorithm=config.algorithm)
    return token, jti


def decode_token(token: str) -> dict:
    return jwt.decode(token, key=config.secret_key, algorithms=[config.algorithm])

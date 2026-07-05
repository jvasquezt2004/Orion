"""Auth router — register, login, refresh, logout, me.

Note: OAuth2PasswordRequestForm requires python-multipart, which is
transitively provided by fastapi[standard].
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

import jwt
from beanie import UpdateResponse
from beanie.operators import Set
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.token import Token
from app.db.user import User
from app.schemas.auth import UserRegister, UserResponse, TokenResponse, RefreshRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Endpoints ---


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: UserRegister):
    existing = await User.find_one(User.email == body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(body.password)
    user = User(email=body.email, hashed_password=hashed)
    await user.insert()
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.email == form.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user_id = str(user.id)
    access_token = create_access_token(user_id)
    refresh_token, jti = create_refresh_token(user_id)

    # Decode refresh token to get expiry for the Token document
    payload = jwt.decode(refresh_token, options={"verify_signature": False})
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    token_doc = Token(jti=jti, user_id=user.id, expires_at=expires_at)
    await token_doc.insert()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    jti = payload.get("jti")
    if jti is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Atomic revoke via findOneAndUpdate (D6): the revoked==False precondition
    # is part of the atomic filter. If a concurrent request already revoked
    # this token, the filter matches zero docs → None → 401 (TOCTOU-safe).
    result = await Token.find_one(
        Token.jti == jti, Token.revoked == False
    ).update(
        Set({Token.revoked: True}),
        response_type=UpdateResponse.NEW_DOCUMENT,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = str(payload["sub"])
    new_access = create_access_token(user_id)
    new_refresh, new_jti = create_refresh_token(user_id)

    new_payload = jwt.decode(new_refresh, options={"verify_signature": False})
    expires_at = datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc)

    new_token_doc = Token(jti=new_jti, user_id=UUID(user_id), expires_at=expires_at)
    await new_token_doc.insert()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", status_code=200)
async def logout(body: RefreshRequest, current_user: User = Depends(get_current_user)):
    try:
        payload = decode_token(body.refresh_token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        # Idempotent — even if the token is invalid/expired, return 200
        return {"detail": "Logged out"}

    jti = payload.get("jti")
    sub = payload.get("sub")

    # Validate that the refresh token belongs to the current user
    if sub != str(current_user.id):
        return {"detail": "Logged out"}

    if jti:
        token_doc = await Token.find_one(Token.jti == jti)
        if token_doc:
            await token_doc.update(Set({Token.revoked: True}))

    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )

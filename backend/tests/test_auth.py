"""Auth endpoint tests — covers all spec auth scenarios."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import jwt
import pytest
from beanie import UpdateResponse
from beanie.operators import Set
from pydantic import ValidationError

from app.core.config import Config
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.token import Token
from app.db.user import User


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


async def test_hash_and_verify_password():
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert verify_password("mysecretpassword", hashed)
    assert not verify_password("wrongpassword", hashed)


# ---------------------------------------------------------------------------
# JWT encode / decode round-trip
# ---------------------------------------------------------------------------


async def test_access_token_round_trip():
    user_id = str(uuid4())
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload


async def test_refresh_token_round_trip():
    user_id = str(uuid4())
    token, jti = create_refresh_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["jti"] == jti
    assert "exp" in payload


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def test_register_success(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "password": "securepass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "hashed_password" not in data
    assert "id" in data
    assert "created_at" in data


async def test_register_duplicate_email_409(client):
    payload = {"email": "dup@example.com", "password": "securepass123"}
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


async def test_register_invalid_email_422(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 422


async def test_register_short_password_422(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "short@example.com", "password": "short"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_valid(client):
    await client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "securepass123"},
    )
    response = await client.post(
        "/api/auth/login",
        data={"username": "login@example.com", "password": "securepass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_401(client):
    await client.post(
        "/api/auth/register",
        json={"email": "wrongpw@example.com", "password": "securepass123"},
    )
    response = await client.post(
        "/api/auth/login",
        data={"username": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_unknown_user_401(client):
    response = await client.post(
        "/api/auth/login",
        data={"username": "nobody@example.com", "password": "securepass123"},
    )
    assert response.status_code == 401


async def test_login_inactive_user_401(client, mongo):
    # Create user directly with is_active=False
    hashed = hash_password("securepass123")
    user = User(email="inactive@example.com", hashed_password=hashed, is_active=False)
    await user.insert()

    response = await client.post(
        "/api/auth/login",
        data={"username": "inactive@example.com", "password": "securepass123"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# me endpoint
# ---------------------------------------------------------------------------


async def test_me_valid_token(client, auth_token):
    access_token, _ = auth_token
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "hashed_password" not in data


async def test_me_missing_token_401(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_me_invalid_token_401(client):
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


async def test_me_expired_token_401(client, mongo):
    # Create a user and an access token with past expiry
    user = User(
        email="expired@example.com",
        hashed_password=hash_password("securepass123"),
    )
    await user.insert()

    expired_payload = {
        "sub": str(user.id),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        expired_payload,
        key=os.environ["SECRET_KEY"],
        algorithm="HS256",
    )

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Refresh with rotation
# ---------------------------------------------------------------------------


async def test_refresh_valid_issues_new_pair(client, auth_token, mongo):
    _, refresh_token = auth_token
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token

    # Old refresh token's record should be revoked
    # Find the old token by decoding it
    old_payload = decode_token(refresh_token)
    old_jti = old_payload["jti"]
    old_token_doc = await Token.find_one(Token.jti == old_jti)
    assert old_token_doc is not None
    assert old_token_doc.revoked is True


async def test_refresh_revoked_token_401(client, auth_token, mongo):
    _, refresh_token = auth_token

    # Manually revoke the token
    payload = decode_token(refresh_token)
    jti = payload["jti"]
    token_doc = await Token.find_one(Token.jti == jti)
    await token_doc.update(Set({Token.revoked: True}))

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401


async def test_refresh_expired_token_401(client):
    expired_payload = {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(days=1),
    }
    expired_token = jwt.encode(
        expired_payload,
        key=os.environ["SECRET_KEY"],
        algorithm="HS256",
    )

    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": expired_token},
    )
    assert response.status_code == 401


async def test_refresh_already_rotated_401(client, auth_token):
    """Refresh once successfully, then try again with the OLD token → 401."""
    _, old_refresh = auth_token

    # First refresh — should succeed
    first = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert first.status_code == 200

    # Second refresh with the same old token — should fail
    second = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert second.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_invalidates_refresh(client, auth_token):
    access_token, refresh_token = auth_token

    response = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    # Subsequent refresh with the same token → 401
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Missing SECRET_KEY fail-fast
# ---------------------------------------------------------------------------


async def test_missing_secret_key_fail_fast():
    """Config() raises ValidationError when SECRET_KEY is absent."""
    # Clear env AND prevent .env file from being loaded by pydantic-settings
    with patch.dict(os.environ, {}, clear=True):
        with patch("app.core.config.load_dotenv"):
            with patch("pathlib.Path.is_file", return_value=False):
                with pytest.raises(ValidationError):
                    Config()


# ---------------------------------------------------------------------------
# Atomic-revoke unit test (design D6 concurrency-safety guarantee)
# ---------------------------------------------------------------------------


async def test_atomic_revoke_returns_none_on_already_revoked(mongo):
    """D6 concurrency-safety: the atomic findOneAndUpdate with revoked==False
    precondition returns None when the token is already revoked — so a
    concurrent second request cannot reuse the same refresh token.
    """
    jti = str(uuid4())
    user_id = uuid4()

    # Insert an already-revoked token
    token = Token(
        jti=jti,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=True,
    )
    await token.insert()

    # The atomic findOneAndUpdate with precondition revoked==False matches
    # zero docs → returns None (not the document). This is the TOCTOU-safe
    # guarantee: only one concurrent request can flip revoked False→True.
    result = await Token.find_one(
        Token.jti == jti, Token.revoked == False
    ).update(
        Set({Token.revoked: True}),
        response_type=UpdateResponse.NEW_DOCUMENT,
    )
    assert result is None

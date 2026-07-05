import logging
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_token
from app.db.user import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate access token and return the current user.

    Per design D8: all token failures (missing/invalid/expired) map to
    a uniform 401. Distinction is logged at debug level only.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        logger.debug("Access token expired")
        raise credentials_exception
    except jwt.InvalidTokenError:
        logger.debug("Invalid access token")
        raise credentials_exception

    user = await User.get(UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    return user

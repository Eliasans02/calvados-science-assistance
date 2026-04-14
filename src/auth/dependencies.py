"""FastAPI dependencies for authenticated and optional users."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.container import get_container


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> dict:
    container = get_container(request)
    user = container.auth_service.get_user_by_token(credentials.credentials)
    request.state.user_id = user["id"]
    return user


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    if not credentials:
        return None
    container = get_container(request)
    user = container.auth_service.get_user_by_token(credentials.credentials)
    request.state.user_id = user["id"]
    return user

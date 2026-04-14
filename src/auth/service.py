"""User registration, login and token-based session management."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from src.auth.security import hash_password, verify_password
from src.data.repository import BackendRepository


class AuthService:
    def __init__(self, repository: BackendRepository) -> None:
        self._repository = repository

    def register(self, email: str, password: str, name: str) -> dict[str, Any]:
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )
        existing = self._repository.get_user_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        return self._repository.create_user(
            email=email,
            name=name,
            password_hash=hash_password(password),
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        user = self._repository.get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        session = self._repository.create_session(user_id=user["id"])
        return {
            "access_token": session["token"],
            "token_type": "bearer",
            "expires_at": session["expires_at"],
            "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        }

    def get_user_by_token(self, token: str) -> dict[str, Any]:
        session = self._repository.get_session(token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        user = self._repository.get_user_by_id(session["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for this token",
            )
        return {"id": user["id"], "email": user["email"], "name": user["name"]}

    def ensure_external_user(self, user_id: str) -> dict[str, Any]:
        return self._repository.ensure_external_user(user_id)

"""Agent helpers."""

from __future__ import annotations

from typing import Optional, Tuple

from fastapi import HTTPException, status

from src.data.repository import BackendRepository


def resolve_text(repository: BackendRepository, user_id: str, payload: dict) -> Tuple[str, Optional[str]]:
    text = (payload.get("text") or "").strip()
    file_id = payload.get("file_id")
    if text:
        return text, file_id
    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'text' or 'file_id' is required",
        )
    file_record = repository.get_file(file_id=file_id, user_id=user_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return file_record["normalized_text"], file_id

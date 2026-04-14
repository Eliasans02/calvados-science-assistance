from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from src.auth.dependencies import get_optional_user
from src.core.container import get_container

router = APIRouter()


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(default=None),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    container = get_container(request)
    resolved_user_id = current_user["id"] if current_user else (user_id or "").strip()
    if not resolved_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provide Bearer token or form field 'user_id'",
        )
    if not container.repository.get_user_by_id(resolved_user_id):
        container.auth_service.ensure_external_user(resolved_user_id)
    request.state.user_id = resolved_user_id
    raw = await file.read()
    result = container.file_service.save_and_normalize(
        user_id=resolved_user_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        raw_content=raw,
    )
    return result

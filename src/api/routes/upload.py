from fastapi import APIRouter, Depends, File, Request, UploadFile

from src.auth.dependencies import get_current_user
from src.core.container import get_container

router = APIRouter()


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    container = get_container(request)
    raw = await file.read()
    result = container.file_service.save_and_normalize(
        user_id=current_user["id"],
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        raw_content=raw,
    )
    return result

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.dependencies import get_current_user
from src.core.container import get_container

router = APIRouter()


@router.get("/history")
def get_history(request: Request, current_user: dict = Depends(get_current_user)):
    container = get_container(request)
    return container.history_service.list_documents(user_id=current_user["id"])


@router.get("/history/{file_id}")
def get_history_item(file_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    container = get_container(request)
    try:
        return container.history_service.get_document_details(
            user_id=current_user["id"],
            file_id=file_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

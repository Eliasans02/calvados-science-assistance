from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse

from src.auth.dependencies import get_current_user
from src.core.container import get_container

router = APIRouter()


@router.get("/report/{file_id}/download")
def download_report(
    file_id: str,
    request: Request,
    format: Literal["md", "json"] = Query(default="md"),
    current_user: dict = Depends(get_current_user),
):
    container = get_container(request)
    report = container.repository.get_latest_report(user_id=current_user["id"], file_id=file_id)
    if report is None:
        container.report_service.compose(user_id=current_user["id"], file_id=file_id)
        report = container.repository.get_latest_report(user_id=current_user["id"], file_id=file_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report is not available")

    base_md = Path(report["report_path"])
    target = base_md if format == "md" else base_md.with_suffix(".json")
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report file not found: {target.name}")
    media_type = "text/markdown" if format == "md" else "application/json"
    return FileResponse(path=str(target), media_type=media_type, filename=target.name)

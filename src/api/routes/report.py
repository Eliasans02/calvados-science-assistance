from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse

from src.auth.dependencies import get_optional_user
from src.core.container import get_container

router = APIRouter()


@router.get("/report/{file_id}/download")
def download_report(
    file_id: str,
    request: Request,
    format: Literal["md", "json", "xlsx"] = Query(default="md"),
    user_id: Optional[str] = Query(default=None),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    container = get_container(request)
    resolved_user_id = current_user["id"] if current_user else (user_id or "").strip()
    if not resolved_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provide Bearer token or query param 'user_id'",
        )
    if not container.repository.get_user_by_id(resolved_user_id):
        container.auth_service.ensure_external_user(resolved_user_id)
    request.state.user_id = resolved_user_id

    report = container.repository.get_latest_report(user_id=resolved_user_id, file_id=file_id)
    if report is None:
        container.report_service.compose(user_id=resolved_user_id, file_id=file_id)
        report = container.repository.get_latest_report(user_id=resolved_user_id, file_id=file_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report is not available")

    base_md = Path(report["report_path"])
    if format == "md":
        target = base_md
        media_type = "text/markdown"
    elif format == "json":
        target = base_md.with_suffix(".json")
        media_type = "application/json"
    else:
        target = base_md.with_suffix(".xlsx")
        if not target.exists():
            container.report_service.render_template_xlsx(report_payload=report["report_json"], output_path=target)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report file not found: {target.name}")
    return FileResponse(path=str(target), media_type=media_type, filename=target.name)


@router.get("/generation/{file_id}/download")
def download_generated_tz_docx(
    file_id: str,
    request: Request,
    user_id: Optional[str] = Query(default=None),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    container = get_container(request)
    resolved_user_id = current_user["id"] if current_user else (user_id or "").strip()
    if not resolved_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provide Bearer token or query param 'user_id'",
        )
    if not container.repository.get_user_by_id(resolved_user_id):
        container.auth_service.ensure_external_user(resolved_user_id)
    request.state.user_id = resolved_user_id

    latest = container.repository.get_latest_agent_result(
        user_id=resolved_user_id,
        file_id=file_id,
        agent_name="generation",
    )
    if latest is None:
        container.agent_registry.execute(
            agent_name="generation",
            user_id=resolved_user_id,
            payload={"file_id": file_id, "context": {}},
        )
        latest = container.repository.get_latest_agent_result(
            user_id=resolved_user_id,
            file_id=file_id,
            agent_name="generation",
        )
    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation result is not available")

    path_raw = (latest.get("output_json") or {}).get("generated_docx_path")
    if not path_raw:
        container.agent_registry.execute(
            agent_name="generation",
            user_id=resolved_user_id,
            payload={"file_id": file_id, "context": {}},
        )
        latest = container.repository.get_latest_agent_result(
            user_id=resolved_user_id,
            file_id=file_id,
            agent_name="generation",
        )
        path_raw = (latest.get("output_json") or {}).get("generated_docx_path") if latest else None
    if not path_raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated DOCX path is missing")
    target = Path(path_raw)
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Generated DOCX not found: {target.name}")
    return FileResponse(
        path=str(target),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=target.name,
    )

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.auth.dependencies import get_current_user
from src.core.container import get_container
from src.utils.schemas import ChatRequest

router = APIRouter()


AGENT_NAME_ALIASES = {
    "text_analysis": "text-analysis",
    "text-analysis": "text-analysis",
    "requirement_analysis": "requirement-analysis",
    "requirement-analysis": "requirement-analysis",
    "structure": "structure",
    "generation": "generation",
    "recommendation": "recommendation",
    "scoring": "scoring",
    "compliance": "compliance",
    "report": "report",
}


@router.post("/chat")
def chat(
    payload: ChatRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    container = get_container(request)
    agent_name = AGENT_NAME_ALIASES.get(payload.agent_name)
    if not agent_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown agent_name")

    request_payload = {
        "file_id": payload.file_id,
        "text": payload.context.get("text"),
        "context": {"chat_message": payload.message, **payload.context},
    }
    result = container.agent_registry.execute(
        agent_name=agent_name,
        user_id=current_user["id"],
        payload=request_payload,
    )
    container.repository.save_chat_message(
        user_id=current_user["id"],
        file_id=payload.file_id,
        message=payload.message,
        agent_name=agent_name,
        response_payload=result,
    )
    return {"agent": agent_name, "response": result}


@router.get("/chat/history")
def chat_history(
    request: Request,
    file_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    container = get_container(request)
    items = container.repository.list_chat_messages(
        user_id=current_user["id"],
        file_id=file_id,
        limit=limit,
    )
    return {"items": items, "total": len(items)}

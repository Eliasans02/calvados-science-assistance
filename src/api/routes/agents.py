from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.dependencies import get_optional_user
from src.core.container import get_container
from src.utils.schemas import AgentRequest

router = APIRouter()


def _resolve_user_id(payload: AgentRequest, user: Optional[dict]) -> str:
    if user:
        return user["id"]
    if payload.user_id:
        return payload.user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide Bearer token or user_id",
    )


def _execute(agent_name: str, payload: AgentRequest, request: Request, user: Optional[dict]) -> dict:
    container = get_container(request)
    user_id = _resolve_user_id(payload, user)
    if not container.repository.get_user_by_id(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    request.state.user_id = user_id
    result = container.agent_registry.execute(
        agent_name=agent_name,
        user_id=user_id,
        payload=payload.model_dump(),
    )
    return {"agent": agent_name, "result": result}


@router.post("/text-analysis")
def text_analysis(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("text-analysis", payload, request, user)


@router.post("/requirement-analysis")
def requirement_analysis(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("requirement-analysis", payload, request, user)


@router.post("/structure")
def structure(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("structure", payload, request, user)


@router.post("/generation")
def generation(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("generation", payload, request, user)


@router.post("/recommendation")
def recommendation(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("recommendation", payload, request, user)


@router.post("/scoring")
def scoring(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("scoring", payload, request, user)


@router.post("/compliance")
def compliance(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("compliance", payload, request, user)


@router.post("/report")
def report(payload: AgentRequest, request: Request, user: Optional[dict] = Depends(get_optional_user)):
    return _execute("report", payload, request, user)

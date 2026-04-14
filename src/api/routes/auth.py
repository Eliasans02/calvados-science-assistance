from fastapi import APIRouter, Depends, Request

from src.auth.dependencies import get_current_user
from src.core.container import get_container
from src.utils.schemas import LoginRequest, RegisterRequest

router = APIRouter()


@router.post("/register")
def register(payload: RegisterRequest, request: Request):
    container = get_container(request)
    user = container.auth_service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    return {"user": user}


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    container = get_container(request)
    return container.auth_service.login(email=payload.email, password=payload.password)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

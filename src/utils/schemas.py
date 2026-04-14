"""Pydantic request/response contracts."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = "Hackathon User"


class LoginRequest(BaseModel):
    email: str
    password: str


class AgentRequest(BaseModel):
    file_id: Optional[str] = None
    user_id: Optional[str] = None
    text: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    agent_name: str = "recommendation"
    file_id: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)

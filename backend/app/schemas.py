"""Pydantic request/response schemas."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid email address")
        return v.lower()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


from datetime import datetime

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    mode: str = Field(default="chat", pattern="^(chat|analyze|code|detect)$")
    target: Optional[str] = None  # for detect mode


class ChatResponse(BaseModel):
    reply: str
    decision: str = "allowed"
    tool: str = "none"
    used_rag: bool = False
    quota_left: Optional[int] = None


class DetectRequest(BaseModel):
    tool: str
    target: str
    args: List[str] = Field(default_factory=list)


class DetectResponse(BaseModel):
    output: str
    decision: str = "allowed"
    tool: str
    exit_code: int = 0
    duration_s: float = 0.0


class RoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(admin|pro|free)$")

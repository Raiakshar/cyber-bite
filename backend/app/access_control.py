"""Role-based access control.

- admin : full control, manages users & quotas
- pro   : "selected user" -> FREE, UNLIMITED access (the feature you asked for)
- free  : limited daily quota, limited modes, no tools

Admins promote users to "pro" via the admin panel / endpoint.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Memory, UsageCounter, User
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


class RolePolicy:
    def __init__(self, name: str, unlimited: bool, daily_messages: int,
                 daily_tokens: int, tool_calls: int, modes: List[str]):
        self.name = name
        self.unlimited = unlimited
        self.daily_messages = daily_messages
        self.daily_tokens = daily_tokens
        self.tool_calls = tool_calls
        self.modes = modes


ROLE_POLICIES = {
    "admin": RolePolicy("admin", unlimited=True, daily_messages=-1, daily_tokens=-1,
                        tool_calls=-1, modes=["chat", "analyze", "code", "detect"]),
    # ---- SELECTED USERS: full free unlimited access ----
    "pro": RolePolicy("pro", unlimited=True, daily_messages=-1, daily_tokens=-1,
                      tool_calls=-1, modes=["chat", "analyze", "code", "detect"]),
    # ---- PUBLIC ACCESS: free users can use all modes/tools ----
    "free": RolePolicy("free", unlimited=True,
                       daily_messages=-1,
                       daily_tokens=-1,
                       tool_calls=-1,
                       modes=["chat", "analyze", "code", "detect"]),
}


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def policy_for(user: User) -> RolePolicy:
    return ROLE_POLICIES.get(user.role, ROLE_POLICIES["free"])


def _today() -> str:
    return date.today().isoformat()


def get_usage(db: Session, user: User) -> Optional[UsageCounter]:
    return (
        db.query(UsageCounter)
        .filter(UsageCounter.user_id == user.id, UsageCounter.day == _today())
        .first()
    )


def quota_left(db: Session, user: User) -> int:
    """Messages remaining today. -1 means unlimited."""
    pol = policy_for(user)
    if pol.unlimited:
        return -1
    used = get_usage(db, user)
    used_m = used.messages if used else 0
    return max(0, pol.daily_messages - used_m)


def check_mode_access(user: User, mode: str) -> None:
    pol = policy_for(user)
    if mode not in pol.modes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your account cannot use the '{mode}' mode. "
                   f"Available: {', '.join(pol.modes)}",
        )


def check_and_consume(db: Session, user: User, mode: str,
                      est_tokens: int = 0) -> Optional[int]:
    """Enforce free-user limits; returns remaining messages (-1 = unlimited)."""
    pol = policy_for(user)
    if pol.unlimited:
        return -1

    usage = get_usage(db, user)
    if usage is None:
        usage = UsageCounter(user_id=user.id, day=_today(), messages=0, tokens=0, tool_calls=0)
        db.add(usage)

    if usage.messages >= pol.daily_messages:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily message limit reached ({pol.daily_messages}). "
                   f"Resets at midnight. Ask an admin to upgrade you to a selected (pro) user.",
        )
    if pol.daily_tokens > 0 and usage.tokens + est_tokens > pol.daily_tokens:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily token limit reached ({pol.daily_tokens}).",
        )

    usage.messages += 1
    usage.tokens += est_tokens
    db.commit()
    return max(0, pol.daily_messages - usage.messages)


def check_tool_quota(db: Session, user: User) -> None:
    pol = policy_for(user)
    if pol.tool_calls < 0:
        return
    usage = get_usage(db, user)
    used = usage.tool_calls if usage else 0
    if pol.tool_calls == 0 or used >= pol.tool_calls:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tool execution is not available for your account tier. "
                   "Ask an admin to upgrade you to a selected (pro) user.",
        )
    if usage is None:
        usage = UsageCounter(user_id=user.id, day=_today(), messages=0, tokens=0, tool_calls=0)
        db.add(usage)
    usage.tool_calls += 1
    db.commit()


def save_memory(db: Session, user: User, key: str, value: str) -> None:
    """Note 8 - safe memory only: project/target/findings/preferences."""
    mem = db.query(Memory).filter(Memory.user_id == user.id, Memory.key == key).first()
    if mem:
        mem.value = value
    else:
        db.add(Memory(user_id=user.id, key=key, value=value))
    db.commit()

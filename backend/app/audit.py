"""Audit logging - Note 8: every action is recorded for review & debugging."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .models import AuditLog, User


def log_action(
    db: Session,
    user: User,
    mode: str,
    request_text: str,
    decision: str = "allowed",
    tool: str = "none",
    result: str = "",
    ip: str = "",
) -> None:
    entry = AuditLog(
        user_id=user.id,
        username=user.username,
        mode=mode,
        request_text=request_text[:2000],
        decision=decision,
        tool=tool,
        result=result[:2000],
        ip=ip,
    )
    db.add(entry)
    db.commit()

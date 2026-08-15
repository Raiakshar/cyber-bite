"""Admin panel - manage users, promote 'selected users' (pro), view audit logs.

The key feature: admins promote users to role "pro" -> those users get FREE,
UNLIMITED access. Everyone else stays on the limited 'free' tier.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..access_control import ROLE_POLICIES, get_current_user, require_admin
from ..database import get_db
from ..models import AuditLog, User
from ..schemas import RoleUpdateRequest, UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list)
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id).all()
    return [
        {
            "id": u.id, "username": u.username, "email": u.email,
            "role": u.role, "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
def set_role(user_id: int, body: RoleUpdateRequest,
             db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if body.role not in ROLE_POLICIES:
        raise HTTPException(status_code=400, detail="Invalid role")
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id and body.role != "admin":
        raise HTTPException(status_code=400, detail="You cannot demote yourself")
    target.role = body.role
    db.commit()
    return {"id": target.id, "username": target.username, "role": target.role}


@router.get("/logs")
def list_logs(limit: int = 100, db: Session = Depends(get_db),
              admin: User = Depends(require_admin)):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(min(limit, 500))
        .all()
    )
    return [
        {
            "timestamp": l.timestamp.isoformat() if l.timestamp else "",
            "username": l.username, "mode": l.mode,
            "request": l.request_text[:300], "decision": l.decision,
            "tool": l.tool, "result": l.result[:300],
        }
        for l in logs
    ]


@router.get("/usage")
def usage_summary(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    from ..models import UsageCounter
    rows = db.query(UsageCounter).order_by(UsageCounter.day.desc()).limit(30).all()
    return [
        {"user_id": r.user_id, "day": r.day, "messages": r.messages,
         "tokens": r.tokens, "tool_calls": r.tool_calls}
        for r in rows
    ]

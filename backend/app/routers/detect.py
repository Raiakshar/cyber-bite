"""DETECT mode - execute security tools inside the isolated lab sandbox (Notes 2, 7, 9)."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..access_control import check_tool_quota, get_current_user
from ..audit import log_action
from ..database import get_db
from ..models import User
from ..sandbox import SandboxError
from ..schemas import DetectRequest, DetectResponse
from ..tool_router import TOOL_REGISTRY, run_tool

router = APIRouter(prefix="/api/detect", tags=["detect"])


@router.get("/tools")
def list_tools():
    return [
        {"name": name, **spec}
        for name, spec in TOOL_REGISTRY.items()
    ]


@router.post("/run", response_model=DetectResponse)
def run_detect(
    body: DetectRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in ("admin", "pro"):
        return JSONResponse(
            status_code=403,
            content=DetectResponse(
                output="Tool execution requires a selected (pro) or admin account.",
                decision="blocked", tool=body.tool, exit_code=1, duration_s=0.0,
            ).model_dump(),
        )

    check_tool_quota(db, user)

    start = time.time()
    try:
        output, exit_code, duration = run_tool(body.tool, body.target, body.args)
    except SandboxError as e:
        log_action(db, user, "detect", f"{body.tool} {body.target}",
                   "blocked", tool=body.tool, result=str(e),
                   ip=request.client.host if request.client else "")
        return DetectResponse(output=str(e), decision="blocked", tool=body.tool,
                              exit_code=1, duration_s=0.0)
    duration = round(time.time() - start, 2)

    log_action(db, user, "detect", f"{body.tool} {body.target} {' '.join(body.args)}",
               "allowed", tool=body.tool, result=output[:500],
               ip=request.client.host if request.client else "")
    return DetectResponse(output=output, decision="allowed", tool=body.tool,
                          exit_code=exit_code, duration_s=duration)

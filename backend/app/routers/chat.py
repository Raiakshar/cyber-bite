"""CHAT / ANALYZE / CODE / DETECT modes - the AI copilot core (Notes 1, 2, 4, 5)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..access_control import check_and_consume, check_mode_access, get_current_user
from ..audit import log_action
from ..config import settings
from ..database import get_db
from ..llm import HostedLLMError, OllamaError, active_provider_name, get_llm
from ..models import User
from ..policy_engine import classify_request, lab_target_suggestion
from ..rag import knowledge_index
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["copilot"])

BASE_SYSTEM = """You are CyberBite, a cybersecurity laboratory assistant.
Your job is to:
- explain security concepts
- analyze defensive code
- review logs
- help with CTF/lab exercises
- identify vulnerabilities
- write safe proof-of-concept demonstrations
- recommend mitigations
- explain detection techniques

Rules:
- Operate only within authorized environments (local lab, localhost, private lab ranges, .lab/.local hostnames).
- Never expose real credentials, secrets, private data, or destructive payloads.
- When a request is unsafe, explain the risk and redirect toward a controlled laboratory exercise.
- The user's environment is an isolated lab/sandbox. Everything is for educational, research and authorized testing purposes only.
- Be precise, technical and practical. Keep answers focused and actionable."""

MODE_HINTS = {
    "chat": "Answer the question with clear explanations and examples.",
    "analyze": "Analyze the provided logs / code / text. Identify anomalies, suspicious patterns, and security issues, then suggest fixes. Format findings as a short list.",
    "code": "Provide complete, working, safe proof-of-concept code for the requested lab scenario. Explain how it works and how to defend against it. Never include destructive payloads.",
    "detect": "Act as a detection engineer: explain how to detect, investigate and respond to the described activity. Give concrete commands, rules or queries.",
}


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else request.client.host if request.client else ""


def _build_reply(decision: str, reason: str, suggestion: str) -> str:
    if decision == "blocked":
        return (
            f"🚫 **Request blocked by policy engine**\n\n{reason}\n\n"
            f"💡 {suggestion}"
        )
    if decision == "redirected":
        return (
            f"⚠️ **Redirected to a safe lab exercise**\n\n{reason}\n\n"
            f"💡 {suggestion}"
        )
    return ""


def _fallback_reply(mode: str, message: str, context: str, used_rag: bool) -> str:
    """Graceful reply when the LLM backend is temporarily unavailable."""
    mode_guidance = {
        "chat": "I can still help with practical security guidance and next steps.",
        "analyze": "I can still provide a structured first-pass analysis and triage checklist.",
        "code": "I can still provide a safe starter template and implementation guidance.",
        "detect": "I can still provide detection/investigation steps and rules to start with.",
    }.get(mode, "I can still help with safe security guidance.")

    if used_rag and context.strip():
        trimmed = context.strip()
        if len(trimmed) > 1800:
            trimmed = trimmed[:1800].rstrip() + "\n..."
        return (
            f"{mode_guidance}\n\n"
            f"Request: {message}\n\n"
            "Knowledge-based response:\n"
            f"{trimmed}\n\n"
            "If you share more details (target stack, logs, code snippet, expected result), "
            "I will refine this into a tighter step-by-step answer."
        )

    return (
        f"{mode_guidance}\n\n"
        f"Request: {message}\n\n"
        "Quick next steps:\n"
        "1. Share the exact goal and environment.\n"
        "2. Provide logs/errors or code snippets.\n"
        "3. I will return a focused, actionable response."
    )


@router.post("/chat", response_model=ChatResponse)
def copilot_chat(
    body: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Mode access (free users are limited to 'chat' by default)
    check_mode_access(user, body.mode)

    # 2. Policy engine (lab-only guardrails)
    decision, reason, suggestion = classify_request(body.message, body.target)
    if decision != "allowed":
        log_action(db, user, body.mode, body.message, decision, ip=_client_ip(request))
        return ChatResponse(
            reply=_build_reply(decision, reason, suggestion),
            decision=decision,
            quota_left=None,
        )

    # 3. Quota (selected/pro users are unlimited; free users have daily caps)
    est_tokens = len(body.message) // 4 + 400
    left = check_and_consume(db, user, body.mode, est_tokens)

    # 4. RAG: retrieve relevant knowledge from the local knowledge base
    context, used_rag = knowledge_index.context_for(body.message)

    system = BASE_SYSTEM
    if body.mode != "chat":
        system += "\n\nMode: " + MODE_HINTS[body.mode]

    messages = [{"role": "system", "content": system}]
    if used_rag:
        messages.append({
            "role": "system",
            "content": (
                "Relevant knowledge base documents (use them to ground your answer, "
                "cite the source name when you use them):\n" + context
            ),
        })
    if body.target:
        messages.append({"role": "user", "content": f"Lab target in scope: {body.target}"})
    messages.append({"role": "user", "content": body.message})

    # 5. LLM (local Ollama or hosted provider)
    provider = active_provider_name()
    try:
        reply = get_llm().chat(messages)
    except (OllamaError, HostedLLMError) as e:
        reply = _fallback_reply(body.mode, body.message, context, used_rag)
        log_action(
            db,
            user,
            body.mode,
            body.message,
            "allowed",
            result=f"LLM unavailable ({provider}): {str(e)[:350]}",
            ip=_client_ip(request),
        )
        return ChatResponse(reply=reply, decision="allowed", used_rag=used_rag, quota_left=left)

    log_action(db, user, body.mode, body.message, "allowed",
               result=reply[:500], ip=_client_ip(request))
    return ChatResponse(reply=reply, decision="allowed", used_rag=used_rag, quota_left=left)

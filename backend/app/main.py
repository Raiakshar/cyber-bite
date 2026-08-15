"""CyberBite - your local AI security copilot. FastAPI backend."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (register models)
from .config import settings
from .database import Base, SessionLocal, engine
from .llm import active_provider_name, hosted, ollama
from .rag import knowledge_index
from .routers import admin, auth, chat, detect
from .security import hash_password

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(detect.router)
app.include_router(admin.router)


def seed_admin():
    db = SessionLocal()
    try:
        from .models import User
        existing = db.query(User).filter(User.username == settings.admin_username).first()
        if existing is None:
            db.add(User(
                username=settings.admin_username,
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role="admin",
            ))
            db.commit()
            print(f"[+] Admin account created: {settings.admin_username}")
        else:
            print(f"[+] Admin account present: {settings.admin_username}")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    if settings.database_url.startswith("sqlite:///"):
        sqlite_path = settings.database_url.replace("sqlite:///", "", 1)
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    os.makedirs(settings.chroma_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    seed_admin()
    ok = knowledge_index.build()
    print(f"[+] Knowledge index: {'ready (' + knowledge_index.mode + ')' if ok else 'empty (add files under knowledge/)'}")
    provider = active_provider_name()
    if provider == "hosted":
        print(f"[+] LLM provider: hosted ({hosted.model})")
    else:
        print("[+] LLM provider: local Ollama")
        if not ollama.is_available():
            print("[!] Ollama not reachable - start it and pull models:")
            print(f"    ollama pull {settings.ollama_model}")
            print(f"    ollama pull {settings.embed_model}")


@app.get("/health")
def health():
    provider = active_provider_name()
    return {"status": "ok", "app": settings.app_name,
            "llm_provider": provider,
            "llm": getattr(hosted if provider == "hosted" else ollama, "is_available")(),
            "model": hosted.model if provider == "hosted" else settings.ollama_model,
            "rag": knowledge_index.mode,
            "docs": "/docs"}

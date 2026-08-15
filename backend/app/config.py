"""Central configuration - every value can be overridden via environment / .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


def _is_vercel_runtime() -> bool:
    return os.getenv("VERCEL") == "1"


def _default_data_dir() -> str:
    return "/tmp/cyberbite" if _is_vercel_runtime() else "./data"


@dataclass
class Settings:
    app_name: str = "CyberBite Security Copilot"
    env: str = os.getenv("ENV", "dev")

    # --- Database (PostgreSQL in docker-compose, SQLite for dev) ---
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{_default_data_dir()}/cyberbite.db")

    # --- Auth ---
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-cyberbite-use-a-long-random-secret-32b")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # --- AI model (Ollama, local & private) ---
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")

    # --- Hosted LLM (OpenAI-compatible: Groq / OpenAI / OpenRouter / Together ...)
    # Used when available (e.g. serverless production where Ollama cannot run).
    # LLM_PROVIDER: auto (prefer hosted if key set, else Ollama) | hosted | ollama
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto")
    hosted_llm_url: str = os.getenv("HOSTED_LLM_URL", "https://api.groq.com/openai/v1")
    hosted_llm_api_key: str = os.getenv("HOSTED_LLM_API_KEY", "")
    hosted_llm_model: str = os.getenv("HOSTED_LLM_MODEL", "llama-3.3-70b-versatile")

    # --- RAG knowledge base ---
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    knowledge_dir: str = os.getenv("KNOWLEDGE_DIR", "./knowledge")
    chroma_dir: str = os.getenv("CHROMA_DIR", f"{_default_data_dir()}/chroma")

    # --- Tool execution / sandbox ---
    tool_executor: str = os.getenv("TOOL_EXECUTOR", "docker")  # docker | local
    sandbox_image: str = os.getenv("SANDBOX_IMAGE", "cyberbite/lab-tools:latest")
    # absolute HOST path mounted read-only into the sandbox at /data (for file tools like yara)
    sandbox_data_mount: str = os.getenv("SANDBOX_DATA_MOUNT", os.path.join(os.getcwd(), "data"))
    tool_timeout: int = int(os.getenv("TOOL_TIMEOUT", "90"))
    # Only these networks/targets may ever be scanned (lab isolation principle)
    lab_networks: List[str] = field(
        default_factory=lambda: [
            n.strip()
            for n in os.getenv(
                "LAB_NETWORKS",
                "127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
            ).split(",")
            if n.strip()
        ]
    )

    # --- First admin account (created on startup if missing) ---
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@cyberbite.lab")

    # --- Access control / quotas (free vs selected users) ---
    free_daily_messages: int = int(os.getenv("FREE_DAILY_MESSAGES", "10"))
    free_daily_tokens: int = int(os.getenv("FREE_DAILY_TOKENS", "20000"))
    free_tool_calls: int = int(os.getenv("FREE_TOOL_CALLS", "0"))  # 0 = no tools
    free_modes: List[str] = field(default_factory=lambda: ["chat"])


settings = Settings()

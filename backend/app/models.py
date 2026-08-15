"""Database models: users, audit log, safe memory, usage counters."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # role: "admin" | "pro" (selected user - full free access) | "free" (limited)
    role = Column(String(16), default="free", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="user")
    memories = relationship("Memory", back_populates="user")


class AuditLog(Base):
    """Note 8 - log every action: time, user, request, tool, decision, result."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(64), nullable=False)
    mode = Column(String(32), nullable=False)  # chat | analyze | code | detect
    request_text = Column(Text, nullable=False)
    decision = Column(String(32), nullable=False)  # allowed | blocked | redirected
    tool = Column(String(64), default="none")
    result = Column(Text, default="")
    ip = Column(String(64), default="")

    user = relationship("User", back_populates="audit_logs")


class Memory(Base):
    """Note 8 - store only safe context, never secrets."""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String(64), nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="memories")


class UsageCounter(Base):
    """Daily usage counters used to enforce free-user limits."""

    __tablename__ = "usage_counters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    messages = Column(Integer, default=0, nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    tool_calls = Column(Integer, default=0, nullable=False)

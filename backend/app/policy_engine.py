"""Policy engine - Note 4 & Note 9 guardrails.

Decisions:
  allowed   -> normal operation
  redirected-> unsafe request: explain the risk, redirect to a lab exercise
  blocked   -> clearly outside the lab scope / violates rules
"""
from __future__ import annotations

import ipaddress
import re
from typing import List, Optional, Tuple

from .config import settings

# Patterns that clearly indicate real-world abuse (never target production / real people)
_BLOCK_PATTERNS = [
    r"\b(real\s+(bank|company|site|website|server|network|victim|person|account))\b",
    r"\b(steal|phish|scam)\s+\w*\s*(credentials|password|card|money|identity)\b",
    r"\b(ransomware|worm|botnet)\s+(deploy|launch|release|spread)\b",
    r"\b(ddos|flood|stress)\s+(a\s+)?(site|server|company|government)\b",
    r"\b(attack|hack|take\s+down|breach)\s+(my\s+)?(neighbor|school|friend|boss|ex\b|girlfriend|boyfriend)\b",
    r"\b(crack|hack)\s+(whatsapp|instagram|facebook|gmail|bank)\s+account\b",
    r"\b(fake\s+id|forged|fraud|identity\s+theft)\b",
]

# Requests that are dangerous without a lab target -> redirect to a lab exercise
_REDIRECT_PATTERNS = [
    r"\b(hack|attack|exploit|take\s+down|breach|intrude|compromise)\b",
    r"\b(real\s+target|production|live\s+site|company\s+server)\b",
    r"\b(steal|exfiltrate|dump)\s+(data|db|database)\b",
]

_HOSTNAME_LAB_SUFFIX = (".lab", ".local", ".test", ".internal")
_LAB_LITERAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "metasploitable", "dvwa", "owaspbwa", "vulnhub", "htb"}


def is_lab_target(target: str) -> bool:
    """Target must be inside the configured lab networks or a lab hostname."""
    t = target.strip().lower().rstrip(".")
    if t in _LAB_LITERAL_HOSTS:
        return True
    if any(t.endswith(s) for s in _HOSTNAME_LAB_SUFFIX):
        return True
    try:
        ip = ipaddress.ip_address(t)
        return any(ip in ipaddress.ip_network(net) for net in settings.lab_networks)
    except ValueError:
        pass
    # hostname without dots (single-label lab host)
    return "." not in t and t.replace("-", "").isalnum()


def classify_request(message: str, target: Optional[str] = None) -> Tuple[str, str, str]:
    """Returns (decision, reason, suggested_redirect)."""
    text = message.lower()

    for pat in _BLOCK_PATTERNS:
        if re.search(pat, text):
            return (
                "blocked",
                "This request appears to target real systems or people outside your lab. "
                "CyberBite only operates inside your authorized laboratory environment.",
                "Try: 'Set up a DVWA lab locally and show me how to test for SQL injection there'",
            )

    if target:
        if not is_lab_target(target):
            return (
                "blocked",
                f"Target '{target}' is outside the allowed lab networks "
                f"({', '.join(settings.lab_networks)}). Only authorized lab targets may be used.",
                "Try a lab host like 127.0.0.1, 192.168.x.x, or your VulnHub/HTB lab VM.",
            )

    for pat in _REDIRECT_PATTERNS:
        if re.search(pat, text):
            return (
                "redirected",
                "This sounds like an attack request. CyberBite explains attacks so you can "
                "defend against them, but only inside your isolated lab.",
                "Tell me what lab environment you have (DVWA, Metasploitable, HTB, VulnHub) "
                "and I will build you a safe, authorized lab exercise.",
            )

    return "allowed", "Within lab policy", ""


def lab_target_suggestion() -> str:
    return (
        "Lab-safe targets: localhost / 127.0.0.1, 192.168.x.x, or hostnames ending in "
        ".lab / .local / .test"
    )

"""Tool router - Note 9: decides which tool runs and how.

Only lab targets are allowed (validated by the policy engine). Arguments are
validated against shell metacharacters - no injection through the router.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .config import settings
from .policy_engine import is_lab_target
from .sandbox import SandboxError, run_in_sandbox

# Whitelisted tools. Add your own here; install them in sandbox/Dockerfile.
TOOL_REGISTRY = {
    "nmap": {
        "description": "Network scanner: ports, services, versions (lab targets only)",
        "network": True,
        "needs_target": True,
        "help": "nmap <target> [-sV -T4 ...]   e.g. nmap 192.168.1.10 -sV",
    },
    "nikto": {
        "description": "Web server vulnerability scanner",
        "network": True,
        "needs_target": True,
        "help": "nikto -h <target-url>   e.g. nikto -h http://127.0.0.1/dvwa",
    },
    "sqlmap": {
        "description": "SQL injection scanner (lab targets only)",
        "network": True,
        "needs_target": True,
        "help": "sqlmap -u <target-url> --batch   e.g. sqlmap -u http://127.0.0.1/dvwa/login.php?id=1",
    },
    "yara": {
        "description": "Pattern scanner for malware/sample files (files under /data only)",
        "network": False,
        "needs_target": True,
        "help": "yara <rule-file> <file>   e.g. yara /data/sample.yar /data/cyberbite.db (files live under ./data)",
    },
}

_META = re.compile(r"[;&|`$<>*?{}\[\]\"'\\\n\r]")


def validate_args(tool: str, target: str, args: List[str]) -> Tuple[Optional[str], List[str]]:
    """Returns (error, safe_command)."""
    spec = TOOL_REGISTRY.get(tool)
    if spec is None:
        return (f"Unknown tool '{tool}'. Available: {', '.join(TOOL_REGISTRY)}", [])

    if spec.get("needs_target") and not target.strip():
        return "A lab target is required (see tool help).", []

    if tool == "yara":
        # yara scans files inside the read-only /data mount (project ./data folder)
        if not target.startswith("/data/"):
            return "yara can only scan files under the mounted /data directory (project ./data folder).", []
    elif not is_lab_target(target):
        return (f"Target '{target}' is outside the allowed lab scope. "
                f"Only lab networks ({', '.join(settings.lab_networks)}) or .lab/.local hostnames.", [])

    for part in [target] + args:
        if _META.search(part):
            return "Arguments may not contain shell metacharacters.", []

    command = [tool] + args + [target]
    return None, command


def run_tool(tool: str, target: str, args: List[str]) -> Tuple[str, int, float]:
    """Validate and execute a tool inside the sandbox."""
    err, command = validate_args(tool, target, args)
    if err:
        raise SandboxError(err)
    spec = TOOL_REGISTRY[tool]
    return run_in_sandbox(tool, command, network=spec["network"])

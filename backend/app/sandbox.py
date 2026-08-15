"""Sandbox executor - Note 7: tools run inside an isolated disposable container.

- Docker mode: `docker run --rm` with resource limits, dropped capabilities,
  and a restricted /data mount (read-only) for file tools.
- Local mode (TOOL_EXECUTOR=local): direct subprocess with timeout, for dev
  machines without Docker. Use only on your own lab machine.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from typing import List, Tuple

from .config import settings


class SandboxError(Exception):
    pass


def _docker_available() -> bool:
    try:
        r = subprocess.run(["docker", "version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def run_in_sandbox(tool: str, command: List[str], network: bool = True,
                   timeout: int = None) -> Tuple[str, int, float]:
    """Execute a command inside the isolated lab container."""
    timeout = timeout or settings.tool_timeout
    start = time.time()

    if settings.tool_executor == "local" or not _docker_available():
        exe = shutil.which(tool)
        if not exe:
            raise SandboxError(
                f"Tool '{tool}' is not installed locally and Docker is unavailable. "
                f"Install Docker Desktop or install the tool on this machine."
            )
        proc = subprocess.run(command, capture_output=True, text=True,
                              timeout=timeout)
        output = (proc.stdout or "") + (proc.stderr or "")
        return output.strip()[-6000:], proc.returncode, round(time.time() - start, 2)

    # Docker mode: disposable container, restricted & isolated
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "host" if network else "none",
        "--memory", "512m",
        "--cpus", "1",
        "--cap-drop", "ALL",
    ]
    if network:
        docker_cmd += ["--cap-add", "NET_RAW", "--cap-add", "NET_ADMIN"]
    docker_cmd += [
        "-v", f"{settings.sandbox_data_mount.rstrip('/')}:/data:ro",
        "--stop-timeout", str(min(timeout, 30)),
        settings.sandbox_image,
    ] + command

    proc = subprocess.run(docker_cmd, capture_output=True, text=True,
                          timeout=timeout + 15)
    output = (proc.stdout or "") + (proc.stderr or "")
    return output.strip()[-6000:], proc.returncode, round(time.time() - start, 2)

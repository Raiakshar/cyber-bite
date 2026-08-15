# Python for Security Tooling (lab automation)

Structure a scanner: parse args -> validate target (lab only) -> connect -> report.

import socket, sys
host = sys.argv[1]; ports = [21,22,80,443,8080]
for p in ports:
    s = socket.socket(); s.settimeout(1)
    if s.connect_ex((host, p)) == 0:
        print(f"{host}:{p} open")
    s.close()

HTTP automation: requests library (proxied via Burp if needed).
- requests.get(url, timeout=5, headers={"User-Agent": "lab-agent"})
- Always validate target against your lab scope before touching the network.

Payload rules in a lab context
- Read-only/test targets only. Never scan ranges you do not own.
- Keep scripts idempotent, bounded (timeouts, max retries), and logged.
- Fuzz wordlists: /usr/share/wordlists (rockyou.txt for hashes is huge - use small subsets).

Use CyberBite's CODE mode to generate and explain such tooling.

# Knowledge Base

Add markdown files here. Each file becomes a retrievable document (RAG).
Keep content high-quality and lab-focused.

Topic folders (Note 5):
- networking/   - protocols, nmap, wireshark, tcpdump
- linux/        - commands, privesc, hardening
- windows/      - recon, AD, powershell, privesc
- python/       - scripting, socket programming
- web-security/ - OWASP, SQLi, XSS, SSRF, auth
- malware-analysis/ - static/dynamic analysis, YARA, unpacking
- detection/    - SIEM rules, threat hunting, EDR evasion basics
- incident-response/ - playbooks, forensics, memory analysis
- ctf/          - methodologies, writeups, tools

After adding files: `docker compose restart backend` (or run scripts/seed_knowledge.py).

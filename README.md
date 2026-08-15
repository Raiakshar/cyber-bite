# CyberBite — Your Local AI Security Copilot

> ## ⚠️ EDUCATIONAL PURPOSE ONLY
>
> This project is built **strictly for educational, research, and authorized
> testing purposes**. Use it only against your **own** systems, lab machines,
> CTF platforms, and environments you are explicitly authorized to test.
> Unauthorized scanning, exploitation, or use of any security tool against
> systems you do not own is **illegal** and against the code of ethics of the
> security community. The authors assume **no responsibility** for any misuse.
> By using this software you agree that you alone are responsible for your
> actions and that you will only use it in a legal, ethical, and authorized
> manner.

`$ cyber_bite@lab` — a self-hosted, private hacking/security assistant with
**CHAT / ANALYZE / CODE / DETECT** modes, local AI (Ollama), RAG knowledge,
an isolated tool sandbox, full audit logging, and role-based access control.

---

## What you get (mapped to the 10 slides)

| Slide | Feature | Where |
|-------|---------|-------|
| 1–2   | Terminal-style copilot UI + 4 modes | `frontend/` |
| 3     | Stack: FastAPI + Ollama + RAG + React + Docker | `docker-compose.yml` |
| 4     | Real system prompt ("cybersecurity laboratory assistant") | `backend/app/routers/chat.py` |
| 5–6   | RAG knowledge base (9 topic folders) | `knowledge/`, `backend/app/rag.py` |
| 7     | Isolated lab sandbox for tools (disposable containers) | `backend/app/sandbox.py`, `sandbox/` |
| 8     | Safe memory + audit logging | `backend/app/models.py`, `audit.py`, admin AUDIT LOGS tab |
| 9     | Final architecture: UI → API → Policy → RAG → Tools → Sandbox → Logs | whole repo |
| 10    | DETECT / DEFEND copilot | 4 modes + policy engine |

**Your extra requirement** — free & unlimited for selected users, limited for everyone else:
- New users register as `free`: limited daily quota, CHAT mode only, no tools.
- Admins promote any user to `pro` in the **ADMIN** tab → that user gets
  **FREE, UNLIMITED** access to every mode and all tools.
- All limits are configurable in `.env`.

---

## 1) Quick start (Docker — recommended)

Requirements: **Docker Desktop** running, ~6 GB disk for AI models.

```bash
cd cyber-bite
./scripts/setup.sh
```

Setup script does: build images → start PostgreSQL + Ollama → pull `llama3`
and `nomic-embed-text` → start backend + frontend.

Then open:
- **Web UI:** http://localhost:8080
- **API docs:** http://localhost:8000/docs
- Admin credentials: from `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`,
  default `admin` / `ChangeMe123!` — **change them**).

First chat is slower while the model loads; afterwards it is fast.

---

## 2) Manual dev setup (no Docker for the app)

```bash
cd cyber-bite

# --- Backend (Python 3.10+) ---
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL=sqlite:///./data/cyberbite.db
uvicorn app.main:app --app-dir backend --reload --port 8000

# --- Frontend ---
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api to :8001 by default)

# --- AI model (install Ollama from ollama.com) ---
ollama pull llama3
ollama pull nomic-embed-text
```

If your backend runs on a different port, set:
```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

---

## 3) Access control — free vs selected users

| Role | Modes | Daily limit | Tools | Managed by |
|------|-------|-------------|-------|------------|
| `free` | CHAT only (configurable) | e.g. 10 messages / 20k tokens | none | automatic on register |
| `pro` (selected) | CHAT + ANALYZE + CODE + DETECT | **unlimited** | all whitelisted tools | admin promotes via ADMIN tab |
| `admin` | everything | unlimited | all | first account (`.env`) |

Admin flow:
1. Log in as admin → **ADMIN** tab → **USERS**.
2. Click **SELECT (unlimited free)** next to a user → they become `pro`.
3. Click **LIMIT** to demote back to `free`.
4. **AUDIT LOGS** tab shows every action: time, user, request, decision, tool, result.

Change the free-tier limits in `.env`:
```
FREE_DAILY_MESSAGES=10
FREE_DAILY_TOKENS=20000
FREE_TOOL_CALLS=0
FREE_MODES=chat
```

---

## 4) Tools & the isolated sandbox (Note 7)

Whitelisted tools: **nmap, nikto, sqlmap, yara** (add more in
`backend/app/tool_router.py` + `sandbox/Dockerfile`).

Every tool run:
- validates the target against the lab scope (`.env` → `LAB_NETWORKS`,
  or `.lab/.local/.test` hostnames) — anything else is **blocked**,
- rejects shell metacharacters in arguments (no injection),
- executes in a **disposable container**: `docker run --rm`, 512 MB RAM,
  1 CPU, `--cap-drop ALL`, no persistent state, read-only `/data` mount.

Usage in DETECT mode: pick tool → lab target → optional args → RUN IN SANDBOX.
Examples: `nmap 127.0.0.1 -sV`, `nikto -h http://dvwa.lab`, `yara /data/sample.bin`.

---

## 5) Knowledge base & RAG (Notes 5–6)

Drop markdown files into `knowledge/<topic>/` (9 topics pre-seeded).
Restart the backend (`docker compose restart backend`) or run
`python scripts/seed_knowledge.py` to rebuild the index.

- Uses ChromaDB if installed, otherwise a built-in vector store
  (Ollama embeddings + cosine similarity), with a keyword fallback.
- Every answer is grounded in retrieved docs; sources are shown in the UI.

---

## 6) Policy engine (Note 4)

`backend/app/policy_engine.py` classifies every request:
- **allowed** → normal operation,
- **blocked** → targets outside the lab scope / clear real-world abuse,
- **redirected** → explains the risk and suggests a safe lab exercise.

The system prompt enforces the "cybersecurity laboratory assistant" role:
explain, analyze, review logs, help CTFs, write safe PoCs, recommend fixes —
never expose real secrets or destructive payloads.

---

## 7) Project layout

```
cyber-bite/
├── backend/            FastAPI app (policy engine, RAG, tool router, sandbox, logging)
├── frontend/           React chat UI (CHAT/ANALYZE/CODE/DETECT + admin)
├── knowledge/          RAG knowledge base (9 topics)
├── sandbox/            lab-tools image (nmap, nikto, sqlmap, yara)
├── scripts/            setup.sh, seed_knowledge.py
├── docker-compose.yml  db + ollama + backend + frontend + lab-tools
└── .env.example        all configuration
```

---

## 8) Security notes

- Change `JWT_SECRET`, `ADMIN_PASSWORD` before exposing anything.
- The backend never scans outside `LAB_NETWORKS`; yara only reads `./data`.
- Everything is logged to PostgreSQL (audit trail).
- AI models run locally (Ollama) — your data never leaves your machine.
- Use it as intended: lab machines, CTF platforms, your own code.

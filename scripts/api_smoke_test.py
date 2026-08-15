import json, urllib.request, urllib.error

BASE = "http://127.0.0.1:8010"
results = []

def req(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}

def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))
    print(("PASS" if cond else "FAIL"), "-", name, extra if not cond else "")

# 1. register two free users
s, r = req("POST", "/api/auth/register", {"username": "alice", "email": "alice@lab.test", "password": "Password123!"})
check("register alice (free)", s == 200 and r.get("role") == "free")
tok_alice = r.get("access_token")

s, r = req("POST", "/api/auth/register", {"username": "bob", "email": "bob@lab.test", "password": "Password123!"})
check("register bob (free)", s == 200 and r.get("role") == "free")
tok_bob = r.get("access_token")

# 2. duplicate register blocked
s, r = req("POST", "/api/auth/register", {"username": "alice", "email": "other@lab.test", "password": "Password123!"})
check("duplicate username rejected", s == 400)

# 3. login admin (auto-created)
s, r = req("POST", "/api/auth/login", {"username": "admin", "password": "ChangeMe123!"})
check("admin login", s == 200 and r.get("role") == "admin")
tok_admin = r.get("access_token")

# 4. wrong password
s, r = req("POST", "/api/auth/login", {"username": "admin", "password": "wrong"})
check("wrong password rejected", s == 401)

# 5. chat - safe question (ollama down -> friendly error but decision allowed)
s, r = req("POST", "/api/chat", {"message": "Explain SQL injection to me", "mode": "chat"}, tok_alice)
check("free user chat allowed", s == 200 and r.get("decision") == "allowed")
check("quota_left returned", isinstance(r.get("quota_left"), int))

# 6. chat - RAG used flag present
check("used_rag is bool", isinstance(r.get("used_rag"), bool))

# 7. policy - blocked target outside lab
s, r = req("POST", "/api/chat", {"message": "Scan 8.8.8.8 for open ports", "mode": "chat", "target": "8.8.8.8"}, tok_alice)
check("external target blocked", s == 200 and r.get("decision") == "blocked")

# 8. policy - lab target allowed through policy (ollama down but decision allowed)
s, r = req("POST", "/api/chat", {"message": "Scan my dvwa.lab for open ports", "mode": "chat", "target": "dvwa.lab"}, tok_alice)
check("lab target passes policy", s == 200 and r.get("decision") == "allowed")

# 9. policy - real-world abuse redirected/blocked
s, r = req("POST", "/api/chat", {"message": "hack my neighbor's wifi", "mode": "chat"}, tok_alice)
check("real-world abuse redirected", s == 200 and r.get("decision") in ("redirected", "blocked"))

# 10. free user cannot use analyze mode
s, r = req("POST", "/api/chat", {"message": "analyze this log", "mode": "analyze"}, tok_alice)
check("free user analyze blocked", s == 403)

# 11. free user cannot run tools
s, r = req("POST", "/api/detect/run", {"tool": "nmap", "target": "127.0.0.1", "args": ["-sV"]}, tok_alice)
check("free user tool run blocked", s in (403, 500) and r.get("decision") == "blocked")

# 12. tools list
s, r = req("GET", "/api/detect/tools")
check("tools list has nmap/nikto/sqlmap/yara", s == 200 and all(t in [x["name"] for x in r] for t in ("nmap", "nikto", "sqlmap", "yara")))

# 13. admin promotes alice to pro
s, r = req("PUT", f"/api/admin/users/{1 if False else 2}/role", {"role": "pro"}, tok_admin)
# find alice id
s, users = req("GET", "/api/admin/users", token=tok_admin)
alice_id = next(u["id"] for u in users if u["username"] == "alice")
s, r = req("PUT", f"/api/admin/users/{alice_id}/role", {"role": "pro"}, tok_admin)
check("admin promotes alice to pro", s == 200 and r.get("role") == "pro")

# 14. alice now has unlimited quota and all modes
s, r = req("GET", "/api/auth/me/quota", token=tok_alice)
check("pro quota unlimited (-1)", s == 200 and r.get("messages_left_today") == -1)
s, r = req("POST", "/api/chat", {"message": "write a port scanner in python", "mode": "code"}, tok_alice)
check("pro can use code mode", s == 200 and r.get("decision") == "allowed")

# 15. non-admin cannot promote
s, r = req("PUT", f"/api/admin/users/{alice_id}/role", {"role": "free"}, tok_bob)
check("non-admin cannot change roles", s == 403)

# 16. admin audit logs exist
s, r = req("GET", "/api/admin/logs?limit=10", token=tok_admin)
check("audit logs returned", s == 200 and len(r) > 0)
decisions = {x["decision"] for x in r}
check("logs include blocked decisions", "blocked" in decisions)

# 17. free quota exhaustion (bob) -> 429
s, r = req("GET", "/api/auth/me/quota", token=tok_bob)
left = r.get("messages_left_today", 0)
statuses = []
for i in range(left + 1):
    st, _ = req("POST", "/api/chat", {"message": f"ping {i}", "mode": "chat"}, tok_bob)
    statuses.append(st)
check("free user hits 429 after daily limit", 429 in statuses, f"statuses={statuses[:3]}...")

# 18. pro user unaffected by limit
s, r = req("POST", "/api/chat", {"message": "one more", "mode": "chat"}, tok_alice)
check("pro still allowed after free limit", s == 200)

print("\n==== SUMMARY ====")
fails = [x for x in results if not x[1]]
print(f"{len(results) - len(fails)}/{len(results)} passed")
if fails:
    print("FAILED:", [f[0] for f in fails])

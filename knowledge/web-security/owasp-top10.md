# OWASP Top 10 - quick reference (2021)

A01 Broken Access Control - check authorization on every endpoint, not just login.
  Test: change IDs/roles in requests, try vertical/horizontal privilege escalation.

A02 Cryptographic Failures - no weak ciphers, no hardcoded keys, TLS everywhere.
  Test: look for http:// plaintext, weak hashes (md5/sha1), hardcoded secrets in JS/source.

A03 Injection - SQLi, NoSQLi, command injection, LDAP, XPath.
  Test: single quotes, boolean blind payloads, time-based payloads (sleep), UNION selects.
  Safe lab practice: always use DVWA/bWAPP/sqli-labs, never a live site.

A04 Insecure Design - missing rate limits, trust boundaries, business logic flaws.

A05 Security Misconfiguration - default creds, verbose errors, unneeded features enabled.
  Test: nmap + nikto + check headers (server, x-powered-by, missing CSP).

A06 Vulnerable Components - outdated libraries with known CVEs.

A07 Identification & Auth Failures - weak password policies, no MFA, session issues.
  Test: session fixation, token in URL, no expiry.

A08 Software & Data Integrity Failures - CI/CD tampering, unsigned updates.

A09 Logging & Monitoring Failures - no audit trail, no alerting. (CyberBite logs everything.)

A10 SSRF - server fetches attacker-controlled URLs.
  Test: point the server at 127.0.0.1, cloud metadata (169.254.169.254) - in lab only.

Defense-first mindset: identify -> understand -> reproduce in lab -> recommend fix.

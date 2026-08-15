# Incident Response Playbook (lab drills)

Preparation
- Document assets, contacts, and what "normal" looks like.
- Keep a jump kit: forensic imaging tools, hashing tools, read-only evidence drives.

Detection & Triage
- Confirm: is it real? scope? (single host vs network-wide)
- Collect evidence without modifying it (forensic image / read-only mounts).
- Record timeline: first seen, user reports, alerts, log sources.

Containment
- Isolate affected hosts (network segmentation), preserve RAM if possible.
- Revoke compromised creds, disable accounts, kill C2 sessions.

Eradication
- Identify root cause (phish? vulnerable service? default creds?).
- Remove persistence: scheduled tasks, services, registry run keys, cron.
- Patch and harden the root cause.

Recovery & Lessons
- Restore from verified clean backups, monitor for re-infection.
- Write the report: timeline, indicators, impact, root cause, recommendations.

Practice: stand up two lab VMs, play attacker/defender, record everything.

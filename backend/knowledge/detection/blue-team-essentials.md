# Blue Team Essentials - detection mindset

1. Know your baseline. Alert on deviations from normal behavior.
2. Prioritize: auth failures, new admin accounts, outbound C2 patterns,
   unusual powershell, scheduled task creation, large data transfers.
3. Windows events to watch: 4624/4625 (logon), 4720 (user created),
   4688 (process creation), 7045 (service install), 1102 (audit log cleared).
4. Linux: /var/log/auth.log, /var/log/syslog, auditd, journalctl.
5. Network: DNS for C2 domains, beaconing (regular intervals), TLS to unusual hosts.
6. Strings that matter: base64 blobs, iex()/Invoke-Expression, encoded commands,
   certutil -urlcache, bitsadmin, schtasks /create.
7. Write simple YARA or Sigma rules to codify detections.
8. Log everything, test your rules with the atomic-red-team / MITRE ATT&CK maps.

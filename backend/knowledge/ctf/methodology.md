# CTF Methodology (HTB / VulnHub / tryhackme-style)

1. Recon - nmap full port + -sV -sC; dirbuster/ffuf for web; note every service/version.
2. Web - check source, robots.txt, parameter fuzzing; test OWASP injection classes in lab.
3. Exploit - match versions to known CVEs (searchsploit), craft minimal PoC, document.
4. Foothold - reverse shell (lab listener only), stabilize with python pty, collect flags.
5. Privesc - follow the linux/windows privesc checklist.
6. Post - enumerate users, config files, credentials; lateral movement notes.
7. Writeup - document commands, evidence, and the fix (defender value!).

Golden rules
- Stay in scope: your lab VM/instance only.
- Log every command - you will need it for the writeup.
- If stuck: re-enumerate. Missed services are the #1 blocker.
- Use CyberBite to explain techniques and generate safe lab PoCs.

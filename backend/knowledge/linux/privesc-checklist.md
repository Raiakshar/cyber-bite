# Linux Privilege Escalation Checklist (lab VMs only)

Enumeration
- id; uname -a; cat /etc/os-release
- sudo -l                      # what can you run as root?
- find / -perm -4000 2>/dev/null   # SUID binaries
- ls -la /etc/passwd /etc/shadow  # writable? world-readable?
- crontab -l; ls /etc/cron*       # scheduled tasks
- env; cat ~/.bash_history        # secrets in history
- ss -tlnp                        # listening services on the box
- find / -writable 2>/dev/null | grep -v proc   # writable dirs for drop-in

Common vectors (lab only)
- SUID misconfigs (e.g. gtfobins.github.io entries)
- sudo wildcards / NOPASSWD entries
- writable cron scripts executed by root
- kernel exploits - only for the exact kernel version in a lab VM
- PATH hijack, .bashrc/.profile inject
- docker group membership -> docker run -v /:/host

After privesc: document how you got in, patch the lab VM, re-verify.
Never run these against systems you don't own. In CyberBite, everything is lab-isolated.

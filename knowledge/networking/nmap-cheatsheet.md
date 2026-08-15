# Nmap Cheat Sheet (lab targets only)

Host discovery
- nmap -sn 192.168.1.0/24        # ping sweep
- nmap -sL 10.0.0.0/24           # list scan (no packets)

Port scanning
- nmap -p- 127.0.0.1             # all 65535 ports
- nmap -p 22,80,443 target.lab   # specific ports
- nmap -sS target.lab            # SYN stealth scan (needs root/raw sockets)
- nmap -sT target.lab            # TCP connect scan (no raw sockets)

Service/version detection
- nmap -sV target.lab            # service versions
- nmap -sC target.lab            # default NSE scripts
- nmap -sV -sC -O target.lab     # classic -A combo: versions, scripts, OS

Output
- nmap -oN out.txt target.lab    # normal output
- nmap -oX out.xml target.lab    # XML (use with searchsploit/nikto pipelines)

Notes
- Always scan lab/VPN targets you own. In CyberBite, only LAB_NETWORKS are allowed.
- Use -T4 for balance; -T5 can drop packets.
- Combine with nikto (-h http://target) for web-layer checks.

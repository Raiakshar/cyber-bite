# Windows Recon Essentials (lab domain/VMs only)

System
- systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
- whoami /all                       # token groups, privileges
- net user /domain; net group "Domain Admins" /domain
- ipconfig /all; route print; arp -a

Network
- netstat -ano                       # listening sockets + PIDs
- powershell "Get-Process | Select-Object Id,ProcessName,Path"

Persistence & detection artifacts to look for
- schtasks /query /fo LIST /v        # scheduled tasks
- reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
- services.msc / sc query            # unusual services
- PowerShell history: (Get-PSReadLineOption).HistorySavePath

Security
- Get-MpComputerStatus               # defender status
- auditpol /get /category:*          # audit policy

Always operate on lab machines you own (e.g. a Windows 10/Server VM in your lab network).

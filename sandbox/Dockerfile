# Isolated lab tools image (Note 7) - disposable, only lab tools
FROM kalilinux/kali-rolling

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap nikto sqlmap yara python3 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# No entrypoint: commands passed at runtime (docker run --rm <image> nmap ...)

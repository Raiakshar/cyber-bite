FROM python:3.11-slim

WORKDIR /app

# Docker CLI so the backend can spawn disposable lab containers (Note 7)
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY knowledge /knowledge
RUN mkdir -p /data

ENV KNOWLEDGE_DIR=/knowledge \
    CHROMA_DIR=/data/chroma \
    SANDBOX_DATA_MOUNT=/host-data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

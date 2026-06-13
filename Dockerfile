FROM python:3.11-slim

WORKDIR /app

# git: repo sync on startup
# pandoc: markdown-to-PDF export
# curl: health check
# PyMuPDF ships its own MuPDF — no system lib needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    pandoc \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .
COPY scripts/ scripts/

RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

ENV VAULT_PATH=/repo/vault
ENV INDEX_PATH=/data/index
ENV PORT=8000

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

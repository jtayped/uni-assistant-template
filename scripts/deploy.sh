#!/bin/bash
# VPS deployment script for Uni Assistant V2
# Designed for Coolify + Docker Compose deployment
# Run this on your VPS after cloning the repo

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Deploying from: $REPO_DIR"

# 1. Verify .env exists
if [ ! -f "$REPO_DIR/.env" ]; then
    echo "ERROR: .env file not found."
    echo "Copy .env.example to .env and fill in your API_KEY:"
    echo "  cp .env.example .env && nano .env"
    exit 1
fi

# 2. Build and start containers
echo ""
echo "Building Docker image..."
docker compose -f "$REPO_DIR/docker-compose.yml" build

echo ""
echo "Starting services..."
docker compose -f "$REPO_DIR/docker-compose.yml" up -d

# 3. Wait for server to start
echo ""
echo "Waiting for server to start..."
sleep 5

# 4. Health check
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "Server is up: http://localhost:8000"
else
    echo "WARNING: Health check failed. Check logs:"
    echo "  docker compose logs uni-mcp"
fi

# 5. Build initial index (if vault has content)
MD_COUNT=$(find "$REPO_DIR/vault" -name "*.md" | wc -l)
if [ "$MD_COUNT" -gt 5 ]; then
    echo ""
    echo "Building vector index ($MD_COUNT markdown files found)..."
    docker compose -f "$REPO_DIR/docker-compose.yml" exec uni-mcp \
        python scripts/build_index.py
else
    echo ""
    echo "Skipping index build (vault is empty — run init first)."
fi

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Next steps:"
echo "  1. In Coolify: create a Docker Compose service pointing to this directory"
echo "  2. In Cloudflare: add A record for your subdomain → VPS IP"
echo "  3. In Coolify: configure SSL domain (Let's Encrypt auto-handles it)"
echo "  4. Add to Claude Code settings:"
echo '     { "mcpServers": { "uni-assistant": { "type": "sse", "url": "https://uni.joeltaylor.business/sse", "headers": { "X-API-Key": "YOUR_KEY" } } } }'
echo ""
echo "Test with:"
echo "  curl -H 'X-API-Key: YOUR_KEY' https://uni.joeltaylor.business/health"

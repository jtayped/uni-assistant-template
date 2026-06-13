#!/bin/bash
set -e

echo "=== Uni Assistant startup ==="
echo "Python: $(python --version)"
echo "VAULT_PATH: ${VAULT_PATH}"
echo "REPO_PATH: ${REPO_PATH}"

# Configure git auth via token
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_REPO" ]; then
    git config --global credential.helper store
    git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
    git config --global user.email "uni-assistant@vps"
    git config --global user.name "Uni Assistant"

    echo "Pulling latest vault from GitHub..."
    git -C /repo pull --ff-only 2>&1 || echo "Warning: git pull failed, continuing with existing files."
else
    echo "Warning: GITHUB_TOKEN not set — skipping git pull."
fi

echo "Verifying Python imports..."
python -c "from mcp_instance import mcp; print('MCP OK')" || {
    echo "ERROR: Failed to import MCP. Check requirements."
    exit 1
}

echo "Starting MCP server on port ${PORT:-8000}..."
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info

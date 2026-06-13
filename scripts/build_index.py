"""
Rebuild the full LanceDB vector index from all vault markdown files.
Run this after adding many files, or on first deploy.

Usage (from repo root):
    python scripts/build_index.py

Usage (inside Docker container):
    python scripts/build_index.py

Usage (via docker compose):
    docker compose exec uni-mcp python scripts/build_index.py
"""
import sys
import argparse
import time
from pathlib import Path

# Resolve server module path — works both locally (scripts/ next to server/)
# and in Docker (server/ contents are flattened into WORKDIR /app).
_here = Path(__file__).parent.parent  # repo root or /app in Docker
for _candidate in [_here / "server", _here]:
    if (_candidate / "config.py").exists():
        sys.path.insert(0, str(_candidate))
        break


def main():
    parser = argparse.ArgumentParser(description="Rebuild LanceDB vector index from vault")
    parser.add_argument("--vault", default=None, help="Path to vault directory")
    parser.add_argument("--index", default=None, help="Path to index directory")
    args = parser.parse_args()

    from config import settings

    vault_path = args.vault or str(settings.VAULT_PATH)
    index_path = args.index or str(settings.INDEX_PATH)

    print(f"Building index...")
    print(f"  Vault:  {vault_path}")
    print(f"  Index:  {index_path}")
    print(f"  Model:  {settings.EMBED_MODEL}")
    print()

    start = time.time()

    from ingestion.indexer import build_index
    result = build_index(vault_path, index_path)

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s")
    print(f"  Files processed: {result['files']}")
    print(f"  Chunks indexed:  {result['indexed']}")
    print(f"  Status: {result['status']}")


if __name__ == "__main__":
    main()

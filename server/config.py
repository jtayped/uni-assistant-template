"""
Server configuration — loads from environment variables.
No secrets here. Secrets go in .env (gitignored).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_KEY: str = os.getenv("API_KEY", "")

    # /repo is the mounted git repo inside the container
    # REPO_PATH on host is the full path where you cloned the repo (e.g. /root/uni-assistant)
    REPO_PATH: Path = Path(os.getenv("REPO_PATH", "/repo"))
    VAULT_PATH: Path = Path(os.getenv("VAULT_PATH", "/repo/vault"))
    INDEX_PATH: Path = Path(os.getenv("INDEX_PATH", "/data/index"))

    # GitHub sync — Personal Access Token with repo scope
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "https://github.com/jtayped/uni-assistant")

    PORT: int = int(os.getenv("PORT", "8000"))
    EMBED_MODEL: str = "all-MiniLM-L6-v2"

    # IANA timezone name — Docker containers default to UTC
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Madrid")

settings = Settings()

# Ensure core directories exist
settings.VAULT_PATH.mkdir(parents=True, exist_ok=True)
settings.INDEX_PATH.mkdir(parents=True, exist_ok=True)
(settings.VAULT_PATH / "ingest").mkdir(exist_ok=True)

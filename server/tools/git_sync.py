"""Git sync — commit vault changes and push to GitHub."""
import subprocess
from urllib.parse import urlparse, urlunparse
from mcp_instance import mcp
from config import settings


def _run(cmd: list[str], cwd: str = None) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, (result.stdout + result.stderr).strip()


def _authenticated_url() -> str | None:
    """Return the GitHub repo URL with the token embedded, or None if token missing."""
    if not settings.GITHUB_TOKEN or not settings.GITHUB_REPO:
        return None
    parsed = urlparse(settings.GITHUB_REPO)
    authed = parsed._replace(netloc=f"x-access-token:{settings.GITHUB_TOKEN}@{parsed.hostname}")
    return urlunparse(authed)


def _ensure_git_identity(repo: str) -> None:
    """Set git user identity if not already configured (required to commit)."""
    code, _ = _run(["git", "config", "user.email"], cwd=repo)
    if code != 0:
        _run(["git", "config", "user.email", "uni-assistant@vps"], cwd=repo)
        _run(["git", "config", "user.name", "Uni Assistant"], cwd=repo)


@mcp.tool()
def git_sync(message: str = "vault: update content") -> str:
    """
    Commits all vault changes and pushes them to GitHub.
    Call after ingesting files, completing exercises, or adding notes.
    This keeps GitHub as the source of truth and syncs across machines.

    message: git commit message describing what changed.
    """
    repo = str(settings.REPO_PATH)

    auth_url = _authenticated_url()
    if not auth_url:
        return (
            "GITHUB_TOKEN not set — cannot push. "
            "Add it to .env and redeploy. Changes are saved locally only."
        )

    _ensure_git_identity(repo)

    code, out = _run(["git", "add", "vault/"], cwd=repo)
    if code != 0:
        return f"git add failed:\n{out}"

    code, _ = _run(["git", "diff", "--staged", "--quiet"], cwd=repo)
    if code == 0:
        return "Nothing to commit — vault is already in sync with GitHub."

    code, out = _run(["git", "commit", "-m", message], cwd=repo)
    if code != 0:
        return f"git commit failed:\n{out}"

    code, out = _run(["git", "push", auth_url, "HEAD:main"], cwd=repo)
    if code != 0:
        return f"git push failed:\n{out}"

    return f"Synced to GitHub: \"{message}\"\nOther machines can now `git pull` to get the update."


@mcp.tool()
def git_pull() -> str:
    """
    Pulls the latest vault from GitHub.
    Use this to manually sync if the container wasn't restarted after a push from another machine.
    """
    repo = str(settings.REPO_PATH)

    auth_url = _authenticated_url()
    if not auth_url:
        return (
            "GITHUB_TOKEN not set — cannot pull. "
            "Add it to .env and redeploy."
        )

    code, out = _run(["git", "pull", "--ff-only", auth_url, "main"], cwd=repo)
    if code != 0:
        return f"git pull failed:\n{out}"

    return f"Pulled latest from GitHub.\n{out}"

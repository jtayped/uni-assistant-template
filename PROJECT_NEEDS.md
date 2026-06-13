# What I Need From You — Uni Assistant V2

---

## Status

- **GitHub repo:** https://github.com/jtayped/uni-assistant ✅
- **API key:** set ✅
- **Subdomain:** uni.joeltaylor.business ✅
- **GitHub token:** needed (see step 2 below)

---

## Remaining Steps

### 1 — Create a GitHub Personal Access Token

The server needs this to `git pull` on startup and `git push` after ingesting files.

1. Go to https://github.com/settings/tokens/new
2. Name: `uni-assistant-vps`
3. Scopes: check **repo** (full repo access)
4. Click Generate → copy the token (`ghp_...`)

You'll add this as `GITHUB_TOKEN` in your `.env` file.

---

### 2 — On your VPS (SSH in)

```bash
# Clone the repo
git clone https://github.com/jtayped/uni-assistant ~/uni-assistant
cd ~/uni-assistant

# Create .env from template
cp .env.example .env
nano .env
```

Fill in `.env`:
```
API_KEY=YOUR_API_KEY
GITHUB_TOKEN=ghp_your_token_here
REPO_PATH=/root/uni-assistant
```

(If your home dir isn't `/root`, adjust `REPO_PATH` accordingly — check with `echo $HOME`.)

---

### 3 — In Coolify

1. Create a new **Docker Compose** service
2. Source: point it at the `docker-compose.yml` in `~/uni-assistant`
3. Set environment variables (copy from your `.env`):
   - `API_KEY`
   - `GITHUB_TOKEN`
   - `REPO_PATH` = `/root/uni-assistant` (or your home path)
4. Set domain: `uni.joeltaylor.business`
5. Deploy

---

### 4 — Cloudflare DNS

Add an A record: `uni` → your VPS IP address.

Coolify handles SSL automatically once DNS resolves.

---

### 5 — Test it

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     https://uni.joeltaylor.business/health
```

Should return: `{"status":"ok","server":"uni-assistant"}`

---

### 6 — Configure Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "uni-assistant": {
      "type": "sse",
      "url": "https://uni.joeltaylor.business/sse",
      "headers": {
        "X-API-Key": "YOUR_API_KEY"
      }
    }
  }
}
```

---

### 7 — Run Init

Start a Claude Code session in the repo root and say:

> "Run the uni assistant init. Let's set up my vault."

The agent reads `INIT.md` and walks you through subjects, marks, and file ingestion conversationally.

---

### 8 — (Optional) Telegram mobile access

Create a bot via `@BotFather` → `/newbot` → copy the token. Set it up with Claude Code Channels on the VPS for mobile access.

---

## How sync works

- **On startup:** container does `git pull` automatically (gets latest vault from GitHub)
- **After ingesting/studying:** agent calls `git_sync()` tool → commits + pushes vault changes to GitHub
- **On desktop:** `git pull` in the repo to sync vault content to your local machine

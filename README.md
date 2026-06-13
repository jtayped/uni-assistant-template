# Uni Assistant V2

Claude Code-powered academic assistant. Handles subjects, marks, exam history, study campaigns, notes, projects, and normative. Runs as an MCP server on a VPS — accessible from Claude Code on desktop and via Telegram on mobile.

## Architecture

```
GitHub (private) ─── source of truth for markdown + images
VPS ────────────── MCP server + LanceDB index + Claude Code Channels (Telegram)
Desktop ────────── Claude Code → MCP server (HTTPS + API key)
Mobile ─────────── Telegram → VPS Claude Code → vault → git
```

## Quick Start

### VPS Deployment (with Coolify)

1. Clone this repo on your VPS:
   ```bash
   git clone https://github.com/jtayped/uni-assistant ~/uni-assistant
   cd ~/uni-assistant
   ```

2. Copy and fill the env file:
   ```bash
   cp .env.example .env
   # Edit .env: set API_KEY to a random secret
   ```

3. In Coolify: create a **Docker Compose** service pointing to this directory. Set the environment variables from `.env`.

4. In Cloudflare: add an A record for your chosen subdomain (e.g. `uni.joeltaylor.business`) pointing to your VPS IP. Coolify handles SSL automatically.

5. Build the initial LanceDB index (after vault has content):
   ```bash
   docker-compose exec uni-mcp python /app/../scripts/build_index.py
   ```

### Desktop Setup

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "uni-assistant": {
      "type": "sse",
      "url": "https://uni.joeltaylor.business/sse",
      "headers": {
        "X-API-Key": "your-api-key-here"
      }
    }
  }
}
```

### First Run — Init

Start a Claude Code session and say:

> "Run the uni assistant init. Let's set up my vault from scratch."

The agent will guide you through adding your university, semester, subjects, and existing files.

See `INIT.md` for the full init procedure.

## Repository Structure

```
uni-assistant/
├── server/          MCP server (Python, FastAPI, runs on VPS)
├── vault/           Knowledge base (source of truth, synced via git)
│   ├── CLAUDE.md    Agent instructions — loaded at every session
│   ├── ingest/      Drop zone — dump files here for the agent to process
│   ├── config/      Philosophy, active semester pointer, normative
│   └── years/       All academic content organized by year/semester/subject
├── scripts/         Maintenance scripts (build index, deploy)
├── Dockerfile
├── docker-compose.yml
├── PROJECT_PLAN.md  Full architecture documentation
├── PROJECT_NEEDS.md What you need to provide to deploy
└── INIT.md          First-time setup instructions
```

## Technology Stack

| Component | Choice |
|-----------|--------|
| MCP server | Python + FastMCP |
| Vector DB | LanceDB (embedded, no separate process) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, free) |
| PDF parsing | PyMuPDF |
| PDF export | Pandoc |
| HTTPS + SSL | Coolify + Let's Encrypt |
| Auth | API key in request header |
| Mobile | Claude Code Channels (Telegram) |
| Sync | Git (GitHub private repo) |

## Study Philosophy

- **Target: 5 (pass)** — above 5 is wasted time better spent on failing subjects
- **Exam-first** — study real past exams from day one, theory is reference only
- **Shallow pass** — attempt all exercises before deepening any, nothing skipped
- **Agent assists, never gatekeeps** — stuck on an exercise? Agent explains and helps through it
- **User overrides always** — agent suggests, you decide. No pushback.

## Non-Goals

- No group collaboration features
- No calendar sync
- No flashcard system
- No automatic lecture transcription
- No cloud-hosted LLM on mobile (Telegram goes through your VPS)

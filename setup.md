# setup — uni assistant

local installation steps for running the assistant on your desktop.

---

## requirements

- [docker desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [claude code](https://claude.ai/code) installed

---

## steps

### 1 — clone the repo

```bash
git clone https://github.com/jtayped/uni-assistant-template ~/uni-assistant
cd ~/uni-assistant
```

### 2 — configure timezone (optional)

copy the example env file and set your timezone:

```bash
cp .env.example .env
```

edit `.env` if your timezone differs from the default (`Europe/Madrid`):

```
TIMEZONE=Europe/Madrid
```

no api key is needed — the server binds to localhost only.

### 3 — start the server

```bash
docker-compose up -d
```

check it's running:

```bash
curl http://localhost:8000/health
# → {"status":"ok","server":"uni-assistant"}
```

### 4 — configure claude code

add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "uni-assistant": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

restart claude code. the `uni-assistant` mcp server should appear in your tool list.

### 5 — run init

open a claude code session in the repo root and say:

> "run the uni assistant init. let's set up my vault from scratch."

see `init.md` for the full procedure.

---

## stopping and updating

```bash
# stop
docker-compose down

# rebuild after code changes
docker-compose up -d --build

# rebuild the search index after bulk vault changes
docker-compose exec uni-mcp python /app/../scripts/build_index.py
```

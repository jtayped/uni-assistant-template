# uni assistant

claude code-powered academic assistant. runs locally as an mcp server — handles subjects, marks, exam history, study campaigns, and notes.

## architecture

```
desktop:  claude code  →  docker (mcp server + lancedb)  →  vault/
```

the mcp server runs in docker on your desktop. claude code connects to it over localhost. the vault is a directory of markdown files and pdfs — everything stays local.

## quick start

### 1 — start the server

```bash
docker-compose up -d
```

first time, after populating the vault, rebuild the lancedb index:

```bash
docker-compose exec uni-mcp python /app/../scripts/build_index.py
```

### 2 — configure claude code

add to your claude code settings (`~/.claude/settings.json`):

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

no api key needed — the server is bound to localhost only.

### 3 — run init

open a claude code session in the repo root and say:

> "run the uni assistant init. let's set up my vault from scratch."

the agent guides you through subjects, grade components, and file ingestion. see `init.md` for the full procedure.

## repository structure

```
uni-assistant/
├── server/          mcp server (python, fastmcp)
├── vault/           your academic knowledge base (gitignored)
│   ├── CLAUDE.md    agent instructions — loaded at every session
│   ├── ingest/      drop zone — dump files here for the agent to process
│   ├── config/      philosophy, active semester pointer, normative
│   └── years/       content organized by year/semester/subject
├── scripts/         maintenance scripts (build index)
├── Dockerfile
├── docker-compose.yml
├── init.md          first-time setup instructions
└── setup.md         local installation steps
```

## technology stack

| component | choice |
|-----------|--------|
| mcp server | python + fastmcp |
| transport | streamable http (localhost:8000) |
| vector db | lancedb (embedded, no separate process) |
| embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, free) |
| pdf parsing | pymupdf |
| pdf export | pandoc |
| runtime | docker compose |

## study philosophy

- **target: 5 (pass)** — above 5 is wasted time better spent on failing subjects
- **exam-first** — study real past exams from day one, theory is reference only
- **shallow pass** — attempt all exercises before deepening any, nothing skipped
- **agent assists, never gatekeeps** — stuck on an exercise? agent explains and helps through it
- **user overrides always** — agent suggests, you decide. no pushback.

## non-goals

- no group collaboration features
- no calendar sync
- no flashcard system
- no automatic lecture transcription
- no cloud sync or remote access

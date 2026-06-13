# Uni Assistant V2 — Project Plan

A Claude Code-powered academic assistant. The brain of everything university-related: subjects, marks, exams, study campaigns, notes, material, projects, deadlines, normative, and study philosophy. Designed for the student who studies last-minute, aims to pass, and needs a system that adapts to reality — not the textbook.

---

## Architecture Overview

```
Desktop (this machine)
├── Git repo — vault/ is the source of truth, pushed to GitHub for backup
├── Docker container — MCP server (FastAPI, localhost:8000, API key auth)
├── LanceDB vector index — persisted in a Docker named volume
├── sentence-transformers — local embeddings, no API cost
└── Claude Code — connects to local MCP server via http://localhost:8000
```

**Key principle:** Everything runs on one machine. No network latency, no VPS RAM limits. GitHub is backup only.

---

## Technology Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| MCP server language | Python | Best PDF parsing, ML ecosystem |
| Vector database | LanceDB | Embedded, fast filtered search, no separate process |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, free, fast |
| PDF parsing | PyMuPDF (fitz) | Text extraction + selective page renders + image detection |
| PDF to image | PyMuPDF render | JPEG compressed, ~50KB/page |
| Web framework | FastAPI | MCP server HTTP layer |
| Serving | localhost:8000, Docker port binding | No HTTPS needed — local only |
| Auth | API key in request headers | Simple, secure enough for local use |
| Markdown to PDF | Pandoc | Informe draft export |
| Telegram integration | Claude Code Channels | Native, maintained by Anthropic |
| Note viewer | Obsidian (optional) | Vault-compatible file structure |
| Sync | Git (GitHub private repo) | Version history, diffs, free |

---

## Repository Structure

```
uni-assistant/
├── PROJECT_PLAN.md              # this file
├── README.md                    # setup guide
├── .gitignore
│
├── server/                      # MCP server (runs on VPS)
│   ├── main.py                  # FastAPI entry point
│   ├── tools/                   # one file per MCP tool group
│   │   ├── search.py            # search_knowledge()
│   │   ├── subjects.py          # get_subject(), list_subjects()
│   │   ├── campaigns.py         # get_campaign(), update_campaign()
│   │   ├── logging.py           # log_progress()
│   │   ├── ingest.py            # ingest_file(), process_ingest_folder()
│   │   ├── marks.py             # get_marks(), compute_passing_status()
│   │   ├── time_tools.py        # get_current_time(), get_session_duration()
│   │   ├── render.py            # render_page() — on-demand PDF page render
│   │   └── export.py            # export_markdown_to_pdf() via pandoc
│   ├── ingestion/               # PDF ingestion pipeline
│   │   ├── pipeline.py          # orchestrator
│   │   ├── pdf_parser.py        # PyMuPDF text + image extraction
│   │   ├── classifier.py        # auto-classify ingest/ files
│   │   └── indexer.py           # LanceDB index build/update
│   ├── config.py                # API key, paths, settings
│   └── requirements.txt
│
├── vault/                       # the knowledge base (source of truth)
│   ├── CLAUDE.md                # root index — loaded at session start
│   ├── ingest/                  # drop zone: dump files here, agent classifies
│   │   └── .gitkeep
│   ├── config/
│   │   ├── active.md            # pointer to current semester path
│   │   ├── philosophy.md        # study philosophy and agent behavior rules
│   │   └── normative.md        # university rules, grading regulations
│   └── years/
│       └── YEAR-YEAR/
│           └── semester-N/
│               ├── INDEX.md     # semester overview, all subjects listed
│               └── subjects/
│                   └── SUBJECT-NAME/
│                       ├── INDEX.md         # marks, exam dates, components
│                       ├── content/         # notes and material
│                       │   └── TOPIC.md
│                       ├── exams/           # past exams
│                       │   └── YEAR-TYPE/   # e.g. 2024-parcial-1/
│                       │       ├── exam.md  # extracted text + exercise index
│                       │       └── images/  # selectively rendered pages (JPEG)
│                       ├── campaigns/       # study campaigns
│                       │   └── CAMPAIGN-NAME/
│                       │       ├── campaign.md  # plan, exercise queue, status
│                       │       └── log.md       # timestamped progress entries
│                       └── projects/        # deliverables
│                           └── PROJECT-NAME/
│                               ├── [your work files]
│                               └── _ai/     # NEVER include in submission zip
│                                   ├── informe_draft.md
│                                   └── informe_draft.pdf
│
└── scripts/
    ├── build_index.py           # rebuild LanceDB index from vault/
    ├── deploy.sh                # VPS setup script
    └── init.py                  # placeholder — init is done conversationally
```

---

## File Formats

### Subject INDEX.md

```markdown
---
name: Calculus
code: MAT101
semester: 2025-2026/semester-1
grading:
  scale: 0-10
  passing: 5.0
  components:
    - id: parcial_1
      name: "Parcial 1"
      weight: 0.35
      date: 2026-03-15
      score: null
      minimum: 5.0
      resittable: true
    - id: parcial_2
      name: "Parcial 2"
      weight: 0.35
      date: 2026-05-20
      score: null
      minimum: 5.0
      resittable: true
    - id: final
      name: "Final"
      weight: 0.30
      date: 2026-06-15
      score: null
      minimum: 5.0
      resittable: false
  resit:
    date: 2026-07-01
    covers: [parcial_1, parcial_2]
deliverables:
  - name: "Lab Report 1"
    due: 2026-03-01
    weight: 0.10
    minimum: 5.0
    resittable: false
    status: not_started
    notes_file: null
---

# Calculus

Brief subject description.
```

### Content file (notes / material)

```markdown
---
type: notes
source: own_notes | borrowed | internet | textbook | slides
quality: complete | partial | unknown
topic: Integration by Parts
subject: calculus
semester: 2025-2026/semester-1
date_added: 2026-01-15
---

# Integration by Parts

Content here...

[UNCLEAR: handwriting unreadable — likely discusses convergence proof]

More content...

[INCOMPLETE: notes stop here]
```

### Exam file

```markdown
---
type: exam
subject: calculus
semester_of_exam: 2024-2025
exam_type: parcial_1 | parcial_2 | final | resit
date: 2024-03-20
source_pdf: raw/calculus-parcial1-2024.pdf
pages: 4
visual_pages: [1, 2, 4]
---

# Calculus — Parcial 1 (2024)

## Exercise 1
[Page 1](images/page_001.jpg)

Extracted text: ...

## Exercise 2
...
```

### Campaign file

```markdown
---
subject: calculus
target_exam: parcial_1
exam_date: 2026-03-15
created: 2026-02-01
status: active
exams_queue:
  - id: 2024-parcial-1
    status: in_progress
    exercises_done: [1, 2]
    exercises_remaining: [3, 4, 5]
  - id: 2023-parcial-1
    status: not_started
  - id: 2022-parcial-1
    status: not_started
---

# Campaign: Calculus Parcial 1
```

### Progress log entry format

```markdown
## 2026-02-15 14:32 | +47min

**Subject:** Calculus
**Campaign:** parcial-1-2026
**Covered:** 2024 Parcial 1 — Exercise 3 (integration by parts)
**Outcome:** completed with agent help
**Notes:** struggled with boundary conditions, flagged for review
```

---

## MCP Server Tools

| Tool | Description |
|------|-------------|
| `get_current_time()` | Returns wall clock time + date. Solves the morning/afternoon session problem. |
| `get_dashboard()` | Returns all active campaigns, days to exam, progress, urgent deliverables |
| `search_knowledge(query, filters)` | Semantic search across vault. Filters: subject, type, semester |
| `get_subject(subject_id)` | Returns subject INDEX.md parsed: marks, components, status |
| `compute_marks_status(subject_id)` | Computes: current average, minimum needed, passing possible, recovery path |
| `get_campaign(campaign_id)` | Returns campaign state: exercise queue, what's done, what's next |
| `update_campaign(campaign_id, update)` | Marks exercises done, updates queue, changes status |
| `log_progress(entry)` | Writes timestamped entry to campaign log.md. Called by hook after every response. |
| `get_session_log(subject_id, since)` | Returns recent log entries for context |
| `ingest_file(path, metadata)` | Classify + parse a file, file it into vault, update index |
| `process_ingest_folder()` | Batch-process everything in ingest/ |
| `render_page(doc_id, page_number)` | Render a PDF page on demand, returns image. Requires raw PDF on VPS. |
| `export_markdown_to_pdf(file_path)` | Runs pandoc on a markdown file, outputs PDF alongside it |
| `get_normative()` | Returns university rules and grading regulations |
| `list_exams(subject_id)` | Lists all past exams for a subject, newest first |
| `search_web_normative(query)` | Fetches normative from the internet during ingestion |

---

## Core Behaviors

### Session Start (every Claude Code session)
1. `get_current_time()` — establish real wall clock
2. `get_dashboard()` — show status: campaigns, days to exams, deliverables due soon
3. Agent suggests highest-priority action, user decides

### Study Campaign Loop
1. Agent presents next exercise from queue (real exam exercise, as-is)
2. Student attempts
3. If stuck: agent explains, helps through it — never skips, never gatekeeps
4. `log_progress()` fires automatically after every agent response (via hook)
5. Exercise marked done, queue advances
6. After full shallow pass: deepen easiest exercises, re-attempt harder ones

### Campaign Strategy Rules
- Exams ordered newest to oldest
- Shallow pass over everything before deepening anything
- Nothing skipped — even hard exercises get attempted (partial credit)
- Agent flags topics appearing in 3+ recent exams as high-yield
- Agent suggests, user overrides — user decision is always final
- Agent never assumes the student has unlimited time

### Study Philosophy (config/philosophy.md)
- Target grade: 5 (pass) in all subjects
- Time is zero-sum: time on a subject above 5 is time stolen from a failing subject
- If passing is mathematically impossible: flag it, recommend redirecting time
- Student profile: studies last minute, doesn't attend all classes, notes may be incomplete
- Never assume notes are complete or correct

### PDF Ingestion Pipeline
1. Receive file (from ingest/ folder or direct upload)
2. Extract text per page (always)
3. Detect visually complex pages (embedded images, dense vector graphics)
4. Render only visual pages as compressed JPEG (~150dpi)
5. Write `exam.md` (text + image references + exercise index)
6. Commit markdown + images to git
7. Update LanceDB index
8. Raw PDF stays on VPS only (gitignored)

### Note Uncertainty Handling
- `source` frontmatter: `own_notes | borrowed | internet | textbook | slides`
- `quality` frontmatter: `complete | partial | unknown`
- `[UNCLEAR: description]` — unreadable section, agent interpretation flagged
- `[INCOMPLETE]` — notes stop here, rest is missing
- Agent always warns when explaining from uncertain content

### Ingest Classification (hybrid)
- Agent reads filename, PDF header, content to classify automatically
- Obvious cases: filed silently
- Ambiguous cases: agent proposes classification, user confirms
- Classification determines: subject, exam year/type, content type, semester

### Deliverables & Informes
- Tracked in subject INDEX.md frontmatter (deadline, weight, minimum, resittable, status)
- `_ai/` folder inside each project: `informe_draft.md` + `informe_draft.pdf`
- `_ai/` is clearly labeled — never include in submission archives
- `export_markdown_to_pdf()` tool runs pandoc on the draft
- Agent drafts informe in markdown; user translates to Word for final formatting

---

## Deployment

### Local Setup (Docker)
```bash
# 1. Start the container
docker compose up -d --build

# 2. Build the vector index
docker compose exec uni-mcp python scripts/build_index.py

# 3. Configure Claude Code MCP server:
#    URL:     http://localhost:8000/sse
#    API key: value from .env
```

To rebuild the index after adding files:
```bash
docker compose exec uni-mcp python scripts/build_index.py
```

### .gitignore
```
vault/*/raw/          # raw PDFs
.index/               # LanceDB index
server/config.py      # API key
*.env
__pycache__/
```

---

## Build Roadmap

### Phase 1 — Scaffold
- [ ] Repository structure
- [ ] CLAUDE.md root index
- [ ] `vault/config/philosophy.md` template
- [ ] `vault/config/active.md` template
- [ ] MCP server skeleton (FastAPI, API key middleware)
- [ ] `get_current_time()` and `get_dashboard()` tools (stubs)

### Phase 2 — Marks & Subjects
- [ ] Subject INDEX.md schema + parser
- [ ] `get_subject()` tool
- [ ] `compute_marks_status()` tool (weighted average, minimum needed, passing check, recovery)
- [ ] Dashboard marks summary

### Phase 3 — PDF Ingestion Pipeline
- [ ] PyMuPDF text extraction per page
- [ ] Visual page detection
- [ ] Selective JPEG rendering
- [ ] Exam markdown writer (text + image references + exercise index)
- [ ] `ingest_file()` and `process_ingest_folder()` tools
- [ ] Classifier (auto-detect exam type, subject, year)
- [ ] `render_page()` on-demand tool

### Phase 4 — Vector Index
- [ ] LanceDB schema (chunk text, frontmatter metadata, embeddings)
- [ ] `build_index.py` — full vault indexer
- [ ] Incremental index update on ingest
- [ ] `search_knowledge()` tool with filters

### Phase 5 — Campaigns
- [ ] Campaign file schema + parser
- [ ] `get_campaign()` and `update_campaign()` tools
- [ ] `list_exams()` tool (newest-to-oldest)
- [ ] Exercise queue management
- [ ] `log_progress()` tool
- [ ] Claude Code hook: fire `log_progress()` after every response

### Phase 6 — Session Dashboard
- [ ] `get_dashboard()` full implementation
- [ ] Days-to-exam countdown
- [ ] High-yield topic detection (appears in 3+ recent exams)
- [ ] Deliverable deadline surfacing (14-day window)

### Phase 7 — Informe Export
- [ ] `export_markdown_to_pdf()` tool (pandoc wrapper)
- [ ] `_ai/` folder convention enforced in ingest/project creation

### Phase 8 — VPS Deployment
- [ ] nginx config template
- [ ] Let's Encrypt setup guide
- [ ] tmux startup script for Claude Code Channels
- [ ] `deploy.sh` script

### Phase 9 — Init (Conversational)
- [ ] `INIT.md` — agent instructions for guided first-time setup
- [ ] Prompts the user through: university, semester, subjects, exam dates, marks so far
- [ ] Triggers mass ingest of existing files
- [ ] Creates full folder structure
- [ ] Pushes initial commit to GitHub

---

## Non-Goals (V2)
- No group project collaboration features
- No calendar sync (deadlines are tracked manually here)
- No flashcard system
- No automatic note generation from lectures
- No mobile / Telegram integration (dropped — VPS too underpowered, adds complexity)

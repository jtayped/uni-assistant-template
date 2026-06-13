# First-Time Init — Uni Assistant V2

This file guides the agent through setting up a new vault. It is read by the agent at the start of an init session.

---

## When to Run Init

Run init when:
- This is your first time setting up the assistant
- You are starting a new semester and want a fresh structure
- You want to mass-ingest an existing folder of notes, exams, and material

---

## How to Start Init

Open a Claude Code session in the repo root and say:

> "Run the uni assistant init. Let's set up my vault from scratch."

The agent will read this file and guide you through the process conversationally.

---

## Agent Init Script

When the user triggers init, follow these steps in order. Ask one group of questions at a time. Confirm before moving on.

### Step 1 — University and Semester

Ask the user:
1. What university are you at?
2. What is the current academic year? (e.g., 2025-2026)
3. Which semester are you in? (1st / 2nd)
4. What is the semester start date and exam period dates?

Then:
- Update `vault/config/active.md` with `semester_path`, `semester_label`, `university`.
- Create `vault/years/YEAR-YEAR/semester-N/INDEX.md` with a blank subject list.

### Step 2 — Subjects

For each subject, ask:
1. Subject name and code (e.g., "Calculus — MAT101")
2. Grade components:
   - For each: name, weight (%), date, minimum mark (default 5.0), resittable? (y/n)
3. Any scores already in? (e.g., "I got a 6.5 on Parcial 1")
4. Resit: date, which components does it cover?
5. Any deliverables (lab reports, projects)?
   - For each: name, due date, weight, minimum, resittable?

Then:
- Create `vault/years/.../subjects/SUBJECT-NAME/INDEX.md` with the full YAML frontmatter.
- Create `vault/years/.../subjects/SUBJECT-NAME/content/` folder.
- Create `vault/years/.../subjects/SUBJECT-NAME/exams/` folder.

Repeat until all subjects are done.

### Step 3 — Normative

Ask:
1. Is your university's normative (grading rules, resit policies) published online?
   - If yes: search for it and ingest the key rules into `vault/config/normative.md`.
   - If no: ask the user to paste or describe the key rules.

### Step 4 — Existing Files

Ask:
1. Do you have existing notes, exams, or material to import?
2. If yes: ask them to drop files into `vault/ingest/` and then call `process_ingest_folder()`.
3. Work through each file: confirm classification for ambiguous ones, ingest each.

### Step 5 — First Campaign (Optional)

Ask:
1. Do you want to start a study campaign right now?
2. If yes: which subject, which exam are you preparing for, when is it?

Then:
- Call `list_exams(subject)` to show available past exams.
- Create `vault/years/.../subjects/SUBJECT/campaigns/CAMPAIGN-NAME/campaign.md` with the queue.
- Create an empty `log.md` alongside it.
- Kick off the first exercise from the newest exam.

### Step 6 — Confirm and Commit

Show a summary of what was created:
- Subjects and their grade structures
- Files ingested
- Campaigns started (if any)

Tell the user:
> "Run `git add -A && git commit -m 'init: vault setup' && git push` to save this to GitHub."

Then offer to run `scripts/build_index.py` to index everything.

---

## File Templates

### Subject INDEX.md

```markdown
---
name: <Subject Name>
code: <CODE>
semester: <year/semester-N>
grading:
  scale: 0-10
  passing: 5.0
  components:
    - id: parcial_1
      name: "Parcial 1"
      weight: 0.35
      date: <YYYY-MM-DD>
      score: null
      minimum: 5.0
      resittable: true
  resit:
    date: <YYYY-MM-DD>
    covers: [parcial_1, parcial_2]
deliverables: []
---

# <Subject Name>

<brief description>
```

### Campaign campaign.md

```markdown
---
subject: <subject-folder-name>
target_exam: <parcial_1 | parcial_2 | final | resit>
exam_date: <YYYY-MM-DD>
created: <YYYY-MM-DD>
status: active
exams_queue:
  - id: <YEAR-exam-type>
    status: not_started
    exercises_done: []
    exercises_remaining: []
---

# Campaign: <Subject> <Target>
```

### Campaign log.md

```markdown
# Progress Log — <Subject> <Campaign>
```
(entries are appended by the agent via log_progress() tool)

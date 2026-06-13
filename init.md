# first-time init — uni assistant

this file guides the agent through setting up a new vault. it is read by the agent at the start of an init session.

---

## when to run init

run init when:
- this is your first time setting up the assistant
- you are starting a new semester and want a fresh structure
- you want to mass-ingest an existing folder of notes, exams, and material

---

## how to start init

open a claude code session in the repo root and say:

> "run the uni assistant init. let's set up my vault from scratch."

the agent will read this file and guide you through the process conversationally.

---

## agent init script

when the user triggers init, follow these steps in order. ask one group of questions at a time. confirm before moving on.

### step 1 — university and semester

ask the user:
1. what university are you at?
2. what is the current academic year? (e.g., 2025-2026)
3. which semester are you in? (1st / 2nd)
4. what is the semester start date and exam period dates?

then:
- update `vault/config/active.md` with `semester_path`, `semester_label`, `university`.
- create `vault/years/YEAR-YEAR/semester-N/INDEX.md` with a blank subject list.

### step 2 — subjects

for each subject, ask:
1. subject name and code (e.g., "calculus — MAT101")
2. grade components:
   - for each: name, weight (%), date, minimum mark (default 5.0), resittable? (y/n)
3. any scores already in? (e.g., "i got a 6.5 on parcial 1")
4. resit: date, which components does it cover?
5. any deliverables (lab reports, projects)?
   - for each: name, due date, weight, minimum, resittable?

then:
- create `vault/years/.../subjects/SUBJECT-NAME/INDEX.md` with the full yaml frontmatter.
- create `vault/years/.../subjects/SUBJECT-NAME/content/` folder.
- create `vault/years/.../subjects/SUBJECT-NAME/exams/` folder.

repeat until all subjects are done.

### step 3 — normative

ask:
1. is your university's normative (grading rules, resit policies) published online?
   - if yes: search for it and ingest the key rules into `vault/config/normative.md`.
   - if no: ask the user to paste or describe the key rules.

### step 4 — existing files

ask:
1. do you have existing notes, exams, or material to import?
2. if yes: ask them to drop files into `vault/ingest/` and then call `process_ingest_folder()`.
3. work through each file: confirm classification for ambiguous ones, ingest each.

### step 5 — first campaign (optional)

ask:
1. do you want to start a study campaign right now?
2. if yes: which subject, which exam are you preparing for, when is it?

then:
- call `list_exams(subject)` to show available past exams.
- create `vault/years/.../subjects/SUBJECT/campaigns/CAMPAIGN-NAME/campaign.md` with the queue.
- create an empty `log.md` alongside it.
- kick off the first exercise from the newest exam.

### step 6 — confirm

show a summary of what was created:
- subjects and their grade structures
- files ingested
- campaigns started (if any)

then offer to run `scripts/build_index.py` to index everything:

```bash
docker-compose exec uni-mcp python /app/../scripts/build_index.py
```

---

## file templates

### subject INDEX.md

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

### campaign campaign.md

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

# campaign: <subject> <target>
```

### campaign log.md

```markdown
# progress log — <subject> <campaign>
```
(entries are appended by the agent via log_progress() tool)

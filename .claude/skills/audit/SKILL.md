---
name: audit
description: Audit the current session/branch and update the shared .md context (MEMORY.md, CLAUDE.md files, docs/course/requirements.md status, docs/tasks.md, docs) so every teammate's AI has the same up-to-date picture. Use when the user types /audit, or at the end of a task before committing.
argument-hint: "[optional: focus]"
---

# /audit: bring the shared context up to date

The team's AIs share context only through files on `main`: `CLAUDE.md` (root + folders), `MEMORY.md`,
`docs/course/requirements.md`, `docs/tasks.md`, `docs/*.md`. Your job: make them match reality after this session.

## 1. What happened
- This session: decisions taken, problems found, things built, things the user said (e.g. "we use 60 Hz").
- The branch: `git diff --stat origin/main...HEAD`, uncommitted `git diff`, `git log origin/main..HEAD --oneline`.
- Read the current `MEMORY.md` and the docs that cover the touched areas.

## 2. Decide what to write (only facts, nothing guessed)
| Happened | Goes to |
|---|---|
| decision made / option rejected | `MEMORY.md` → Decisions (one dated line) |
| gotcha, bug, surprising behaviour | `MEMORY.md` → Known problems / gotchas |
| status changed (something now works / exists) | `MEMORY.md` → Current status (update the line, bump the date) |
| question answered | remove it from Open questions (MEMORY.md and `requirements.md`), record the answer as a decision |
| new open question | Open questions |
| checklist item progressed | status column of `docs/course/requirements.md` |
| task done / new task / owner changed | `docs/tasks.md` |
| code behaviour, interface, file format, command changed | the `CLAUDE.md` of that folder and/or `docs/architecture.md` |

## 3. Rules for the edits
- MEMORY.md format: `- YYYY-MM-DD XX – text` (XX = initials of the user, from `git config user.name`; ask if unclear),
  newest first in its section, one line where possible, < 150 lines total.
- **Delete or rewrite lines that are no longer true**; don't stack contradictions. Fix docs that now contradict the code.
- Short, precise, no narrative of the session ("we tried…"). Only what a teammate needs next time.
- Don't change frozen interfaces or decisions by writing docs. If the session changed one without team agreement → flag it.
- Never write names, keys or personal data. Edit only `.md` files (and nothing in `docs/course/` except `requirements.md`).

## 4. Report
Show a short list of every file changed and the one-line reason for each, plus anything you were unsure about
(not written). Remind: commit these in the **same PR** as the work (`/gitup end`), so `main` stays the shared truth.

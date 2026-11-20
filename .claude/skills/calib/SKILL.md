---
name: calib
description: Corrector for SEMGIA. Checks whether the work in this session or on the current branch fits the user's own task, the project rules and the course assignment, then corrects what drifted. Use when the user types /calib, or asks "is this on track / does this fit the assignment".
argument-hint: "[optional: what to check, e.g. a file, the branch, or 'session']"
---

# /calib: are we still building the right thing?

Goal: catch drift early. Compare **what was done** against **what is required**, report it briefly, then fix it.

## 1. Collect what was done
- Scope = the argument if given; otherwise this session's changes **and** the current branch:
  `git branch --show-current`, `git status`, `git diff --stat origin/main...HEAD`, `git diff` (uncommitted).
- Read the changed files (not just the stat).

## 2. Collect what is required
Read, in this order (higher wins on conflict):
1. `docs/course/report1_assignment.md`: the assignment (authoritative).
2. `docs/course/requirements.md`: checklist, owners, mapping of course words, open questions.
3. `CLAUDE.md` (root + the folders touched) and `MEMORY.md`: hard rules, frozen interfaces, decisions.
4. `docs/tasks.md`: the user's role. Find the role from the branch prefix / `git config user.name`; ask if unclear.

## 3. Check (one line per finding, cite file:line and the rule's source)
- **Assignment:** does it serve a checklist item or the final goal (> 75 % on unseen sessions, record + metadata in
  the cloud)? Exact required file names/locations/columns? Copies the professor's example (forbidden)?
  Fair split kept (choose on train sessions only, test opened once, no windows of one recording on both sides)?
- **Own task:** inside the user's role and owned files? Touches someone else's files → flag.
- **Project rules:** frozen interfaces unchanged (or MEMORY.md agreement exists); labels only from the timer; constants
  only in `semgia/config.py`; one feature path for live + offline; no new dependency / framework / service without a
  MEMORY.md note; tests for `semgia/` changes; privacy (codes only, no faces/names/keys); Azure never blocks recording.
- **Scope creep:** work nobody asked for, gold-plating, a second way of doing something that already exists.
- **Consistency:** docs say what the code does; numbers in docs match config (e.g. notch, window sizes).

## 4. Report, then correct
Report first, short, grouped: **Blocking** (breaks a hard rule or the assignment) · **Drift** (outside the role
or scope) · **Fine**. Then:
- Clear-cut fixes inside the user's own files (wrong file name, missing column, magic number, missing test,
  outdated doc line) → fix them, run `pytest -q && ruff check .`, say what changed.
- Anything that changes a frozen interface, touches another person's files, removes work, or needs a judgement call
  about the assignment → **ask first**, with the options and your recommendation.
- Unclear requirement → don't guess. Add it to "Open questions" in `docs/course/requirements.md` only if the user agrees.
End with one line: "On track" / "On track after fixes" / "Needs a decision: …".

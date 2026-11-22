---
name: gitup
description: Start or finish a SEMGIA task with Git the team's way (branch per task, checks, commit with a why, push, PR, squash merge). Use when a teammate types /gitup start <task>, /gitup end, /gitup merge, /gitup sync or /gitup status.
argument-hint: "start <short-task> | end | merge | sync | status"
disable-model-invocation: true
---

# /gitup: Git for one task, start to finish

Rules come from `docs/git_workflow.md`, `CONTRIBUTING.md`, `docs/tasks.md` (ownership) and the course
(`docs/course/requirements.md`). Commands work in bash and PowerShell (teammates use Windows 11).
Show the user each command you run. Stop and ask on anything unexpected (conflicts, foreign changes, dirty `main`).

## Who owns what (from docs/tasks.md)
| Person | Owns |
|---|---|
| P1 Hardware & recordings | `firmware/`, `semgia/sources.py`, `docs/protocol.md` / `PROTOCOL.md`, `data/raw/`, `figures/`, `cue/` |
| P2 AI (Ben) | `semgia/processing.py`, `semgia/model.py`, `scripts/train.py`, `scripts/evaluate.py`, `DECISIONS.md` 7–8, `QUALITY-REPORT.md`, `data/metadata.csv` scripts |
| P3 Azure & privacy | `semgia/storage.py`, `docs/azure_setup.md`, `docs/privacy.md`, dashboard deployment, `DECISIONS.md` 9 |
| P4 Interface & dashboard | `scripts/record.py`, `semgia/recorder.py`, `dashboard/app.py`, `README.md`, CI, tags |
| Everyone | own `rationale/Mxx.md`, `ai-tools/Mxx.png`, own line in PROTOCOL.md, `MEMORY.md` lines |
Shared files (`CLAUDE.md`, `MEMORY.md`, `docs/course/requirements.md`): small edits only, pull right before.

## Iron rules
- Never commit or push on `main`. Never `push --force` to `main`. `--force-with-lease` only on your own branch.
- Branch = `name/short-task`, lower case, e.g. `ben/notch-60hz`. One task = one branch = one PR, ½–2 days.
- Each member commits from **their own** GitHub account (course requirement). Check `git config user.name` matches the person.
- Never commit: `.env`, keys, connection strings, name lists, real names, faces, videos > 20 MB, `data/synthetic/`,
  `models/` caches, `__pycache__`. Raw recordings in `data/raw/` only via a `name/data-YYYY-MM-DD` branch.
- Only commit code that was run. Commit message: first line = what (< 60 chars, imperative), body = why + what you tested.

## `start <short-task>`
1. `git status`. Uncommitted changes → ask: commit them first, stash, or stop.
2. `git switch main` → `git pull`.
3. Derive the name from `git config user.name` (ask if unclear) → `git switch -c <name>/<short-task>`.
4. Read `MEMORY.md` and the `CLAUDE.md` of the folders the task touches. Tell the user in 3–5 lines: what the task is
   for (which checklist item in `docs/course/requirements.md`), which files they own for it, and anything in MEMORY.md
   that affects it. If the files belong to someone else → warn.

## `end`
1. `git status` + `git diff --stat`. List the changed files and check each against the ownership table. Files of
   another person or unrelated changes → ask whether to drop them or split them into another branch.
2. Scan the diff for secrets / names / big files (see iron rules). Found → stop and fix first.
3. Run the checks: `pytest -q && ruff check .` (if missing: `python -m pytest -q`, `python -m ruff check .`).
   Red → stop, show the error, offer to fix. Never commit red.
4. Decision made, gotcha found or status changed? → suggest running `/audit` first (MEMORY.md line in the same PR).
5. Stage only the files that belong to the task (`git add <paths>`, not blindly `-A`). Write the commit message
   (what + why + tested) and show it. Commit.
6. `git push -u origin <branch>`.
7. PR: `gh pr create --base main` with the template in `.github/pull_request_template.md` filled in (What, Closes #,
   How I tested it, checklist). No `gh` → give the GitHub "Compare & pull request" link and stop.
8. Merge: continue with `merge` below. No teammate approval needed (team rule since 2026-11-19).

## `merge` (the AI is the housekeeper: it merges when every gate is green)
Gates, all required. Any gate fails → stop, show why, ask the user. Never merge around a gate.
1. Ownership + secrets checks of `end` passed (no foreign files without the user's OK, nothing secret).
2. `main` moved since the branch started? → run `sync` first (conflicts → ask, never guess).
3. CI green: `gh pr checks <pr> --watch` (wait for it; red → stop, offer to fix).
4. No conflicts: `gh pr view <pr> --json mergeable,mergeStateStatus` → `MERGEABLE` and `CLEAN`.
Then: `gh pr merge <pr> --squash --delete-branch` → `git switch main && git pull` → tell the user the merge commit
and that teammates get it with `git pull`.

## `sync` (branch older than a day, or `main` moved)
`git fetch` → `git switch main && git pull` → `git switch <branch> && git merge main`. Conflict → show files,
explain both sides, ask which to keep, never guess on someone else's file. Then rerun the checks.
If the branch was based on another, now squash-merged branch: `git rebase --onto origin/main <old-base> <branch>`
then `git push --force-with-lease` (explain this first).

## `status`
Current branch, ahead/behind `origin/main`, uncommitted files, open PRs (`gh pr list`), and whether the branch's
files match the user's role. One short block, no actions.

## Course extras (remind when relevant)
Tags `v0-first` and `v1-report` (P4, on `main` only, `git tag <t> && git push origin <t>`); every member ≥ 1 commit;
professor added as collaborator.

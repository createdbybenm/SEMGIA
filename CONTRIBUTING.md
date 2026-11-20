# Contributing

1. Pick or create an issue on the Project board. Assign it to yourself and move it to *Doing*.
2. `git switch main && git pull && git switch -c yourname/short-task`
3. Build it (vibecoding is fine), **run it yourself**, add a test.
4. `pytest -q && ruff check .`
5. Commit, push, open a PR (`Closes #<issue>`). Fill in the checklist.
6. One teammate reviews → squash merge → the issue moves to *Done*.

Rules:
- Never push to `main`. Keep branches ≤ 1–2 days.
- No names, `.env` or keys in Git. See [docs/privacy.md](docs/privacy.md).
- Decision made or gotcha found → add one dated line to [MEMORY.md](MEMORY.md) in the same PR.
- Changing a frozen interface (see CLAUDE.md) → talk to the team first.

Command cheat sheet: [docs/git_workflow.md](docs/git_workflow.md). Tasks per week: [docs/tasks.md](docs/tasks.md).

## Using Claude Code (or other AI assistants)
- Team skills in `.claude/skills/`: `/gitup start <task>` → work → `/calib` → `/audit` → `/gitup end`. `/docit <file>` for docs.
- `CLAUDE.md` (root + every folder) and `MEMORY.md` are loaded automatically, so all of us share the same context.
- Start a task with: *"Read MEMORY.md and the CLAUDE.md of the folder, then do issue #12."*
- End a task with: *"Update MEMORY.md with what changed."*
- Personal notes → `CLAUDE.local.md` (gitignored).

# SEMGIA – project rules for AI assistants

Single-channel sEMG → **contraction / rest** classifier for **one patient, one muscle**.
It must stay robust to electrode re-placement and fatigue. Team of 4, 3 weeks (2026-11-03 → 2026-11-24).
AI runs **locally**. Azure only stores data + predictions + metadata and shows a dashboard.

## The assignment comes first
This is a graded course project (M6 ML & IoT, Tec). **What we must hand in is in @docs/course/requirements.md.**
- The Report 1 PDF (`docs/course/report1_assignment.md`) is authoritative. Slides are background. The PDF wins.
- **Report 1 due Sat 2026-11-21 23:59**: required root files README.md (six parts), PROTOCOL.md, DECISIONS.md,
  QUALITY-REPORT.md, `data/metadata.csv`, `rationale/`, `ai-tools/`, cue video, electrode photos, tags. Final class 2026-11-24.
- Before building anything, check it serves a checklist item. Never deviate from the assignment without asking the user.
- Fair split: choose features/models on **training sessions only**; the test sessions are opened once, at the end.

## The #1 rule: simple and robust
- Prefer the boring solution. No new framework, service or abstraction unless MEMORY.md says the team agreed.
- Everything must have a fallback: no sensor → `--source mock`/`file`, no Azure → offline, weak ML → threshold model.
- If something is unclear, ask the user. Don't invent requirements.

## Architecture (don't add boxes)
```
DFRobot SEN0240 sensor → ESP32 (12-bit, GPIO 34, firmware/HamShot_EMG) → its WEB PAGE (Wi-Fi, firmware/HamShot_EMG/pagina.h):
   calibration once per electrode placement (rest + max contraction)
   → "Collect sample" → metadata form → 24 s with cues → data/raw/sample_NNN/ (source of truth)
semgia/ + scripts/ (this repo): Filter → Windower → features → Calibration → Model → Smoother
   → train / evaluate / live AI · upload to Azure Storage (Blob + Table) ← dashboard/app.py (Streamlit)
scripts/record.py = Python GUI with the same flow, backup/demo only
```
**Transition in progress:** the code still calibrates each sample on its own first rest phase. Agreed target:
one calibration per placement from the web interface (see MEMORY.md). Don't build on per-sample calibration.
Details: @docs/architecture.md

## Hard rules
- **Privacy:** never write real names, birth dates or other identifying data into code, data, logs, commits, tests or Azure.
  Subjects are `P001`, operators `OP01` (validated in `semgia/storage.py:make_metadata`).
- Never commit `.env`, keys or connection strings. Config comes from `.env` (see `.env.example`).
- Local save comes first. The Azure upload is best effort and **must never raise or block** the recording.
- **Frozen interfaces** (only change them after team agreement + a MEMORY.md entry):
  `Source.read()/set_cue()/close()`, `Model.predict(features) -> int`, `METADATA_FIELDS`,
  the `signal.csv` columns `t_s,value,label`, the sample protocol `config.SAMPLE_STEPS` (rest 8 / contract 8 / rest 8 s),
  the serial format `<int>\n`.
- **Labels come only from the timer** (row number / FS + `SAMPLE_STEPS`), never from the signal or the person.
  Transitions are NOT cut out of the CSV. Training drops them in code (`processing.clean_mask`, `config.TRIM_S`).
- All constants live in `semgia/config.py`. No magic numbers anywhere else.
- Live and offline code use the **same** `Filter`/`Windower`/`features`. Never write a second feature path.

## Code style
- Python 3.11+, plain functions and small classes, type hints, short docstrings. Match the surrounding code.
- Dependencies only from `requirements.txt` (dashboard: `dashboard/requirements.txt`). Adding one = a MEMORY.md note.
- Every module in `semgia/` has tests in `tests/`. Before committing, run: `pytest -q && ruff check .`
- Scripts in `scripts/` are thin CLIs (argparse) around `semgia/`.

## Git
- Never commit to `main`. Branch = `name/short-task` (e.g. `ben/serial-reader`). Small PR → squash merge by `/gitup merge`
  once CI is green and there are no conflicts. No teammate approval needed.
- Only commit code you actually ran. See docs/git_workflow.md.

## Team skills (`.claude/skills/`, shared via Git)
`/gitup start <task>` · `/gitup end` (branch, checks, commit, PR) · `/calib` (does this work fit my task + the assignment?)
· `/docit <file>` (clear, short, exact docs) · `/audit` (update MEMORY.md + docs after a session). Typical task:
`/gitup start` → work → `/calib` → `/audit` → `/gitup end`.

## Shared memory
@MEMORY.md is the team's shared memory. **When a decision is made, a gotcha is found or the status changes,
add one dated line there in the same PR.** Keep it short and delete outdated lines.
Personal notes go in `CLAUDE.local.md` (gitignored).

## Useful commands
```
pip install -r requirements.txt
python scripts/record.py --source mock              # recording app without hardware
python scripts/make_mock_samples.py && python scripts/evaluate.py --data data/synthetic
streamlit run dashboard/app.py
```
Each folder has its own CLAUDE.md with the details for that folder.

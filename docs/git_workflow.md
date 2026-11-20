# Git workflow (cheat sheet)

**Rule:** `main` always works. You never commit on `main`. Everything goes through a Pull Request.

## Once
```
git clone https://github.com/createdbybenm/SEMGIA.git
cd SEMGIA
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                     # paste the Azure key (optional)
```
Repo owner, once: Settings → Branches → add rule for `main`: *Require a pull request (0 approvals)*,
*Require status checks (CI)*. Settings → General → allow only **Squash merging**, enable *Automatically delete head branches*.

## Every task
```
git switch main && git pull                  # start from the newest main
git switch -c ben/serial-reader              # new branch: name/short-task
# ... work, run it, test it ...
pytest -q && ruff check .                    # must pass
git add -A && git commit -m "Add serial reader"
git push -u origin ben/serial-reader
gh pr create --fill                          # or click "Compare & pull request" on GitHub
```
CI green + no conflicts → *Squash and merge* (or `/gitup merge`) → the branch gets deleted. No approval needed.

## Every morning (when your branch is older than a day)
```
git switch main && git pull
git switch ben/serial-reader && git merge main
```

## Merge conflict
1. `git status` shows the files. Open them and look for `<<<<<<<` … `>>>>>>>`.
2. Keep the right parts and remove the markers. Ask the other person if unsure.
3. `git add <file> && git commit` → `pytest -q` → push.

## Habits that prevent pain
- Small branches (½–1 day), merged quickly. Two people shouldn't edit the same file at the same time; check the board first.
- Issues + Project board (Todo / Doing / Done): one issue = one branch = one PR. Write `Closes #12` in the PR.
- Commit messages: short, imperative ("Add notch filter", "Fix calibration with negative span").
- Before pushing: `git status`, and check that there's no `.env`, no name list, no huge files.
- Something broke on main? `git revert <commit>` via PR. Never `push --force` on main.

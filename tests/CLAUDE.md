# tests/ – pytest

Run everything: `pytest -q` (CI runs this + `ruff check .` on every PR).

## Rules
- One test file per area: `test_processing.py`, `test_model.py`, `test_evaluation.py`, `test_report.py`,
  `test_sources_storage.py`. Add to them before creating new ones.
- Tests must run without hardware, internet or Azure: use `MockSource`, `make_sample(tmp_path, ...)` and
  `AzureUploader(..., conn_str="")`. Never read from or write to the real `data/raw`. Use `tmp_path`.
- Fast: the whole suite stays under ~10 s. Use `MockSource.generate(n)` instead of real-time `read()` + sleep.
- Test behaviour, not implementation: e.g. "chunked == whole", "names are rejected", "model > 95% on an unseen placement", "a sample has exactly 24 000 labelled rows".
- A bug fix comes with a test that would have caught it.

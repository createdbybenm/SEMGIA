# SEMGIA – sEMG contraction detection

Detects whether a muscle is **contracting or at rest** from a single surface-EMG channel, live, on your laptop.
Measurements are stored pseudonymized in Azure and shown on a small dashboard.

## Quickstart (no hardware, no Azure needed)
```
git clone https://github.com/createdbybenm/SEMGIA.git && cd SEMGIA
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/record.py --source mock                 # recording app with fake EMG
streamlit run dashboard/app.py                         # dashboard (local mode)
```
Train & evaluate on fake data:
```
python scripts/make_mock_samples.py
python scripts/train.py --data data/synthetic
python scripts/evaluate.py --data data/synthetic
```
With the real sensor: flash `firmware/emg_serial`, then `python scripts/record.py --source serial --port COM3` (Linux: `/dev/ttyACM0`).
With Azure: `cp .env.example .env` and add the connection string (see `docs/azure_setup.md`).

## How it works
Recording happens in our web interface (separate repo); `scripts/record.py` is a Python backup with the same flow.
Electrodes on → calibrate once (rest + max contraction) → press **Collect sample**, fill in the metadata form, and the app records one continuous 24 s sample
(rest 8 s → contract 8 s → rest 8 s) into `data/raw/sample_NNN/`. Labels come from the timer. Training uses only
the clean middle of each phase. Signals are scaled by the placement's calibration, which makes the model robust to new
electrode placements. Model: threshold or logistic regression on RMS/MAV/WL/ZC of 200 ms windows. More in [docs/architecture.md](docs/architecture.md).

## Repo layout
| Folder | Content |
|---|---|
| `semgia/` | core package: sources, processing, models, storage |
| `scripts/` | recording app, train, evaluate, upload, mock data |
| `dashboard/` | Streamlit dashboard (Azure App Service) |
| `firmware/` | Arduino sketch |
| `data/raw/` | recorded samples (pseudonymized) |
| `models/` | trained models |
| `docs/` | architecture, protocol, privacy, Azure setup, Git workflow, tasks |
| `notebooks/` | exploration |
| `tests/` | pytest |

## Team workflow
Read [CONTRIBUTING.md](CONTRIBUTING.md). AI assistants: [CLAUDE.md](CLAUDE.md) + [MEMORY.md](MEMORY.md).

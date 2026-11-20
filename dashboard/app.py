"""SEMGIA dashboard (Streamlit). Read-only view of what the recording app uploaded.

    streamlit run dashboard/app.py

Uses Azure Storage if AZURE_STORAGE_CONNECTION_STRING is set, otherwise falls back to
the local data/raw folder (so you can develop it without Azure).
Self-contained on purpose: does not import the semgia package (deployed alone to App Service).
"""

import json
import os
import time
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
CONN = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
LOCAL = Path(__file__).resolve().parent.parent / "data" / "raw"
FS = 1000
STEP_S = 0.1                                   # one AI prediction per 100 ms window
STEPS = [(0, 8), (1, 8), (0, 8)]              # = semgia/config.py SAMPLE_STEPS (dashboard is self-contained)

st.set_page_config(page_title="SEMGIA Dashboard", layout="wide")


# ---------- data access (Azure or local) ----------

@st.cache_resource
def clients():
    from azure.data.tables import TableServiceClient
    from azure.storage.blob import BlobServiceClient
    tables = TableServiceClient.from_connection_string(CONN)
    return (BlobServiceClient.from_connection_string(CONN).get_container_client("signals"),
            tables.get_table_client("samples"), tables.get_table_client("predictions"))


def load_samples() -> pd.DataFrame:
    if CONN:
        rows = [dict(e) for e in clients()[1].query_entities("PartitionKey eq 'sample'")]
    else:
        rows = [json.loads(p.read_text()) for p in LOCAL.glob("*/metadata.json")]
    df = pd.DataFrame(rows)
    return df.drop(columns=["PartitionKey", "RowKey"], errors="ignore").sort_values(
        "start_time_utc", ascending=False) if len(df) else df


def timer_label(t_s) -> pd.Series:
    """Label from the protocol timer (0 rest / 1 contract), the same rule as semgia.recorder.label_at."""
    t = pd.Series(t_s, dtype=float)
    out, start = pd.Series(0, index=t.index), 0
    for label, dur in STEPS:
        out[(t >= start) & (t < start + dur)] = label
        start += dur
    return out


def snap(t_s: pd.Series) -> pd.Series:
    """Window end times -> 100 ms grid (samples don't start on a window edge; Azure has no exact times)."""
    return ((t_s / STEP_S).round() * STEP_S).round(3)


def chunk_rows(rows: list[dict]) -> pd.DataFrame:
    """Azure predictions rows (one per 2 s chunk, `labels` = one AI output per window) -> t_s, prediction."""
    out = []
    for e in sorted(rows, key=lambda e: e["t0_s"]):
        preds = str(e.get("labels") or "")
        end = e["t0_s"] + e["n"] / FS                    # windows end inside the chunk, 100 ms apart
        out += [(end - (len(preds) - 1 - i) * STEP_S, int(c)) for i, c in enumerate(preds)]
    df = pd.DataFrame(out, columns=["t_s", "prediction"])
    df["t_s"] = snap(df.t_s)
    return df


def load_predictions(sid: str) -> pd.DataFrame:
    """One row per AI window: t_s, prediction (0/1)."""
    if CONN:
        return chunk_rows([dict(e) for e in clients()[2].query_entities(f"PartitionKey eq '{sid}'")])
    p = LOCAL / sid / "predictions.csv"
    if not p.exists():
        return pd.DataFrame(columns=["t_s", "prediction"])
    df = pd.read_csv(p)
    df["t_s"] = snap(df.t_s)                             # so it lines up with the label grid below
    return df


@st.cache_data(ttl=30)
def summary() -> pd.DataFrame:
    """Per sample: AI contraction % and agreement % with the timer label."""
    if CONN:
        by_sid: dict[str, list] = {}
        for e in clients()[2].list_entities():
            by_sid.setdefault(e["PartitionKey"], []).append(dict(e))
        frames = {sid: chunk_rows(rows) for sid, rows in by_sid.items()}
    else:
        frames = {p.parent.name: load_predictions(p.parent.name) for p in LOCAL.glob("*/predictions.csv")}
    rows = []
    for sid, df in frames.items():
        if len(df):
            agree = (df.prediction == timer_label(df.t_s)).mean()
            rows.append({"sample_id": sid, "AI contraction %": round(100 * df.prediction.mean(), 1),
                         "agrees with label %": round(100 * agree, 1)})
    return pd.DataFrame(rows, columns=["sample_id", "AI contraction %", "agrees with label %"])


def load_signal(sid: str) -> pd.DataFrame:
    if CONN:
        container = clients()[0]
        blobs = container.list_blobs(name_starts_with=f"{sid}/")
        names = sorted(b.name for b in blobs if b.name.endswith(".csv"))
        values = []
        for name in names:
            values += [int(v) for v in container.download_blob(name).readall().decode().split()]
        return pd.DataFrame({"t_s": pd.RangeIndex(len(values)) / FS, "value": values})
    p = LOCAL / sid / "signal.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, usecols=["t_s", "value"])


# ---------- page ----------

st.title("SEMGIA – sEMG contraction monitor")
st.caption(f"Data source: {'Azure Storage' if CONN else 'local data/raw (no Azure connection string)'}")

samples = load_samples()
if samples.empty:
    st.info("No samples yet. Record one with `python scripts/record.py --source mock`.")
    st.stop()

with st.sidebar:
    sid = st.selectbox("Sample", samples.sample_id)
    auto = st.checkbox("Auto refresh (3 s)", value=True)
    st.metric("Samples recorded", len(samples))
    st.metric("Electrode placements", samples.placement_id.nunique())

meta = samples[samples.sample_id == sid].iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Subject", meta.subject_id)
c2.metric("Muscle", f"{meta.muscle} ({meta.side})")
c3.metric("Placement", meta.placement_id)
c4.metric("Effort / condition", f"{meta.effort} / {meta.condition}")
c5.metric("Operator", meta.operator_id)

preds = load_predictions(sid)
sig = load_signal(sid)

st.subheader("Raw signal (24 s: rest 8 s · contract 8 s · rest 8 s)")
if sig.empty:
    st.write("No signal data yet.")
else:
    st.line_chart(sig, x="t_s", y="value", height=250)

st.subheader("Label (timer) vs. AI output  ·  0 = rest, 1 = contraction")
if preds.empty:
    st.write("No predictions yet (the first 8 s of the sample build the rest baseline).")
else:
    k1, k2, k3 = st.columns(3)
    agree = (preds.prediction == timer_label(preds.t_s)).mean()
    k1.metric("AI: time in contraction", f"{100 * preds.prediction.mean():.0f} %")
    k2.metric("Label: time in contraction", f"{100 * timer_label(preds.t_s).mean():.0f} %",
              help="Of the windows the AI scored, the share the timer labels as contraction.")
    k3.metric("AI agrees with label", f"{100 * agree:.0f} %")
    n_steps = int(sum(d for _, d in STEPS) / STEP_S)
    grid = pd.DataFrame({"t_s": [round(i * STEP_S, 3) for i in range(n_steps + 1)]})
    grid["label (timer)"] = timer_label(grid.t_s)
    line = grid.merge(preds.rename(columns={"prediction": "AI prediction"}), on="t_s", how="left")
    st.line_chart(line, x="t_s", y=["label (timer)", "AI prediction"], height=220)

st.subheader("Contraction % per sample")
table = samples[["sample_id", "placement_id", "effort", "condition"]]
table = table.merge(summary(), on="sample_id", how="left")
st.dataframe(table, width="stretch", hide_index=True)

with st.expander("All sample metadata"):
    st.dataframe(samples, width="stretch")

if auto:
    time.sleep(3)
    st.rerun()

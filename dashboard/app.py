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


def load_predictions(sid: str) -> pd.DataFrame:
    if CONN:
        rows = [dict(e) for e in clients()[2].query_entities(f"PartitionKey eq '{sid}'")]
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)[["t0_s", "contract_ratio"]].sort_values("t0_s")
    p = LOCAL / sid / "predictions.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    df["t0_s"] = (df.t_s // 2) * 2
    df = df.groupby("t0_s", as_index=False).prediction.mean()
    return df.rename(columns={"prediction": "contract_ratio"})


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

st.subheader("AI output: share of time in contraction (per 2 s)")
if preds.empty:
    st.write("No predictions yet (the first 8 s of the first sample build the rest baseline).")
else:
    st.bar_chart(preds, x="t0_s", y="contract_ratio", height=200)

with st.expander("All sample metadata"):
    st.dataframe(samples, width="stretch")

if auto:
    time.sleep(3)
    st.rerun()

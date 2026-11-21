"""Local saving (source of truth) and Azure upload (best effort, never crashes the app).

Local layout:  data/raw/<sample_id>/metadata.json, signal.csv, predictions.csv
Azure layout:  blob  signals/<sample_id>/metadata.json, signals/<sample_id>/<seq>.csv
               table samples     (PartitionKey="sample", RowKey=sample_id, metadata fields)
               table predictions (PartitionKey=sample_id, RowKey=seq, t0_s, n, contract_ratio, labels)
"""

import json
import logging
import os
import queue
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from semgia import config

log = logging.getLogger(__name__)

METADATA_FIELDS = [
    "sample_id", "placement_id", "subject_id", "operator_id", "muscle", "side", "sensor_id",
    "electrode_type", "placement_notes", "effort", "condition", "sampling_rate_hz", "start_time_utc", "notes",
]
SUBJECT_RE = re.compile(r"^P\d{3}$")    # P001  - pseudonym only, never a name
OPERATOR_RE = re.compile(r"^OP\d{2}$")  # OP01
PLACEMENT_RE = re.compile(r"^E\d{2}$")  # E01 = first electrode placement, E02 = re-applied, ...
SAMPLE_RE = re.compile(r"^sample_(\d{3,})$")


def next_sample_id(root: Path = config.DATA_RAW) -> str:
    """sample_001, sample_002, ... (one higher than the highest folder in root)."""
    nums = [int(m.group(1)) for p in Path(root).glob("sample_*") if (m := SAMPLE_RE.match(p.name))]
    return f"sample_{max(nums, default=0) + 1:03d}"


def make_metadata(root: Path = config.DATA_RAW, **fields) -> dict:
    """Builds and checks sample metadata. Raises ValueError on anything that looks like a name."""
    if not SUBJECT_RE.match(fields.get("subject_id", "")):
        raise ValueError("Subject ID must look like P001 (pseudonym, no names!)")
    if not OPERATOR_RE.match(fields.get("operator_id", "")):
        raise ValueError("Operator ID must look like OP01")
    if not PLACEMENT_RE.match(fields.get("placement_id", "")):
        raise ValueError("Placement ID must look like E01 (new number every time electrodes are re-applied)")
    unknown = set(fields) - set(METADATA_FIELDS)
    if unknown:
        raise ValueError(f"unknown metadata fields: {unknown}")
    meta = {k: "" for k in METADATA_FIELDS}
    meta.update(sample_id=next_sample_id(root), sampling_rate_hz=config.FS,
                start_time_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    meta.update(fields)
    return meta


class LocalWriter:
    """Writes data/raw/<sample_id>/ : metadata.json, signal.csv (t_s,value,label), predictions.csv."""

    def __init__(self, metadata: dict, root: Path = config.DATA_RAW):
        self.dir = Path(root) / metadata["sample_id"]
        self.dir.mkdir(parents=True, exist_ok=False)
        (self.dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        self.signal = open(self.dir / "signal.csv", "w")
        self.signal.write("t_s,value,label\n")
        self.preds = open(self.dir / "predictions.csv", "w")
        self.preds.write("t_s,prediction\n")
        self.n = 0

    def write_samples(self, values, labels) -> None:
        for v, lab in zip(values, labels):
            self.signal.write(f"{self.n / config.FS:.3f},{int(v)},{int(lab)}\n")
            self.n += 1

    def write_prediction(self, t_s: float, pred: int) -> None:
        self.preds.write(f"{t_s:.3f},{pred}\n")

    def close(self) -> None:
        self.signal.close()
        self.preds.close()


def load_sample(sample_dir: Path) -> tuple[pd.DataFrame, dict]:
    sample_dir = Path(sample_dir)
    meta = json.loads((sample_dir / "metadata.json").read_text())
    return pd.read_csv(sample_dir / "signal.csv"), meta


def list_samples(root: Path = config.DATA_RAW) -> list[Path]:
    return sorted(p for p in Path(root).glob("*") if (p / "signal.csv").exists())


def last_metadata(root: Path = config.DATA_RAW) -> dict:
    """Metadata of the newest sample (used to pre-fill the form), or {}."""
    samples = list_samples(root)
    return json.loads((samples[-1] / "metadata.json").read_text()) if samples else {}


class AzureUploader:
    """Background uploader. If there is no connection string or Azure fails, it only logs."""

    def __init__(self, metadata: dict, conn_str: str | None = None):
        self.meta = metadata
        # conn_str="" means "offline on purpose", None means "take it from .env"
        self.conn_str = conn_str if conn_str is not None else os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.q: queue.Queue = queue.Queue()
        self.enabled = bool(self.conn_str)
        if not self.enabled:
            log.warning("No AZURE_STORAGE_CONNECTION_STRING - running offline (data is saved locally).")
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def send(self, seq: int, t0_s: float, samples, predictions) -> None:
        """Queue one chunk. Never blocks, never raises."""
        if self.enabled:
            self.q.put((seq, t0_s, list(samples), list(predictions)))

    def close(self, timeout: float = 10) -> None:
        if self.enabled:
            self.q.put(None)
            self.thread.join(timeout)

    def _run(self) -> None:
        try:
            blobs, samples, preds = _clients(self.conn_str)
            sid = self.meta["sample_id"]
            blobs.upload_blob(f"{sid}/metadata.json", json.dumps(self.meta), overwrite=True)
            samples.upsert_entity({"PartitionKey": "sample", "RowKey": sid, **self.meta})
        except Exception as e:  # no internet, wrong key, ... -> stay offline
            log.error("Azure setup failed, continuing offline: %s", e)
            self.enabled = False
            return
        while (item := self.q.get()) is not None:
            seq, t0, values, labels = item
            try:
                blobs.upload_blob(f"{sid}/{seq:06d}.csv", "\n".join(str(int(v)) for v in values),
                                  overwrite=True)
                preds.upsert_entity({
                    "PartitionKey": sid, "RowKey": f"{seq:06d}", "t0_s": t0, "n": len(values),
                    "contract_ratio": sum(labels) / max(len(labels), 1),
                    "labels": "".join(str(int(p)) for p in labels),
                })
            except Exception as e:
                log.error("Upload of chunk %d failed (kept locally): %s", seq, e)


def _clients(conn_str: str):
    from azure.data.tables import TableServiceClient
    from azure.storage.blob import BlobServiceClient

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container = blob_service.get_container_client(config.BLOB_CONTAINER)
    if not container.exists():
        container.create_container()
    tables = TableServiceClient.from_connection_string(conn_str)
    return (container,
            tables.create_table_if_not_exists(config.TABLE_SAMPLES),
            tables.create_table_if_not_exists(config.TABLE_PREDICTIONS))


def delete_sample(sample_id: str, root: Path = config.DATA_RAW, conn_str: str | None = None,
                  clients=None) -> dict:
    """Deletes one sample everywhere (privacy: right to withdraw, see docs/privacy.md).

    Local folder root/<sample_id>, blobs signals/<sample_id>/*, the `samples` row and all `predictions`
    rows of that sample. Returns counts. Git history is NOT touched (see docs/privacy.md).
    """
    if not SAMPLE_RE.match(sample_id):
        raise ValueError("sample_id must look like sample_001")
    import shutil
    done = {"local": 0, "blobs": 0, "sample_rows": 0, "prediction_rows": 0}
    local = Path(root) / sample_id
    if local.is_dir():
        shutil.rmtree(local)
        done["local"] = 1
    conn_str = conn_str if conn_str is not None else os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if clients is None:
        if not conn_str:
            log.warning("No AZURE_STORAGE_CONNECTION_STRING - deleted locally only.")
            return done
        clients = _clients(conn_str)
    blobs, samples, preds = clients
    for b in list(blobs.list_blobs(name_starts_with=f"{sample_id}/")):
        blobs.delete_blob(b.name)
        done["blobs"] += 1
    for e in list(samples.query_entities(f"RowKey eq '{sample_id}'")):
        samples.delete_entity(e["PartitionKey"], e["RowKey"])
        done["sample_rows"] += 1
    for e in list(preds.query_entities(f"PartitionKey eq '{sample_id}'")):
        preds.delete_entity(e["PartitionKey"], e["RowKey"])
        done["prediction_rows"] += 1
    return done


def upload_sample(sample_dir: Path, conn_str: str | None = None) -> None:
    """Upload a finished local sample afterwards (e.g. it was recorded offline)."""
    df, meta = load_sample(sample_dir)
    preds = pd.read_csv(Path(sample_dir) / "predictions.csv")
    up = AzureUploader(meta, conn_str)
    if not up.enabled:
        raise RuntimeError("No AZURE_STORAGE_CONNECTION_STRING set")
    chunk = int(config.UPLOAD_EVERY_S * config.FS)
    for seq, start in enumerate(range(0, len(df), chunk)):
        t0, t1 = start / config.FS, (start + chunk) / config.FS
        p = preds[(preds.t_s >= t0) & (preds.t_s < t1)].prediction
        up.send(seq, t0, df.value.iloc[start:start + chunk], p)
    up.close(timeout=300)

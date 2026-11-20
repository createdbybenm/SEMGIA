import numpy as np
import pandas as pd

from semgia import config
from semgia.recorder import SAMPLE_N, label_at
from semgia.report import (
    COURSE_COLUMNS,
    OWN_COLUMNS,
    check_signal,
    metadata_row,
    metadata_table,
    quality_markdown,
    quality_table,
    split_of,
)
from semgia.storage import LocalWriter, make_metadata

IDS = dict(subject_id="P001", operator_id="OP01", placement_id="E01")


def good_df(n: int = SAMPLE_N) -> pd.DataFrame:
    """A clean fake signal: mid-scale noise, never at the ADC limit, no gaps."""
    rng = np.random.default_rng(0)
    idx = np.arange(n)
    values = 512 + rng.integers(-20, 20, n)
    return pd.DataFrame({"t_s": idx / config.FS, "value": values, "label": label_at(idx)})


def test_good_signal_passes():
    assert check_signal(good_df()) == ""


def test_adc_limit_is_rejected():
    df = good_df()
    df.loc[100, "value"] = 2 ** config.ADC_BITS - 1
    df.loc[200, "value"] = 0
    assert "ADC limit" in check_signal(df)


def test_nan_is_rejected():
    df = good_df().astype({"value": float})
    df.loc[5, "value"] = np.nan
    assert "NaN" in check_signal(df)


def test_missing_rows_are_rejected():
    df = good_df().drop(index=range(1000, 1010)).reset_index(drop=True)
    assert "gaps" in check_signal(df)


def test_length_tolerance_is_2_percent():
    assert check_signal(good_df(int(SAMPLE_N * 0.99))) == ""      # 1 % short -> ok
    assert "length" in check_signal(good_df(int(SAMPLE_N * 0.97)))  # 3 % short -> rejected


def test_split_uses_test_placements(monkeypatch):
    monkeypatch.setattr(config, "TEST_PLACEMENTS", ["E05"])
    assert split_of("E05") == "test"
    assert split_of("E01") == "train"


def test_metadata_row_has_course_columns(tmp_path):
    meta = make_metadata(root=tmp_path, **IDS)
    row = metadata_row(meta, "data/raw/sample_001/signal.csv")
    assert all(c in row for c in COURSE_COLUMNS)
    assert len(set(row)) == len(row) == len(COURSE_COLUMNS) + 1 + len(OWN_COLUMNS)
    assert (row["session"], row["rest_s"], row["move_s"], row["between_s"]) == ("E01", 8, 8, 8)
    assert row["date"] == meta["start_time_utc"][:10]
    assert row["set"] == "train"


def write_sample(root, values) -> None:
    w = LocalWriter(make_metadata(root=root, **IDS), root)
    w.write_samples(values, label_at(np.arange(len(values))))
    w.close()


def test_tables_one_row_per_sample(tmp_path):
    write_sample(tmp_path, np.full(SAMPLE_N, 512))
    write_sample(tmp_path, np.full(SAMPLE_N, 1023))          # clipped -> rejected
    meta = metadata_table(tmp_path)
    assert list(meta.sample_id) == ["sample_001", "sample_002"]
    assert meta.file_name.iloc[0].endswith("sample_001/signal.csv")
    q = quality_table(tmp_path)
    assert list(q.verdict) == ["ok", "rejected"]
    md = quality_markdown(q)
    assert "Rejection rule" in md and "| sample_002 | E01 | 24000 | rejected |" in md

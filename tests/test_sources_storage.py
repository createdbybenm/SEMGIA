import json
import time

import numpy as np
import pandas as pd
import pytest

from semgia import config
from semgia.model import ThresholdModel
from semgia.recorder import SAMPLE_N, LivePredictor, SampleRecorder
from semgia.sources import MockSource
from semgia.storage import AzureUploader, LocalWriter, load_sample, make_metadata, next_sample_id

IDS = dict(subject_id="P001", operator_id="OP01", placement_id="E01")


def test_mock_source_reacts_to_cue():
    src = MockSource(seed=0)
    rest = src.generate(1000)
    src.set_cue(config.CONTRACT)
    contract = src.generate(1000)
    assert contract.std() > 3 * rest.std()


def test_mock_source_real_time_read():
    src = MockSource()
    time.sleep(0.05)
    assert 30 <= len(src.read()) <= 200


@pytest.mark.parametrize("field,bad", [("subject_id", "Max Mustermann"), ("subject_id", "p001"),
                                       ("operator_id", "Anna"), ("placement_id", "1"), ("subject_id", "")])
def test_metadata_rejects_names_and_bad_ids(tmp_path, field, bad):
    with pytest.raises(ValueError):
        make_metadata(root=tmp_path, **{**IDS, field: bad})


def test_metadata_rejects_unknown_fields(tmp_path):
    with pytest.raises(ValueError):
        make_metadata(root=tmp_path, name="Max", **IDS)


def test_sample_ids_count_up(tmp_path):
    assert next_sample_id(tmp_path) == "sample_001"
    (tmp_path / "sample_001").mkdir()
    (tmp_path / "sample_009").mkdir()
    assert next_sample_id(tmp_path) == "sample_010"


def test_local_writer_roundtrip(tmp_path):
    meta = make_metadata(root=tmp_path, muscle="biceps brachii", **IDS)
    w = LocalWriter(meta, tmp_path)
    w.write_samples([500, 510], [0, 1])
    w.close()
    df, meta2 = load_sample(w.dir)
    assert list(df.columns) == ["t_s", "value", "label"]
    assert list(df.value) == [500, 510] and list(df.label) == [0, 1]
    assert meta2 == meta and w.dir.name == "sample_001"
    assert json.loads((w.dir / "metadata.json").read_text())["placement_id"] == "E01"


def test_recorder_records_exactly_one_labelled_sample(tmp_path):
    """Feed 30 s of mock data in uneven chunks: sample = exactly 24 s, labels from the counter."""
    src, pred = MockSource(seed=3), LivePredictor(ThresholdModel())
    pred.push(src.generate(1234))                        # some idle data before the button press
    rec = SampleRecorder(make_metadata(root=tmp_path, **IDS), pred.total, tmp_path)
    for n in np.random.default_rng(0).integers(20, 120, size=1000):
        if rec.done:
            break
        src.set_cue(rec.cue()[0])
        x = src.generate(int(n))
        rec.push(x, pred.push(x))
        if rec.calib is not None:
            pred.calib = rec.calib
    rec.close()
    assert rec.done and rec.calib is not None
    df = pd.read_csv(rec.writer.dir / "signal.csv")
    assert len(df) == SAMPLE_N
    assert df.label.tolist() == [0] * 8000 + [1] * 8000 + [0] * 8000
    p = pd.read_csv(rec.writer.dir / "predictions.csv")
    assert p.t_s.min() >= 8.0                             # predictions start after the rest baseline
    contract = p[(p.t_s > 9.5) & (p.t_s < 15.5)].prediction
    rest = p[p.t_s > 18].prediction
    assert contract.mean() > 0.9 and rest.mean() < 0.1


def test_uploader_offline_never_raises(tmp_path):
    up = AzureUploader(make_metadata(root=tmp_path, **IDS), conn_str="")
    assert not up.enabled
    up.send(0, 0.0, [1, 2, 3], [0])
    up.close()


def test_uploader_bad_connection_string_never_raises(tmp_path):
    up = AzureUploader(make_metadata(root=tmp_path, **IDS), conn_str="garbage")
    up.send(0, 0.0, [1, 2, 3], [0])
    up.close(timeout=5)
    assert not up.enabled


# --- files downloaded by the web interface (scripts/import_web.py) ---
def web_sample(**meta):
    m = dict(IDS, muscle="biceps brachii", side="right", sensor_id="DFRobot-SEN0240",
             electrode_type="dry (built-in)",
             effort="light", condition="fresh", sampling_rate_hz=1000,
             start_time_utc="2026-11-20T10:00:00+00:00", notes="", placement_notes="")
    m.update(meta)
    src = MockSource(seed=5)                       # what the ESP32 would stream: rest / contract / rest
    parts = []
    for cue in (config.REST, config.CONTRACT, config.REST):
        src.set_cue(cue)
        parts.append(src.generate(SAMPLE_N // 3))
    return {"format": "semgia-sample-1", "metadata": m, "values": np.concatenate(parts).astype(int).tolist()}


def test_web_sample_becomes_a_normal_sample(tmp_path):
    from semgia.recorder import save_web_sample
    d = save_web_sample(web_sample(), tmp_path)
    df, meta = load_sample(d)
    assert d.name == "sample_001" and meta["sample_id"] == "sample_001"
    assert list(df.columns) == ["t_s", "value", "label"] and len(df) == SAMPLE_N
    assert df.label.tolist() == [0] * 8000 + [1] * 8000 + [0] * 8000   # labels from the timer, not the file
    assert meta["start_time_utc"] == "2026-11-20T10:00:00+00:00"
    p = pd.read_csv(d / "predictions.csv")                              # same live pipeline as record.py
    assert p.t_s.min() >= 8.0
    assert p[(p.t_s > 9.5) & (p.t_s < 15.5)].prediction.mean() > 0.9 and p[p.t_s > 18].prediction.mean() < 0.1
    assert save_web_sample(web_sample(), tmp_path) is None             # importing twice is a no-op
    second = save_web_sample(web_sample(start_time_utc="2026-11-20T10:01:00+00:00"), tmp_path)
    assert second.name == "sample_002"


@pytest.mark.parametrize("bad", [dict(subject_id="Max Mustermann"), dict(effort="hard"),
                                 dict(sampling_rate_hz=500), dict(name="Max")])
def test_web_sample_rejects_bad_metadata(tmp_path, bad):
    from semgia.recorder import save_web_sample
    with pytest.raises(ValueError):
        save_web_sample(web_sample(**bad), tmp_path)
    assert not list(tmp_path.iterdir())


def test_web_sample_rejects_incomplete_recording(tmp_path):
    from semgia.recorder import save_web_sample
    p = web_sample()
    p["values"] = p["values"][:SAMPLE_N - 1]
    with pytest.raises(ValueError):
        save_web_sample(p, tmp_path)


def test_web_sample_rejects_values_that_are_not_adc_counts(tmp_path):
    """Offset-removed mV (negative values) would be flagged as clipping by the quality check."""
    from semgia.recorder import save_web_sample
    p = web_sample()
    p["values"] = [v - 2048 for v in p["values"]]
    with pytest.raises(ValueError):
        save_web_sample(p, tmp_path)


def test_web_sample_passes_the_quality_check(tmp_path):
    from semgia.recorder import save_web_sample
    from semgia.report import check_signal
    df, _ = load_sample(save_web_sample(web_sample(), tmp_path))
    assert check_signal(df) == ""


def test_web_calibration_is_saved_per_placement_and_not_a_sample(tmp_path):
    from semgia.recorder import save_web_calibration
    from semgia.storage import list_samples
    cal = {"format": "semgia-calib-1", "placement_id": "E01", "subject_id": "P001", "operator_id": "OP01",
           "start_time_utc": "2026-11-20T09:55:00+00:00", "sampling_rate_hz": 1000, "rest_mV": 4.2,
           "max_mV": 180.5, "values": [1, -2, 3], "steps": [0, 1, 2]}
    d = save_web_calibration(cal, tmp_path)
    assert d.name == "calibration_E01"
    assert json.loads((d / "calibration.json").read_text())["max_mV"] == 180.5
    assert pd.read_csv(d / "calibration.csv").step.tolist() == [0, 1, 2]
    assert list_samples(tmp_path) == [] and next_sample_id(tmp_path) == "sample_001"
    assert save_web_calibration(cal, tmp_path) is None                  # same file again: skipped
    with pytest.raises(ValueError):                                     # a different one: refused
        save_web_calibration({**cal, "start_time_utc": "2026-11-20T11:00:00+00:00"}, tmp_path)
    with pytest.raises(ValueError):
        save_web_calibration({**cal, "placement_id": "E02", "subject_id": "Anna"}, tmp_path)


def test_file_source_rewind_restarts_the_replay(tmp_path):
    """Demo fallback: 'Collect sample' rewinds the file, so the cues match the recorded phases."""
    from semgia.sources import FileSource
    csv = tmp_path / "signal.csv"
    pd.DataFrame({"t_s": [0, 0.001, 0.002], "value": [10, 20, 30], "label": 0}).to_csv(csv, index=False)
    src = FileSource(csv)
    time.sleep(0.01)
    assert len(src.read()) > 0 and src.pos > 0
    src.rewind()
    assert src.pos == 0
    time.sleep(0.002)
    assert src.read()[0] == 10                          # starts at the first value again

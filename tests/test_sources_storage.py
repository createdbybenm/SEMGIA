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

"""Import the files downloaded by the web interface (ESP32 page) into data/raw/.

The page downloads one file per sample (semgia_sample_*.json) and per calibration (semgia_calib_*.json).
This turns them into data/raw/sample_NNN/ and data/raw/calibration_EXX/. Safe to run again:
files that were already imported are skipped. Files are imported in recording order.

    python scripts/import_web.py                         # looks in your Downloads folder
    python scripts/import_web.py C:/Users/me/Downloads/semgia_sample_E01_20261120T101500Z.json
    python scripts/import_web.py some/folder --out data/raw
    python scripts/import_web.py --upload                # also send new samples to Azure (needs .env)

Each sample is replayed through the same pipeline as record.py, so it also gets predictions.csv.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.recorder import save_web_calibration, save_web_sample  # noqa: E402


def find_files(paths: list[str]) -> list[Path]:
    files = []
    for p in map(Path, paths):
        files += sorted(p.glob("semgia_*.json")) if p.is_dir() else [p]
    return files


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="*", default=[str(Path.home() / "Downloads")],
                   help="files or folders (default: ~/Downloads)")
    p.add_argument("--out", default=str(config.DATA_RAW), help="where samples are saved")
    p.add_argument("--upload", action="store_true", help="also upload new samples to Azure (best effort)")
    a = p.parse_args()
    # without --upload, "running offline" is intended -> only show real errors
    logging.basicConfig(level=logging.INFO if a.upload else logging.ERROR, format="%(levelname)s %(message)s")
    load_dotenv()

    loaded, errors = [], 0
    for f in find_files(a.paths):
        try:
            loaded.append((f, json.loads(f.read_text(encoding="utf-8"))))
        except (OSError, ValueError) as e:
            print(f"ERROR {f.name}: cannot read ({e})")
            errors += 1
    # calibrations first, then samples, each in recording order -> sample numbers follow the recording
    def order(fp):
        payload = fp[1]
        start = payload.get("start_time_utc") or payload.get("metadata", {}).get("start_time_utc", "")
        return payload.get("format") != "semgia-calib-1", start

    loaded.sort(key=order)

    new = 0
    for f, payload in loaded:
        try:
            if payload.get("format") == "semgia-calib-1":
                out = save_web_calibration(payload, Path(a.out))
            else:
                out = save_web_sample(payload, Path(a.out), upload=a.upload)
        except (ValueError, KeyError) as e:
            print(f"ERROR {f.name}: {e}")
            errors += 1
            continue
        if out is None:
            print(f"skip  {f.name} (already imported)")
        else:
            print(f"ok    {f.name} -> {out}")
            new += 1
    print(f"{new} imported, {errors} errors, {len(loaded)} files checked.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

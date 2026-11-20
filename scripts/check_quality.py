"""Check every recording against the rejection rule and write QUALITY-REPORT.md.

    python scripts/check_quality.py                                    # data/raw -> QUALITY-REPORT.md
    python scripts/check_quality.py --data data/synthetic --out /tmp/QUALITY-REPORT.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.report import quality_markdown, quality_table  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(config.DATA_RAW))
    p.add_argument("--out", default=str(config.ROOT / "QUALITY-REPORT.md"))
    a = p.parse_args()
    table = quality_table(Path(a.data))
    if table.empty:
        sys.exit(f"No samples found in {a.data}")
    Path(a.out).write_text(quality_markdown(table))
    bad = table[table.verdict == "rejected"]
    print(f"{len(table)} recordings, {len(bad)} rejected -> {a.out}")
    for r in bad.itertuples():
        print(f"  {r.sample}: {r.reason}")


if __name__ == "__main__":
    main()

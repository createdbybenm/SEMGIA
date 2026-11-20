"""Write data/metadata.csv: one row per recording (course columns, file_name, then our metadata fields).

    python scripts/export_metadata.py                                  # data/raw -> data/metadata.csv
    python scripts/export_metadata.py --data data/synthetic --out /tmp/metadata.csv
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia import config  # noqa: E402
from semgia.report import metadata_table  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(config.DATA_RAW))
    p.add_argument("--out", default=str(config.ROOT / "data" / "metadata.csv"))
    a = p.parse_args()
    table = metadata_table(Path(a.data))
    if table.empty:
        sys.exit(f"No samples found in {a.data}")
    table.to_csv(a.out, index=False)
    print(f"{len(table)} rows ({table['set'].value_counts().to_dict()}) -> {a.out}")


if __name__ == "__main__":
    main()

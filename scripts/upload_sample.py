"""Upload locally recorded samples to Azure afterwards (e.g. they were recorded offline).

    python scripts/upload_sample.py data/raw/sample_007 data/raw/sample_008
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia.storage import upload_sample  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("sample_dirs", nargs="+")
    a = p.parse_args()
    load_dotenv()
    for d in a.sample_dirs:
        upload_sample(Path(d))
        print("uploaded", d)


if __name__ == "__main__":
    main()

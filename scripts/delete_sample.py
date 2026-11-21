"""Delete samples everywhere: data/raw/<id>/ and Azure (blobs + table rows). Privacy: right to withdraw.

    python scripts/delete_sample.py sample_007 sample_008          # asks for confirmation
    python scripts/delete_sample.py sample_007 --yes

Without AZURE_STORAGE_CONNECTION_STRING in .env it deletes locally only. The sample stays in the Git history
(see docs/privacy.md); remove it from the repo with a PR as well.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from semgia.storage import delete_sample  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("sample_ids", nargs="+", help="e.g. sample_007")
    p.add_argument("--yes", action="store_true", help="don't ask for confirmation")
    a = p.parse_args()
    load_dotenv()
    if not a.yes and input(f"Delete {', '.join(a.sample_ids)} locally AND in Azure? [y/N] ").lower() != "y":
        sys.exit("cancelled")
    for sid in a.sample_ids:
        print(sid, delete_sample(sid))


if __name__ == "__main__":
    main()

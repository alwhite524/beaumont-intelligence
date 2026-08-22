"""Publish the Beaumont Intelligence PD Technology article to the MBF site."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "police" / "pd-technology.html"
OUTPUT = ROOT / "docs" / "dossiers" / "police" / "flock-cameras.html"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish the canonical PD Technology article without changing its MBF design."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the published MBF article differs from the Beaumont Intelligence source.",
    )
    args = parser.parse_args()

    if not SOURCE.is_file():
        print(f"Missing canonical source: {SOURCE.relative_to(ROOT)}", file=sys.stderr)
        return 1

    source_bytes = SOURCE.read_bytes()
    published_bytes = OUTPUT.read_bytes() if OUTPUT.is_file() else None

    if args.check:
        if published_bytes != source_bytes:
            print(
                f"Out of date: {OUTPUT.relative_to(ROOT)}; run "
                f"'{sys.executable} scripts/publish_pd_technology.py'.",
                file=sys.stderr,
            )
            return 1
        print("PD Technology MBF article matches its Beaumont Intelligence source.")
        return 0

    if published_bytes == source_bytes:
        print("PD Technology MBF article is already current.")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(source_bytes)
    print(f"Published {SOURCE.relative_to(ROOT)} -> {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

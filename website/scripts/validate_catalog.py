from pathlib import Path
import csv
from urllib.parse import urlparse

root = Path(__file__).resolve().parents[1]
catalog = root / "data" / "stewart-park" / "source-catalog.csv"
errors, seen = [], set()

with catalog.open(encoding="utf-8") as f:
    for row_no, row in enumerate(csv.DictReader(f), start=2):
        code = row["archive_code"].strip()
        if not code:
            errors.append(f"Row {row_no}: missing archive_code")
        elif code in seen:
            errors.append(f"Row {row_no}: duplicate archive_code {code}")
        seen.add(code)

        parsed = urlparse(row["url"].strip())
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"Row {row_no}: invalid HTTPS URL")

        if row["evidence"] not in {"A","B","C","D"}:
            errors.append(f"Row {row_no}: invalid evidence level")

        if row["status"] not in {"unreviewed","reviewed","verified","disputed","superseded"}:
            errors.append(f"Row {row_no}: invalid status")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)

print(f"Validated {len(seen)} source records.")

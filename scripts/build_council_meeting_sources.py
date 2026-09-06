"""Build the Council meeting video and agenda-packet source index."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def meeting_records() -> list[dict[str, str | None]]:
    meetings: dict[str, dict[str, str | None]] = {}
    for transcript in sorted((DOCS / "transcripts").glob("*-city-council-transcript.txt")):
        date = transcript.name[:10]
        header = transcript.read_text(encoding="utf-8", errors="replace")[:1500]
        video = re.search(r"https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]+", header)
        if not video:
            continue
        if date == "2021-06-21" and "June 1, 2021" in header:
            date = "2021-06-01"
        meetings.setdefault(date, {"date": date, "video": None, "packet": None})["video"] = video.group(0)

    manifest = json.loads((ROOT / "data" / "document-storage-manifest.json").read_text(encoding="utf-8"))
    candidates: dict[str, list[dict]] = {}
    for document in manifest["documents"]:
        path = document["path"]
        match = re.search(r"(\d{4}-\d{2}-\d{2}).*agenda-(?:package|packet).*\.pdf$", path, re.I)
        if match:
            candidates.setdefault(match.group(1), []).append(document)
    for date, documents in candidates.items():
        preferred = sorted(documents, key=lambda item: ("records/agenda-packets" not in item["path"], item["path"]))[0]
        meetings.setdefault(date, {"date": date, "video": None, "packet": None})["packet"] = preferred["url"]

    return sorted(meetings.values(), key=lambda item: item["date"], reverse=True)


def main() -> None:
    records = meeting_records()
    output = DOCS / "council-meeting-sources.js"
    output.write_text(
        "window.BI_COUNCIL_MEETING_SOURCES=" + json.dumps(records, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Council meeting sources: {len(records)} meetings")


if __name__ == "__main__":
    main()

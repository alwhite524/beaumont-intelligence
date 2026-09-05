"""Build the browser-side Research Library index from archived and City-hosted records."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def title_from_path(path: str) -> str:
    name = Path(path).stem
    name = re.sub(r"^(g|i|j)-\d+-", "", name, flags=re.I)
    return " ".join(word.upper() if word in {"cip", "cfd", "rctc", "ots", "eir", "mou"} else word.title()
                    for word in name.replace("_", "-").split("-") if word)


def agenda_item(path: str) -> str:
    match = re.search(r"/(g|i|j)-(\d+)-", path, re.I)
    return f"{match.group(1).upper()}.{match.group(2)}" if match else ""


def topic_for(text: str) -> str:
    value = text.lower()
    rules = [
        ("parks", ("park", "recreation", "beaumont nights")),
        ("transportation", ("street", "traffic", "interchange", "pennsylvania", "vehicle", "bike", "transport")),
        ("utilities", ("wastewater", "sewer", "solid waste", "water master")),
        ("environment", ("sustainability", "climate", "eir", "environment")),
        ("money", ("budget", "finance", "bond", "grant", "economic", "cfd", "sponsorship", "warrant", "accounts receivable")),
        ("growth", ("billboard", "planning", "development", "agreement", "short-term rental")),
        ("public-safety", ("police", "flock", "axon", "traffic safety", "animal control")),
    ]
    return next((topic for topic, words in rules if any(word in value for word in words)), "government")


records: list[dict] = []
manifest = json.loads((ROOT / "data" / "document-storage-manifest.json").read_text(encoding="utf-8"))
for doc in manifest["documents"]:
    path = doc["path"]
    parts = path.split("/")
    date = parts[1] if len(parts) > 2 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[1]) else ""
    if date == "2026-09-01":
        continue  # The official source inventory below is complete and avoids duplicate results.
    title = title_from_path(path)
    records.append({"title": title, "url": doc["url"], "date": date, "item": agenda_item(path),
                    "topic": topic_for(title), "type": "Archived document", "body": title})

source_text = (DOCS / "briefings" / "2026-09-01-sources.js").read_text(encoding="utf-8")
for item, section, title, doc_id in re.findall(r"\['([^']+)','([^']+)','([^']+)',(\d+)\]", source_text):
    records.append({"title": title, "url": f"https://pub-beaumont.escribemeetings.com/filestream.ashx?DocumentId={doc_id}",
                    "date": "2026-09-01", "item": item, "topic": topic_for(title),
                    "type": "Official City document", "body": f"{item} {section} {title}"})

for transcript in sorted((DOCS / "transcripts").glob("*-city-council-transcript.txt"), reverse=True):
    date = transcript.name[:10]
    body = transcript.read_text(encoding="utf-8", errors="replace")
    video_match = re.search(r"https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]+", body[:1000])
    records.append({"title": f"{date} City Council transcript", "url": f"../transcripts/{transcript.name}",
                    "videoUrl": video_match.group(0) if video_match else "", "date": date, "item": "",
                    "topic": "council", "type": "Meeting transcript", "body": body})

output = "window.BI_RESEARCH_LIBRARY=" + json.dumps(records, ensure_ascii=False, separators=(",", ":")) + ";\n"
(DOCS / "documents" / "library-index.js").write_text(output, encoding="utf-8")
print(f"Research Library index: {len(records)} records")

"""Build the Council meeting video and agenda-packet source index."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def meeting_records() -> list[dict[str, str | None]]:
    meetings: dict[str, dict[str, str | None]] = {}
    for transcript in sorted((DOCS / "transcripts").glob("*-city-council-transcript.txt")):
        date = transcript.name[:10]
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            continue
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

    # Include standalone agendas and minutes without calling them full packets.
    for document in manifest['documents']:
        if document.get('publication_status') == 'pending-upload':
            continue
        match = re.fullmatch(r'official-documents/(\d{4}-\d{2}-\d{2})/(agenda|special-meeting-minutes|council-minutes|workshop-minutes)\.pdf', document['path'])
        if match:
            date, kind = match.groups()
            record = meetings.setdefault(date, {'date': date, 'video': None, 'packet': None})
            if kind == 'agenda':
                record['agenda'] = document['url']
            elif kind == 'council-minutes':
                record['minutes'] = document['url']
            else:
                title = 'Special meeting minutes' if kind == 'special-meeting-minutes' else 'Workshop minutes'
                record.setdefault('documents', []).append({'title': title, 'url': document['url']})
    register = json.loads((ROOT / 'data/budget/source-register.json').read_text(encoding='utf-8'))
    for source in register['sources']:
        date = source.get('councilMeetingDate')
        if not date or 'wrcog-restitution' not in source.get('relatedCenters', []):
            continue
        record = meetings.setdefault(date, {'date': date, 'video': None, 'packet': None})
        url = source.get('archivePath') or source.get('officialUrl')
        if source['documentType'] == 'Council Agenda' and not record.get('packet'):
            record.setdefault('agenda', url)
        if source['documentType'] == 'Council Minutes' and url not in [d['url'] for d in record.get('documents', [])]:
            record.setdefault('minutes', url)
        if source['sourceId'] in ('SRC-0035', 'SRC-0036'):
            record.setdefault('documents', []).append({'title': 'Settlement agreement and attachments', 'url': url})

    # Dates in this catalog describe the meeting recorded, not the approving agenda.
    minutes = json.loads((ROOT / 'data/council/minutes-register.json').read_text(encoding='utf-8'))['documents']
    for minute in minutes:
        date = minute['date']
        if not date:
            continue
        record = meetings.setdefault(date, {'date': date, 'video': None, 'packet': None})
        existing = [d['url'] for d in record.get('documents', [])] + [record.get('minutes')]
        if minute['url'] in existing:
            continue
        if minute['kind'] == 'regular' and not minute['url'].lower().endswith('.docx') and not record.get('minutes'):
            record['minutes'] = minute['url']
        else:
            record.setdefault('documents', []).append({'title': minute['title'], 'url': minute['url']})

    meetings.setdefault('2015-11-03', {'date': '2015-11-03', 'video': 'https://www.youtube.com/watch?v=mokmwjT4ujs', 'packet': None})
    return sorted(meetings.values(), key=lambda item: item["date"], reverse=True)


def main() -> None:
    records = meeting_records()
    output = DOCS / "council-meeting-sources.js"
    output.write_text(
        "window.BI_COUNCIL_MEETING_SOURCES=" + json.dumps(records, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
        newline="\n",
    )
    compilations = [d for d in json.loads((ROOT / 'data/document-storage-manifest.json').read_text())['documents'] if re.fullmatch(r'official-documents/20\d{2}/20\d{2}-council-minutes\.pdf', d['path'])]
    with output.open('a', encoding='utf-8') as stream:
        stream.write('window.BI_COUNCIL_MINUTES_COMPILATIONS=' + json.dumps([{'year': d['path'].split('/')[1], 'url': d['url']} for d in compilations]) + ';\n')
    print(f"Council meeting sources: {len(records)} meetings")


if __name__ == "__main__":
    main()

"""Split bookmarked eSCRIBE agenda packages into viewer-ready source PDFs."""
from __future__ import annotations

import re
import shutil
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"
OUTPUT = ROOT / "docs" / "official-documents"
PACKETS = ROOT / "docs" / "records" / "agenda-packets"

MEETINGS = {
    "Apr07_2026": "2026-04-07",
    "Apr21_2026": "2026-04-21",
    "May05_2026": "2026-05-05",
    "Jun02_2026": "2026-06-02",
    "Jun16_2026": "2026-06-16",
    "Jul21_2026": "2026-07-21",
    "Aug18_2026": "2026-08-18",
    "Sep01_2026": "2026-09-01",
}

SOURCE_VARS = {
    "2026-04-07": "BI_APRIL_7_SOURCES",
    "2026-04-21": "BI_APRIL_21_SOURCES",
}


def slug(value: str) -> str:
    value = value.removesuffix(".pdf").lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:180]


def destinations(reader: PdfReader) -> list[tuple[int, str]]:
    result = []
    for entry in reader.outline or []:
        if isinstance(entry, list):
            continue
        try:
            result.append((reader.get_destination_page_number(entry), entry.title))
        except (AttributeError, ValueError):
            continue
    return result


def main() -> None:
    total = 0
    for token, date in MEETINGS.items():
        source = DOWNLOADS / f"Agenda Package - City Council Closed and Regular Session_{token}.pdf"
        if not source.exists():
            raise FileNotFoundError(source)

        packet_dir = PACKETS / date
        packet_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, packet_dir / f"{date}-city-council-agenda-package.pdf")

        reader = PdfReader(str(source))
        marks = destinations(reader)
        target_dir = OUTPUT / date
        target_dir.mkdir(parents=True, exist_ok=True)
        used: set[str] = set()
        source_records: list[dict[str, str]] = []

        for index, (start, title) in enumerate(marks):
            end = marks[index + 1][0] if index + 1 < len(marks) else len(reader.pages)
            if end <= start:
                continue
            filename = f"{slug(title)}.pdf"
            if filename in used:
                filename = f"{slug(title)}-{index + 1}.pdf"
            used.add(filename)
            writer = PdfWriter()
            for page_index in range(start, end):
                writer.add_page(reader.pages[page_index])
            with (target_dir / filename).open("wb") as stream:
                writer.write(stream)
            match = re.match(r"^([GIJ]\.\d+)\.\s*(.+)\.pdf$", title, re.IGNORECASE)
            if match and date in SOURCE_VARS:
                item, document_title = match.groups()
                section = {"G": "Consent", "I": "Public Hearing", "J": "Action"}[item[0].upper()]
                archive_name = filename
                if date == "2026-04-07" and item.upper() == "J.9" and document_title.lower().startswith("staff report"):
                    archive_name = "j-9-staff-report-drone-as-first-responder.pdf"
                source_records.append({
                    "item": item.upper(),
                    "section": section,
                    "title": document_title,
                    "archiveUrl": f"https://documents.beaumontintelligence.com/official-documents/{date}/{archive_name}",
                })
            total += 1

        if date in SOURCE_VARS:
            output_js = ROOT / "docs" / "briefings" / f"{date}-sources.js"
            output_js.write_text(
                f"window.{SOURCE_VARS[date]}=" + json.dumps(source_records, ensure_ascii=False, separators=(",", ":")) + ";\n",
                encoding="utf-8",
            )

        print(f"{date}: packet plus {len(used)} viewer documents")
    print(f"Created {total} viewer documents from {len(MEETINGS)} agenda packages")


if __name__ == "__main__":
    main()

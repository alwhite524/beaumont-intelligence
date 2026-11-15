"""Build searchable Council agendas from supplied packets and archived minutes."""

import argparse
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PACKETS = {"2023-06-06": "Jun06_2023", "2024-08-20": "Aug20_2024", "2025-02-04": "Feb04_2025"}
HISTORICAL = ("2015-11-17", "2017-05-16", "2018-06-19", "2018-07-03")
SECTIONS = {"B": "Closed session", "G": "Consent calendar", "I": "Public hearings", "J": "Action items"}
BUDGET_TITLES = {
    ("2023-06-06", "I.1"): "FY 2023–24 budget and FY 2024–28 Capital Improvement Plan adoption",
    ("2024-08-20", "I.3"): "First amendment to the FY 2025–29 Capital Improvement Plan",
    ("2025-02-04", "I.2"): "Third amendment to the FY 2025–29 Capital Improvement Plan",
}
HISTORICAL_ITEMS = {
    "2015-11-17": [
        ("4.a", "Planning Commission appointment", 206),
        ("4.b", "Title 22 ultraviolet validation purchase order", 207),
        ("4.c", "Community clean-up event", 207),
        ("4.d", "City Attorney invoices", 208),
    ],
    "2017-05-16": [
        ("Workshop 1", "CFD and Mello-Roos workshop recap", 75),
        ("Workshop 2", "FY 2017–18 budget review", 75),
        ("3", "Amended WRCOG settlement agreement", 77),
        ("20", "FY 2017–18 annual budget adoption", 80),
        ("21", "Potrero Interchange gap funding agreements", 81),
        ("22", "Wastewater treatment plant expansion and salt mitigation", 81),
    ],
    "2018-06-19": [
        ("15", "Wastewater service rates", 109),
        ("16", "FY 2018–19 budget and five-year capital projects budget", 110),
        ("17", "Wastewater Enterprise Lease Agreement termination", 110),
        ("18", "2018 wastewater bonds", 111),
        ("21", "FY 2016–17 audited financial statements", 112),
        ("22", "FY 2018–19 appropriations limit", 112),
    ],
    "2018-07-03": [
        ("5", "Calimesa animal control services agreement", 121),
        ("7", "Rolling Hills Ranch Industrial Park Specific Plan amendment", 122),
        ("8", "Logistics Way street vacation", 122),
        ("10", "Special tax refunding bonds", 123),
        ("11", "Wastewater revenue bonds", 124),
        ("12", "Community Choice Aggregation", 125),
        ("13", "Local wastewater discharge limits", 125),
        ("14", "Infrastructure server hardware purchase", 126),
    ],
}
VIDEO_CUES = {
    ("2015-11-17", "4.a"): "2:34:05",
    ("2015-11-17", "4.b"): "3:07:10",
    ("2015-11-17", "4.c"): "3:10:18",
    ("2017-05-16", "Workshop 1"): "0:00:04",
    ("2017-05-16", "3"): "1:11:53",
    ("2017-05-16", "20"): "1:50:21",
    ("2017-05-16", "21"): "2:41:48",
    ("2017-05-16", "22"): "3:07:56",
    ("2018-06-19", "16"): "3:42:34",
    ("2018-06-19", "17"): "4:01:30",
    ("2018-07-03", "7"): "1:05:51",
    ("2018-07-03", "8"): "1:20:43",
    ("2018-07-03", "11"): "3:09:38",
    ("2018-07-03", "13"): "4:38:50",
    ("2018-07-03", "14"): "4:40:54",
}


def packet_items(reader):
    bookmarks = [(reader.get_destination_page_number(entry) + 1, entry.title)
                 for entry in reader.outline if not isinstance(entry, list)]
    agenda_end = bookmarks[1][0]
    entries = {}
    for page, pdf_page in enumerate(reader.pages[:agenda_end - 1], 1):
        for line in pdf_page.extract_text(extraction_mode="layout").splitlines():
            match = re.match(r"^\s*([A-S]\.(?:\d+)?)\s{2,}(.+?)\s*$", line)
            if match:
                key, title = match.groups()
                entries[key] = [re.sub(r"\s{2,}\d+$", "", title), page, []]
    for index, (page, title) in enumerate(bookmarks[1:], 1):
        match = re.match(r"([A-S]\.\d+)\.\s*(.*)", title)
        stop = bookmarks[index + 1][0] - 1 if index + 1 < len(bookmarks) else len(reader.pages)
        if match:
            key, label = match.groups()
            row = entries.setdefault(key, [label.removesuffix(".pdf"), page, []])
            if not row[2] and re.match(r"Staff Report\s*[-–�]", label, re.I):
                row[0] = re.sub(r"^Staff Report\s*[-–�]\s*", "", label, flags=re.I).removesuffix(".pdf").strip()
        else:
            row = entries.setdefault("Attachments", ["Other packet attachments", page, []])
            label = title
        row[2].append((page, max(page, stop), label.removesuffix(".pdf").replace("\ufffd", "–")))
    numbered_sections = {key[0] for key in entries if re.fullmatch(r"[A-S]\.\d+", key)}
    return {key: row for key, row in entries.items() if not (
        re.fullmatch(r"[A-S]\.", key) and key[0] in numbered_sections)}


def pdf_link(url, page, label):
    return f'<a href="{escape(url, quote=True)}#page={page}">{escape(label)}</a>'


def watch_cue(video, cue, label="Watch around"):
    hours, minutes, seconds = map(int, cue.split(":"))
    offset = hours * 3600 + minutes * 60 + seconds
    return f'<a href="{escape(video, quote=True)}&amp;t={offset}s">{label} {cue}</a>'


def agenda_card(key, title, section, body, index):
    return (f'<details class="agenda-record" id="item-{index}" data-section="{escape(section, quote=True)}">'
            f'<summary><span class="agenda-number">{escape(key)}</span><strong>{escape(title)}</strong></summary>'
            f'<div class="agenda-body">{body}</div></details>')


def write_agenda(day, video, minutes, packet=None, archived_packet=None):
    meeting = date.fromisoformat(day)
    label = f"{meeting:%B} {meeting.day}, {meeting.year}"
    transcript = DOCS / "transcripts" / f"{day}-city-council-transcript.txt"
    links = [f'<a class="btn" href="{escape(video, quote=True)}">Watch Council meeting</a>']
    if transcript.exists():
        links.append(f'<a class="btn secondary" href="../transcripts/reader.html?date={day}">Search transcript</a>')
    if archived_packet and not packet:
        links.append(pdf_link(archived_packet, 1, "Open full agenda packet"))
    if minutes:
        doc, pages = minutes
        links.append(pdf_link(doc["url"], pages[0], "Read official minutes"))
    groups = {}
    if packet:
        packet_url, reader = packet
        links.append(pdf_link(packet_url, 1, f"Open full packet ({len(reader.pages):,} pages)"))
        for key, (title, page, attachments) in packet_items(reader).items():
            section = SECTIONS.get(key[0], "Other agenda items")
            body = f'<p>{pdf_link(packet_url, page, f"See packet page {page}")}</p>'
            if minutes:
                doc, pages = minutes
                minutes_page = next((p for p in pages if re.search(
                    rf"(?m)^\s*{re.escape(key)}(?:\s|$)", doc["textPages"][p - 1])), None)
                if minutes_page:
                    body += f'<p>{pdf_link(doc["url"], minutes_page, f"See minutes page {minutes_page}")}</p>'
            if attachments:
                body += '<ul>' + ''.join(f'<li>{pdf_link(packet_url, start, name)} '
                                         f'<small>(pp. {start}–{end})</small></li>'
                                         for start, end, name in attachments) + '</ul>'
            title = BUDGET_TITLES.get((day, key), title)
            anchor = key.rstrip(".").lower().replace(".", "-")
            groups.setdefault(section, []).append(agenda_card(key, title, section, body, anchor))
    elif minutes:
        doc, pages = minutes
        for key, title, page in HISTORICAL_ITEMS.get(day, []):
            assert page in pages, (day, page)
            section = "Selected agenda items"
            body = f'<p>{pdf_link(doc["url"], page, f"Read the Council record on minutes page {page}")}</p>'
            if (day, key) == ("2017-05-16", "20"):
                body += f'<p>{pdf_link(doc["url"], 81, "Read the recorded adoption vote (4–0)")}</p>'
                body += f'<p>{watch_cue(video, "2:41:11", "Watch the vote around")}</p>'
            cue = VIDEO_CUES.get((day, key))
            if cue:
                body += f"<p>{watch_cue(video, cue)}</p>"
            anchor = key.lower().replace(".", "-").replace(" ", "-")
            groups.setdefault(section, []).append(agenda_card(key, title, section, body, anchor))
        for page in pages:
            section = "Official minutes"
            body = f'<p>{pdf_link(doc["url"], page, f"Open minutes page {page}")}</p>'
            page_text = "\n".join(line.rstrip() for line in doc["textPages"][page - 1].strip().splitlines())
            body += f'<p style="white-space:pre-line">{escape(page_text)}</p>'
            groups.setdefault(section, []).append(agenda_card("Page", f"Minutes page {page}", section, body, page))
    controls = ""
    if groups:
        options = ''.join(f'<option>{escape(section)}</option>' for section in groups)
        cards = ''.join(f'<section class="agenda-section"><h2>{escape(section)}</h2>{"".join(rows)}</section>'
                        for section, rows in groups.items())
        config = json.dumps({"date": day})
        controls = f'''
        <div class="agenda-toolbar">
          <label>Search meeting records <input id="agenda-search" type="search"></label>
          <label>Section <select id="agenda-section"><option value="all">All sections</option>{options}</select></label>
        </div>
        <p id="agenda-count" role="status"></p>
        <p id="agenda-empty" hidden>No records match your search.</p>
        {cards}
        <dialog id="viewer-dialog"><strong id="viewer-title"></strong><button id="viewer-close">Close</button><iframe id="viewer-frame" title="Document viewer"></iframe></dialog>
        <script type="application/json" id="agenda-config">{config}</script>
        <script defer src="video-agendas.js"></script>'''
    title = "Interactive Council agenda" if groups else "Council meeting recording"
    if packet:
        note = "<p>Browse published agenda items and supporting documents. See the minutes for Council actions.</p>"
    elif minutes:
        note = "<p>Browse selected agenda items and the full minutes for this meeting.</p>"
    else:
        note = "<p>The published agenda and minutes for this meeting are unavailable in the catalog.</p>"
    if day == "2017-05-16":
        note += ("<p>The YouTube title says May 23. The presiding officer gives the May 16 meeting date "
                 f"when calling the regular session to order. {watch_cue(video, '1:05:30')}.</p>")
    (DOCS / "briefings" / f"{day}-sources.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label} {title} | Beaumont Intelligence</title>
<link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="video-agendas.css"></head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header class="app-header"><div class="wrap header-row"><a class="brand" href="../index.html">Beaumont Intelligence</a></div></header>
<main id="main" class="section"><div class="wrap narrow"><h1>{label} {title}</h1>
<p><a href="../council-meeting-sources.html">Council meeting sources</a></p>
<div class="status-actions">{" ".join(links)}</div>{note}{controls}
</div></main></body></html>
""", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", type=Path, default=Path.home() / "Downloads")
    args = parser.parse_args()
    from build_council_meeting_sources import meeting_records

    meetings = {record["date"]: record for record in meeting_records()}
    register = json.loads((ROOT / "data/council/minutes-register.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/document-storage-manifest.json").read_text(encoding="utf-8"))
    archived = {row["path"]: row["url"] for row in manifest["documents"]
                if row.get("publication_status") != "pending-upload"}
    for day in (*PACKETS, *HISTORICAL):
        packet = None
        if day in PACKETS:
            key = f"records/agenda-packets/{day}/{day}-city-council-agenda-package.pdf"
            target = DOCS / key
            source = next(args.downloads.glob(f"Agenda Package*{PACKETS[day]}.pdf"), None)
            if source and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            reader = PdfReader(target)
            meeting = date.fromisoformat(day)
            label = f"{meeting:%B} {meeting.day}, {meeting.year}"
            if label not in reader.pages[0].extract_text():
                raise ValueError(f"Packet cover does not match {day}: {target.name}")
            packet = (archived.get(key, "../" + key), reader)
            print(day, len(reader.pages), "packet pages")
        minutes = None
        for doc in register["documents"]:
            pages = [i for i, value in enumerate(doc["pageDates"], 1) if value == day]
            if doc["date"] == day and doc["kind"] == "regular":
                pages = list(range(1, len(doc["textPages"]) + 1))
            if day == "2017-05-16":
                pages = [page for page in pages if page >= 75]
            if pages:
                minutes = (doc, pages)
                break
        write_agenda(day, meetings[day]["video"], minutes, packet, meetings[day].get("packet"))


if __name__ == "__main__":
    main()

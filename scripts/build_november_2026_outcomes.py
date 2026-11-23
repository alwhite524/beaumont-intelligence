"""Publish reviewed November 17 outcomes alongside the preserved agenda analysis."""

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
START = "<!-- november-17-outcomes:start -->"
END = "<!-- november-17-outcomes:end -->"


def build():
    review = json.loads((ROOT / "data/council/2026-11-17-outcomes.json").read_text(encoding="utf-8"))
    cards = []
    for item in review["items"]:
        seconds = item["videoSeconds"]
        timestamp = f"{seconds // 3600}:{seconds % 3600 // 60:02}:{seconds % 60:02}"
        vote = f' · {item["vote"]}' if item["vote"] else ""
        limit = f'<p class="source-note">{escape(item["evidenceLimit"])}</p>' if item.get("evidenceLimit") else ""
        cards.append(
            f'<article class="card"><div class="meta">{escape(item["item"] + vote)}</div>'
            f'<h3>{escape(item["title"])}</h3><p>{escape(item["summary"])}</p>{limit}'
            f'<a href="{review["videoUrl"]}&amp;t={seconds}s">Watch at {timestamp}</a></article>'
        )
    section = (
        START + '<section id="meeting-outcomes" aria-labelledby="outcomes-title">'
        '<h2 id="outcomes-title">November 17 Council actions</h2>'
        f'<p class="source-note">{escape(review["evidence"])}</p>'
        '<p><a href="../transcripts/reader.html?date=2026-11-17">Search the meeting transcript</a></p>'
        + "".join(cards) + "</section>" + END
    )
    for name in ("2026-11-17.html", "2026-11-17-sources.html"):
        path = DOCS / "briefings" / name
        page = path.read_text(encoding="utf-8")
        page = re.sub(re.escape(START) + ".*?" + re.escape(END), "", page, flags=re.S)
        page = page.replace('Upcoming interactive agenda', 'Interactive agenda')
        page = page.replace("Proposed actions await Council decisions.", "See the reviewed Council actions above.")
        # Place the outcome review after the first heading on either page.
        page = re.sub(r"</h1>", lambda match: match.group(0) + section, page, count=1)
        path.write_text(page, encoding="utf-8")
    agenda = ROOT / "data/council/2026-11-17-agenda.json"
    data = json.loads(agenda.read_text(encoding="utf-8"))
    data["meetingStatus"] = "held"
    data["videoUrl"] = review["videoUrl"]
    data["outcomesSource"] = "data/council/2026-11-17-outcomes.json"
    agenda.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()

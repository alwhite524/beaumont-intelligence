"""Route archived briefing PDF links through the shared document viewer."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIEFINGS = (
    ROOT / "docs" / "briefings" / "2026-07-21.html",
    ROOT / "docs" / "briefings" / "2026-08-04.html",
)

LINK_PATTERN = re.compile(
    r'<a([^>]*?)href="(\.\./official-documents/[^"]+\.pdf)"([^>]*)>',
    re.IGNORECASE,
)


def migrate(path: Path) -> int:
    source = path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        attributes = match.group(1) + match.group(3)
        attributes = re.sub(
            r'\s+(?:target="_blank"|rel="noopener")', "", attributes
        )
        relative_pdf = match.group(2).split("/official-documents/", 1)[1]
        return (
            f'<a{attributes} href="../documents/viewer.html?pdf={relative_pdf}">'
        )

    migrated, count = LINK_PATTERN.subn(replace, source)
    if count:
        path.write_text(migrated, encoding="utf-8", newline="")
    return count


def validate(path: Path) -> tuple[int, list[str]]:
    source = path.read_text(encoding="utf-8")
    document_data = (ROOT / "docs" / "documents" / "document-data.js").read_text(
        encoding="utf-8"
    )
    viewer_links = re.findall(r'documents/viewer\.html\?pdf=([^"&]+)', source)
    missing = [link for link in viewer_links if link.split("/", 1)[1] not in document_data]
    direct_pdfs = re.findall(
        r'href="[^"]*official-documents[^"]+\.pdf"', source, re.IGNORECASE
    )
    new_tab_viewers = re.findall(
        r'<a[^>]+documents/viewer[^>]+target="_blank"', source, re.IGNORECASE
    )
    if direct_pdfs or new_tab_viewers:
        missing.extend(direct_pdfs + new_tab_viewers)
    return len(viewer_links), missing


if __name__ == "__main__":
    for briefing in BRIEFINGS:
        print(f"{briefing.name}: {migrate(briefing)} links migrated")
        count, problems = validate(briefing)
        print(f"{briefing.name}: {count} viewer links, {len(problems)} problems")
        if problems:
            raise SystemExit("\n".join(problems))

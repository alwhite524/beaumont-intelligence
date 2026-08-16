"""Identify archived PDFs that need raster fallbacks in browser viewers."""

from collections import Counter
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def filters_for(path: Path) -> Counter[str]:
    filters: Counter[str] = Counter()
    reader = PdfReader(path)
    for page in reader.pages:
        xobjects = (page.get("/Resources") or {}).get("/XObject") or {}
        for item in xobjects.values():
            obj = item.get_object()
            filters[str(obj.get("/Filter"))] += 1
    return filters


for meeting in ("2026-07-21", "2026-08-04"):
    for pdf in sorted((ROOT / "docs" / "official-documents" / meeting).glob("*.pdf")):
        filters = filters_for(pdf)
        if any("CCITTFaxDecode" in name for name in filters):
            pages = len(PdfReader(pdf).pages)
            print(f"{meeting}\t{pdf.name}\t{pages}\t{dict(filters)}")

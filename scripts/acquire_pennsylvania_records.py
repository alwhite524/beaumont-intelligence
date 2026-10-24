"""Retrieve and fingerprint the primary Pennsylvania reconciliation records."""
import hashlib
import json
from pathlib import Path
import urllib.request
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/official-documents/pennsylvania-reconciliation-2026-10-24'
REPORT = ROOT / 'docs/research/pennsylvania'
SOURCES = {
    'ctc-march-baseline': 'https://catc.ca.gov/-/media/ctc-media/documents/programs/shopp/baseline-agreements/2026-03/pennsylvania-avenue-grade-separation-project.pdf',
    'ctc-march-agency-change': 'https://catc.ca.gov/-/media/ctc-media/documents/ctc-meetings/2026/2026-03/96-4-22-a11y.pdf',
    'ctc-may-extension-request': 'https://catc.ca.gov/-/media/ctc-media/documents/ctc-meetings/2026/2026-05/123-2-8a9-a11y.pdf',
    'rctc-january-western-riverside': 'https://www.rctc.org/wp-content/uploads/2026/01/WRC-January-Agenda.pdf',
    'rctc-february-commission': 'https://www.rctc.org/wp-content/uploads/2026/02/February-Commission-Agenda.pdf',
    'city-august-staff-report': 'https://documents.beaumontintelligence.com/official-documents/2026-08-04/j-2-staff-report-pennsylvania-ave-grade-separation-funding-strategy.pdf',
    'city-august-rctc-presentation': 'https://documents.beaumontintelligence.com/official-documents/2026-08-04/j-2-attachment-rctc-project-update-presentation.pdf',
    'city-august-timeline': 'https://documents.beaumontintelligence.com/official-documents/2026-08-04/j-2-a-project-timeline.pdf',
}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    register = []
    for name, url in SOURCES.items():
        row = dict(id=name, source_url=url, retrieved_on='2026-10-24')
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read()
                row['resolved_url'] = response.url
            if not payload.startswith(b'%PDF-'):
                raise ValueError('Response is not a PDF')
            path = OUT / (name + '.pdf')
            path.write_bytes(payload)
            reader = PdfReader(path)
            text = '\n'.join(f'\n--- PDF page {n} ---\n{page.extract_text() or ""}' for n, page in enumerate(reader.pages, 1))
            (REPORT / (name + '.txt')).write_text(text, encoding='utf-8')
            row.update(status='retrieved', path=path.relative_to(ROOT).as_posix(), bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(), pages=len(reader.pages))
        except Exception as error:
            row.update(status='failed', error=str(error))
        register.append(row)
        print(name, row['status'], flush=True)
        (REPORT / 'acquisition-register.json').write_text(json.dumps(register, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()

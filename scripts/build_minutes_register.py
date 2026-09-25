"""Consolidate local minutes and cache searchable text; retain existing archive URLs."""
import hashlib
import json
import re
import zipfile
from xml.etree import ElementTree
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
REGISTER = ROOT / 'data/council/minutes-register.json'

MONTHS = ('January|February|March|April|May|June|July|August|September|October|November|December')


def annual_page_dates(pages: list[str], year: str) -> list[str]:
    """Associate each compilation page with the meeting date printed in its header."""
    current = ''
    dates = []
    pattern = re.compile(rf'\b({MONTHS})\s*(\d{{1,2}}),?\s*({year})\b', re.I)
    for page in pages:
        # Limit the scan to the heading so an agenda-item date does not relabel
        # subsequent pages from the same meeting.
        match = pattern.search(re.sub(r'\s+', ' ', page[:1200]))
        if match:
            current = datetime.strptime(
                f'{match.group(1)} {match.group(2)} {match.group(3)}', '%B %d %Y'
            ).strftime('%Y-%m-%d')
        dates.append(current)
    return dates


def main():
    manifest = json.loads((ROOT / 'data/document-storage-manifest.json').read_text(encoding='utf-8'))
    previous = {r['archivePath']: r for r in json.loads(REGISTER.read_text(encoding='utf-8'))['documents']} if REGISTER.exists() else {}
    folder = DOCS / 'minutes'
    folder.mkdir(exist_ok=True)
    records = []
    for doc in manifest['documents']:
        archive = doc['path']
        if 'minutes' not in Path(archive).stem.lower() or doc.get('publication_status') == 'pending-upload':
            continue
        old = previous.get(archive, {})
        filename = archive.replace('/', '--')
        local = folder / filename
        original = DOCS / archive
        if original.exists() and original != local:
            if local.exists():
                raise RuntimeError(f'Duplicate local file needs review: {archive}')
            original.rename(local)
        if not local.exists():
            raise FileNotFoundError(local)
        checksum = hashlib.sha256(local.read_bytes()).hexdigest()
        if checksum != doc['sha256']:
            raise RuntimeError(f'Checksum mismatch: {archive}')
        name = Path(archive).stem
        annual = re.fullmatch(r'(20\d{2})-council-minutes', name)
        date = ''
        match = re.search(r'cc-minutes-(\d{2})-(\d{2})-(\d{4})', name)
        named = re.search(r'minutes-of-([a-z]+-\d{1,2}-\d{4})', name)
        if match:
            date = f'{match[3]}-{match[1]}-{match[2]}'
        elif named:
            date = datetime.strptime(named[1], '%B-%d-%Y').strftime('%Y-%m-%d')
        elif name in ('council-minutes', 'special-meeting-minutes', 'workshop-minutes'):
            date = archive.split('/')[-2]
        elif name == 'g-2-september-2-minutes-item-bundle':
            date = '2025-09-02'
        elif name == 'g-2-august-4-2026-minutes':
            date = '2026-08-04'
        elif re.fullmatch(r'\d{4}-\d{2}-\d{2}-(?:council|special-meeting|workshop)-minutes', name):
            date = name[:10]
        date = old.get('date') or date
        if date:
            datetime.strptime(date, '%Y-%m-%d')
        kind = 'annual' if annual else 'special' if 'special' in name or 'sp-mtg' in name else 'workshop' if 'workshop' in name else 'regular'
        kind = old.get('kind') or kind
        pages = old.get('textPages') if old.get('sha256') == checksum else None
        if pages is None:
            if local.suffix.lower() == '.docx':
                with zipfile.ZipFile(local) as word:
                    tree = ElementTree.fromstring(word.read('word/document.xml'))
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                pages = ['\n'.join(''.join(t.text or '' for t in paragraph.findall('.//w:t', ns))
                                   for paragraph in tree.findall('.//w:p', ns))]
            else:
                pages = [page.extract_text() or '' for page in PdfReader(local).pages]
        title = f'{annual[1]} Council minutes compilation' if annual else f'{date or "Undated"} {kind.title()} Council minutes'
        if local.suffix.lower() == '.docx':
            title += ' (Word original)'
        page_dates = annual_page_dates(pages, annual[1]) if annual else []
        records.append(dict(archivePath=archive, localPath=local.relative_to(DOCS).as_posix(), url=doc['url'],
                            date=date, year=annual[1] if annual else date[:4], kind=kind, title=title,
                            sha256=checksum, textPages=pages, pageDates=page_dates))
    REGISTER.write_text(json.dumps({'description': 'Minutes catalog using existing document-storage-manifest archive identities. Extracted text is a search aid, not verified transcription.', 'documents': records}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Minutes catalog: {len(records)} files in docs/minutes')


if __name__ == '__main__':
    main()

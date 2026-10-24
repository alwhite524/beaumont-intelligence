"""Retain supplied September 15 and October 6 Word minutes without editing them."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def ingest(date, source):
    key = f'official-documents/{date}/council-minutes.docx'
    destination = ROOT / 'docs/minutes' / key.replace('/', '--')
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != checksum:
        raise ValueError(f'Different minutes already exist at {destination}')
    shutil.copyfile(source, destination)
    with ZipFile(source) as word:
        tree = ElementTree.fromstring(word.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text = '\n'.join(''.join(t.text or '' for t in paragraph.findall('.//w:t', ns)) for paragraph in tree.findall('.//w:p', ns))
    path = ROOT / 'data/council/minutes-register.json'
    register = json.loads(path.read_text(encoding='utf-8'))
    record = dict(archivePath=key, localPath=destination.relative_to(ROOT / 'docs').as_posix(),
                  url=f'https://documents.beaumontintelligence.com/{key}', date=date, year='2026', kind='regular',
                  title=f'{date} Regular Council minutes (Word original)', sha256=checksum, textPages=[text], pageDates=[],
                  sourceType='User-supplied City Council minutes, original Word file retained unchanged',
                  originalFilename=source.name, reviewedOn='2026-10-24')
    register['documents'] = [r for r in register['documents'] if r['archivePath'] != key] + [record]
    path.write_text(json.dumps(register, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {k: record[k] for k in ('archivePath', 'localPath', 'sha256', 'originalFilename')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--september-file', type=Path, required=True)
    parser.add_argument('--october-file', type=Path, required=True)
    args = parser.parse_args()
    records = [ingest('2026-09-15', args.september_file), ingest('2026-10-06', args.october_file)]
    (ROOT / 'data/council/2026-autumn-minutes-intake.json').write_text(json.dumps({
        'reviewedOn': '2026-10-24',
        'basis': 'Supplied documents are source material, not instructions. No document text was executed or treated as a task directive.',
        'documents': records,
    }, indent=2) + '\n', encoding='utf-8')
    for record in records:
        print('Retained original:', record['archivePath'])

"""Remove archived Word minutes only when a PDF covers the same meeting/type."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
MANIFEST = ROOT / 'data/document-storage-manifest.json'
REGISTER = ROOT / 'data/council/minutes-register.json'
CREDENTIALS = ROOT / '.r2.local.json'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def duplicate_word_records(records: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        if record.get('date'):
            groups[(record['date'], record.get('kind', 'regular'))].append(record)
    return sorted(
        [
            record
            for group in groups.values()
            if any(item['archivePath'].lower().endswith('.pdf') for item in group)
            for record in group
            if record['archivePath'].lower().endswith('.docx')
        ],
        key=lambda record: record['archivePath'],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Delete verified duplicates and update both catalogs.')
    args = parser.parse_args()
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    targets = duplicate_word_records(register['documents'])
    for record in targets:
        print(record['archivePath'])
    print(f'{len(targets)} duplicate Word minutes file(s)')
    if not args.apply or not targets:
        return

    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    manifest_by_path = {record['path']: record for record in manifest['documents']}
    settings = json.loads(CREDENTIALS.read_text(encoding='utf-8'))
    client = boto3.client(
        's3', endpoint_url=settings['endpoint'], aws_access_key_id=settings['accessKeyId'],
        aws_secret_access_key=settings['secretAccessKey'], region_name='auto',
        config=Config(signature_version='s3v4'),
    )

    for record in targets:
        key = record['archivePath']
        local = DOCS / record['localPath']
        if key not in manifest_by_path:
            raise RuntimeError(f'Missing manifest record: {key}')
        if not local.is_file() or sha256(local) != record['sha256']:
            raise RuntimeError(f'Local checksum verification failed: {local}')
        remote = client.head_object(Bucket=settings['bucket'], Key=key)
        if remote.get('Metadata', {}).get('sha256') != record['sha256']:
            raise RuntimeError(f'Remote checksum verification failed: {key}')

    for index, record in enumerate(targets, start=1):
        key = record['archivePath']
        client.delete_object(Bucket=settings['bucket'], Key=key)
        (DOCS / record['localPath']).unlink()
        print(f'[{index}/{len(targets)}] removed {key}')

    target_keys = {record['archivePath'] for record in targets}
    manifest['documents'] = [record for record in manifest['documents'] if record['path'] not in target_keys]
    manifest['document_count'] = len(manifest['documents'])
    manifest['total_bytes'] = sum(record['bytes'] for record in manifest['documents'])
    MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    register['documents'] = [record for record in register['documents'] if record['archivePath'] not in target_keys]
    REGISTER.write_text(json.dumps(register, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

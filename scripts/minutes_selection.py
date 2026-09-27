"""Choose one public minutes file for each meeting date and session type."""
from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath


def _preference(record: dict) -> tuple[int, str]:
    path = record['archivePath']
    suffix = PurePosixPath(path).suffix.lower()
    date = record.get('date', '')
    kind = record.get('kind', 'regular')
    filename = {
        'regular': 'council-minutes.pdf',
        'special': 'special-meeting-minutes.pdf',
        'workshop': 'workshop-minutes.pdf',
    }.get(kind, '')
    canonical = f'official-documents/{date}/{filename}' if date and filename else ''
    if path == canonical:
        rank = 0
    elif suffix == '.pdf' and 'cc-minutes-' in PurePosixPath(path).name.lower():
        rank = 1
    elif suffix == '.pdf' and 'alternate-' not in path.lower():
        rank = 2
    elif suffix == '.pdf':
        rank = 3
    else:
        rank = 4
    return rank, path


def preferred_minutes(records: list[dict]) -> list[dict]:
    """Return one preferred PDF, or one Word file when no PDF exists, per meeting/type."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        identity = record.get('date') or record.get('year') or record['archivePath']
        groups[(identity, record.get('kind', 'regular'))].append(record)
    return [min(group, key=_preference) for group in groups.values()]

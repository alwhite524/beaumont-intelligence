"""Route published archive links into the site's document viewer."""
import json
import os
import re
from html import escape, unescape
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
ARCHIVE_HOST = 'documents.beaumontintelligence.com'
ANCHOR = re.compile(r'<a\s[^<>]*>', re.I)
HREF = re.compile(r'(?<![\w-])href\s*=\s*(["\'])(.*?)\1', re.I | re.S)
DOWNLOAD = re.compile(r'\sdownload(?=\s|=|>)(?:\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+))?', re.I)


def route_link(tag, page):
    match = HREF.search(tag)
    if not match:
        return tag
    href = unescape(match[2])
    try:
        url = urlsplit(href)
    except ValueError:
        return tag
    if url.path.endswith('/viewer.html') or url.path == 'viewer.html':
        return DOWNLOAD.sub('', tag)
    if PurePosixPath(url.path).suffix.lower() not in ('.pdf', '.docx'):
        return tag

    viewer = DOCS / 'documents' / 'viewer.html'
    if url.hostname == ARCHIVE_HOST and url.scheme == 'https':
        source = urlunsplit(url._replace(fragment=''))
    elif not url.netloc and not url.scheme and not url.path.startswith('/'):
        path = (page.parent / unquote(url.path)).resolve()
        if not path.is_relative_to(DOCS) or not path.is_file():
            return tag
        source = Path(os.path.relpath(path, viewer.parent)).as_posix()
    else:
        return tag

    params = {'url': source}
    if fragment := re.fullmatch(r'page=(\d+)', url.fragment, re.I):
        params['page'] = fragment[1]
    href = Path(os.path.relpath(viewer, page.parent)).as_posix() + '?' + urlencode(params)
    return DOWNLOAD.sub('', tag[:match.start(2)] + escape(href, quote=True) + tag[match.end(2):])


def main():
    minutes = json.loads((ROOT / 'data/council/minutes-register.json').read_text(encoding='utf-8'))['documents']
    word_records = []
    for record in minutes:
        url = record['url']
        if url.endswith('.docx'):
            word_records.append({'url': url if url.startswith('https://') else '../' + url,
                                 'text': '\n'.join(record['textPages'])})
    (DOCS / 'documents/word-minutes.json').write_text(
        json.dumps(word_records, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8'
    )

    for page in DOCS.rglob('*.html'):
        original = page.read_bytes()
        html = original.decode('utf-8')
        updated = ANCHOR.sub(lambda match: route_link(match[0], page), html)
        if updated != html:
            page.write_bytes(updated.encode('utf-8'))


if __name__ == '__main__':
    main()

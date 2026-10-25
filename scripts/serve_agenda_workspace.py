"""Private, loopback-only meeting review dashboard. No publishing or external AI."""
from __future__ import annotations
import argparse
from datetime import date as calendar_date, datetime, timezone
import hashlib
import html
import importlib.util
import io
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import parse_qs, unquote, urlsplit, urlencode
from agenda_package import PackageWorkflow

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ('not-started', 'in-progress', 'needs-clarification', 'ready')
RENDER_LOCK = threading.Lock()  # PDFium calls must not run concurrently.
MAX_UPLOAD = 50 * 1024 * 1024

def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Invalid date')
    calendar_date.fromisoformat(value)
    return value

def local_document(root, url):
    parsed = urlsplit(url)
    if parsed.hostname != 'documents.beaumontintelligence.com':
        return None
    base = (root / 'docs').resolve()
    path = (base / unquote(parsed.path.lstrip('/'))).resolve()
    return path if path.is_relative_to(base) and path.is_file() and path.suffix.lower() == '.pdf' else None

def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def load_meeting(root, date):
    valid_date(date)
    source = root / f'data/council/{date}-agenda.json'
    if not source.exists():
        raise FileNotFoundError('Meeting not collected')
    agenda = read_json(source, {})
    packet = read_json(root / f'data/council/{date}-packet-map.json', {})
    review = read_json(root / f'data/council/{date}-review.json', {})
    outcomes = read_json(root / f'data/council/{date}-outcomes.json', {})
    documents = agenda.get('documents') or packet.get('documents') or []
    if not documents:
        path = root / f'docs/briefings/{date}-sources.js'
        if path.exists():
            text = path.read_text(encoding='utf-8')
            try:
                documents = json.loads(text[text.index('=') + 1:].strip().rstrip(';'))
            except (ValueError, json.JSONDecodeError):
                pass
    items = {}
    for row in agenda.get('items', []):
        if isinstance(row, dict) and row.get('item'):
            items[row['item']] = dict(row)
    for doc in documents:
        key = doc.get('item')
        if key and key not in items:
            items[key] = dict(item=key, title=doc.get('itemTitle') or key, section=doc.get('section') or 'Agenda', summary='')
    reviewed = review.get('items', {})
    if not isinstance(reviewed, dict):
        reviewed = {r['item']: r for r in reviewed if r.get('item')}
    result = []
    for key, item in items.items():
        details = reviewed.get(key, {})
        checks = item.get('checks', []) + details.get('checks', [])
        unique = {json.dumps(c, sort_keys=True): c for c in checks}
        flags = [dict(c, id=hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()[:16]) for c in unique.values() if c.get('attention')]
        docs = []
        for i, doc in enumerate(d for d in documents if d.get('item') == key):
            url = doc.get('archiveUrl') or doc.get('officialUrl') or ''
            if not url.startswith('https://'):
                continue
            docs.append(dict(id=hashlib.sha256(url.encode()).hexdigest()[:16], title=doc.get('title') or 'Source document', url=url, officialUrl=doc.get('officialUrl'), pageStart=doc.get('packet_page_start'), pageEnd=doc.get('packet_page_end'), localAvailable=bool(local_document(root, url)) and importlib.util.find_spec('pypdfium2') is not None))
        outcome = next((r for r in outcomes.get('items', []) if r.get('item') == key), None)
        result.append(dict(item=key, title=item.get('title') or key, section=item.get('section') or 'Agenda', summary=details.get('summary') or item.get('summary') or '', funding=details.get('funding') or '', question=details.get('question') or '', flags=flags, documents=docs, outcome=outcome))
    if not result:
        raise ValueError('No structured agenda items available')
    return dict(date=date, items=result, audit=agenda.get('audit', {}), officialAgendaUrl=agenda.get('officialAgendaUrl'), reviewDate=review.get('reviewedOn'), reviewScope=review.get('scope'), outcomeEvidence=outcomes.get('evidence'), packetUrl=packet.get('packetArchiveUrl') or agenda.get('packetArchiveUrl'))

class Store:
    def __init__(self, root, path):
        self.root, self.path = root, path
        self.lock = threading.Lock()
        self.packages = PackageWorkflow(self)

    def read(self, date, revision=None):
        active=self.packages.data(date)['active']
        revision=active if revision is None else revision
        suffix=f'-r{revision}' if revision else ''
        return read_json(self.path / f'{date}{suffix}.json', dict(date=date, items={}))

    def catalog_path(self, date):
        return self.path.parent / 'meetings' / f'{valid_date(date)}.json'

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Windows sync/scanner processes may briefly hold the destination open.
        for attempt in range(6):
            try:
                temporary.replace(path)
                break
            except PermissionError:
                if attempt==5:raise
                time.sleep(0.05*(2**attempt))

    def meeting(self, date, revision=None):
        if self.packages.data(date)['active']:
            return self.packages.meeting(date,revision)
        catalog = read_json(self.catalog_path(date), {})
        try:
            meeting = load_meeting(self.root, date)
        except FileNotFoundError:
            if not catalog:
                raise
            meeting = dict(date=date, items=[], audit={}, officialAgendaUrl=None, reviewDate=None, reviewScope='', outcomeEvidence='', packetUrl=None)
        meeting['title'] = catalog.get('title') or f'{date} City Council'
        existing = {i['item']: i for i in meeting['items']}
        for row in catalog.get('items', []):
            key = row['item']
            if key not in existing:
                item = dict(item=key, title=row['title'], section=row.get('section') or 'Private agenda', summary=row.get('summary') or '', funding='', question='', flags=[], documents=[], outcome=None)
                meeting['items'].append(item)
                existing[key] = item
            for doc in row.get('documents', []):
                existing[key]['documents'].append(dict(doc, localAvailable=importlib.util.find_spec('pypdfium2') is not None))
        return meeting

    def dates(self):
        dates = {p.name[:10] for p in (self.root / 'data/council').glob('????-??-??-agenda.json')}
        dates.update(p.stem for p in (self.path.parent / 'meetings').glob('????-??-??.json'))
        dates.update(p.stem for p in (self.path.parent / 'packages').glob('????-??-??.json'))
        return sorted(dates, reverse=True)

    def create_meeting(self, date, title):
        valid_date(date)
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError('Use a meeting title up to 200 characters')
        with self.lock:
            if date in self.dates():
                raise ValueError('A meeting already exists on that date. Select it to add documents.')
            self.write_json(self.catalog_path(date), dict(date=date, title=title.strip(), items=[dict(item='MEETING', title='Agenda and full packet', section='Meeting documents', documents=[])]))

    def add_item(self, date, key, title, section):
        if self.packages.data(date)['active']:
            raise ValueError('Correct the complete agenda outside this app, then upload a new revision')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,30}', key):
            raise ValueError('Use an item number such as J.1, without spaces or slashes')
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError('Use an item title up to 200 characters')
        if section not in ('Consent', 'Public Hearing', 'Action', 'Meeting documents', 'Other'):
            raise ValueError('Invalid section')
        with self.lock:
            meeting = self.meeting(date)
            if any(i['item'] == key for i in meeting['items']):
                raise ValueError('That agenda item already exists')
            catalog = read_json(self.catalog_path(date), dict(date=date, title=meeting['title'], items=[]))
            catalog['items'].append(dict(item=key, title=title.strip(), section=section, documents=[]))
            self.write_json(self.catalog_path(date), catalog)

    def document_path(self, doc):
        if doc.get('uploaded'):
            digest = doc.get('sha256', '')
            if not re.fullmatch(r'[0-9a-f]{64}', digest):
                return None
            path = self.path.parent / 'documents' / f'{digest}.pdf'
            return path if path.is_file() else None
        return local_document(self.root, doc['url'])

    def upload(self, date, key, filename, title, payload):
        if self.packages.data(date)['active']:
            raise ValueError('Upload corrections as a complete new draft revision, not individual replacements')
        if len(payload) > MAX_UPLOAD or not payload.startswith(b'%PDF-'):
            raise ValueError('Upload a PDF no larger than 50 MB')
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError('Use a document title up to 200 characters')
        filename = filename.replace('\\', '/').split('/')[-1][:200]
        if not filename.lower().endswith('.pdf'):
            raise ValueError('Only PDF documents are supported')
        # Parse before storing: a renamed HTML/ZIP or locked PDF is not an accepted source.
        try:
            from pypdf import PdfReader
            pdf = PdfReader(io.BytesIO(payload), strict=True)
            if pdf.is_encrypted or not len(pdf.pages):
                raise ValueError()
            pages = len(pdf.pages)
        except Exception:
            raise ValueError('The PDF is damaged, empty or password-protected. Upload an unlocked PDF.') from None
        digest = hashlib.sha256(payload).hexdigest()
        with self.lock:
            meeting = self.meeting(date)
            item = next((i for i in meeting['items'] if i['item'] == key), None)
            if not item:
                raise ValueError('Select an existing agenda item')
            prior = next((d for d in item['documents'] if d.get('sha256') == digest), None)
            if prior:
                return dict(document=prior, duplicate=True)
            catalog = read_json(self.catalog_path(date), dict(date=date, title=meeting['title'], items=[]))
            row = next((i for i in catalog['items'] if i['item'] == key), None)
            if row is None:
                row = dict(item=key, title=item['title'], section=item['section'], documents=[])
                catalog['items'].append(row)
            identifier = 'upload-' + digest
            query = urlencode(dict(date=date, item=key, doc=identifier))
            doc = dict(id=identifier, title=title.strip(), filename=filename, url='/api/uploaded?' + query, uploaded=True, sha256=digest, bytes=len(payload), pages=pages, uploadedAt=datetime.now(timezone.utc).isoformat(), officialUrl=None, pageStart=None, pageEnd=None)
            destination = self.path.parent / 'documents' / f'{digest}.pdf'
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                temporary = destination.with_suffix('.tmp')
                temporary.write_bytes(payload)
                temporary.replace(destination)
            row.setdefault('documents', []).append(doc)
            # A new document invalidates a prior "ready" decision and stale open-tab saves.
            state = self.read(date)
            review = state['items'].setdefault(key, dict(status='not-started', notes='', clarifications='', reviewedDocuments=[], resolvedFlags=[], version=0))
            review['version'] += 1
            review['updatedAt'] = datetime.now(timezone.utc).isoformat()
            if review['status'] == 'ready':
                review['status'] = 'in-progress'
            self.write_json(self.path / f'{date}.json', state)
            self.write_json(self.catalog_path(date), catalog)
            return dict(document=doc, duplicate=False)

    def save(self, date, key, value):
        if not isinstance(value, dict):
            raise ValueError('Invalid review')
        meeting = self.meeting(date)
        if meeting.get('package') and value.get('packageRevision')!=meeting['package']['number']:
            raise ValueError('Reload the current draft before saving review notes')
        item = next((x for x in meeting['items'] if x['item'] == key), None)
        if not item:
            raise ValueError('Unknown agenda item')
        if value.get('status') not in STATUSES:
            raise ValueError('Invalid review status')
        if meeting.get('package') and value['status']=='ready':
            issues=meeting['package']['analysis']['issues']
            if any(i['status']!='resolved' and i['item'] in (key,'MEETING') for i in issues):
                raise ValueError('Resolve or recheck this item’s package findings before marking it ready')
            if set(value.get('reviewedDocuments',[]))!={d['id'] for d in item['documents']}:
                raise ValueError('Check each supporting document before marking this item ready')
        for field, limit in [('notes', 20000), ('clarifications', 10000)]:
            if not isinstance(value.get(field), str) or len(value[field]) > limit:
                raise ValueError(f'Invalid {field}')
        for field, allowed in [('reviewedDocuments', {d['id'] for d in item['documents']}), ('resolvedFlags', {f['id'] for f in item['flags']})]:
            selected = value.get(field)
            if not isinstance(selected, list) or len(selected) > len(allowed) or any(not isinstance(s, str) or s not in allowed for s in selected):
                raise ValueError(f'Invalid {field}')
        with self.lock:
            if meeting.get('package') and self.packages.data(date)['active']!=meeting['package']['number']:
                return None
            state = self.read(date)
            current = state['items'].get(key, {})
            if value.get('version') != current.get('version', 0):
                return None
            saved = {k: value[k] for k in ('status', 'notes', 'clarifications', 'reviewedDocuments', 'resolvedFlags')}
            saved.update(version=current.get('version', 0) + 1, updatedAt=datetime.now(timezone.utc).isoformat())
            state['items'][key] = saved
            suffix=f'-r{meeting["package"]["number"]}' if meeting.get('package') else ''
            target = self.path / f'{date}{suffix}.json'
            self.write_json(target,state)
            return saved

class WorkspaceServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, root=ROOT, storage=None):
        self.root = root
        self.store = Store(root, storage or root / 'private-workspace/agenda-reviews')
        self.access_code = secrets.token_urlsafe(24)
        self.sessions = set()
        super().__init__(address, Handler)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # No private note/request-body logging.

    def send(self, value, status=200, content_type='application/json', cookie=None):
        body = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def authenticated(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            return cookie.get('agenda_session') is not None and cookie['agenda_session'].value in self.server.sessions
        except Exception:
            return False

    def do_GET(self):
        if not self.valid_host():
            return self.send({'error': 'Invalid host'}, 403)
        url = urlsplit(self.path)
        if url.path in ('/', '/dashboard.js', '/dashboard.css', '/package-review.js'):
            name = {'/': 'index.html', '/dashboard.js': 'dashboard.js', '/dashboard.css': 'dashboard.css', '/package-review.js':'package-review.js'}[url.path]
            path = self.server.root / 'private-dashboard' / name
            return self.send(path.read_bytes(), content_type='text/javascript; charset=utf-8' if name.endswith('.js') else 'text/css; charset=utf-8' if name.endswith('.css') else 'text/html; charset=utf-8')
        if not self.authenticated():
            return self.send({'error': 'Unlock the workspace first'}, 401)
        try:
            if url.path == '/api/meetings':
                dates = []
                for date in self.server.store.dates():
                    try:
                        meeting = self.server.store.meeting(date)
                        dates.append(dict(date=meeting['date'], title=meeting['title'], count=len(meeting['items'])))
                    except (ValueError, KeyError):
                        continue
                return self.send({'meetings': dates})
            if url.path in ('/api/meeting', '/api/export'):
                date = parse_qs(url.query).get('date', [''])[0]
                revision = int(parse_qs(url.query)['revision'][0]) if 'revision' in parse_qs(url.query) else None
                meeting = self.server.store.meeting(date,revision)
                state = self.server.store.read(date,revision)
                return self.send(dict(meeting=meeting, state=state))
            if url.path in ('/document', '/api/document-page', '/api/uploaded'):
                params = parse_qs(url.query)
                date, key, document_id = (params.get(k, [''])[0] for k in ('date', 'item', 'doc'))
                revision = int(params['revision'][0]) if 'revision' in params else None
                if 'stage' in params:
                    stage=self.server.store.packages.stage(params['stage'][0])
                    row=next((d for d in stage.get('analysis',{}).get('documents',[]) if d['id']==document_id),None)
                    doc=dict(row,uploaded=True,sha256=row['file'],url='/api/uploaded?'+urlencode(dict(stage=stage['id'],doc=document_id)),localAvailable=True) if row else None
                else:
                    meeting = self.server.store.meeting(date,revision)
                    item = next((i for i in meeting['items'] if i['item'] == key), None)
                    doc = next((d for d in item['documents'] if d['id'] == document_id), None) if item else None
                path = self.server.store.document_path(doc) if doc else None
                if url.path == '/api/uploaded' and path and doc.get('uploaded'):
                    return self.send(path.read_bytes(), content_type='application/pdf')
                if not path or not doc['localAvailable']:
                    return self.send({'error': 'Local document unavailable'}, 404)
                bounded_range=bool(doc.get('packageRevision') or doc.get('file'))
                number = int(params.get('page', [str((doc.get('pageStart') or 1) if bounded_range else 1)])[0])
                import pypdfium2 as pdfium
                with RENDER_LOCK:
                    pdf = pdfium.PdfDocument(str(path))
                    try:
                        total = len(pdf)
                        first=(doc.get('pageStart') or 1) if bounded_range else 1
                        last=min(doc.get('pageEnd') or total,total) if bounded_range else total
                        if not first <= number <= last:
                            return self.send({'error': 'Page not found'}, 404)
                        if url.path == '/api/document-page':
                            page = pdf[number - 1]
                            bitmap = page.render(scale=1.5)
                            try:
                                image = bitmap.to_pil()
                                buffer = io.BytesIO()
                                image.save(buffer, format='PNG')
                                data = buffer.getvalue()
                            finally:
                                bitmap.close()
                                page.close()
                            return self.send(data, content_type='image/png')
                    finally:
                        pdf.close()
                query = dict(date=date, item=key, doc=document_id)
                if 'stage' in params:query=dict(stage=params['stage'][0],doc=document_id)
                if revision is not None:query['revision']=str(revision)
                links = []
                if number > first:
                    links.append(f'<a href="/document?{html.escape(urlencode(dict(query, page=number-1)))}">← Previous</a>')
                if number < last:
                    links.append(f'<a href="/document?{html.escape(urlencode(dict(query, page=number+1)))}">Next →</a>')
                image_url = '/api/document-page?' + urlencode(dict(query, page=number))
                page_html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(doc['title'])}</title><style>body{{margin:0;font:14px system-ui;background:#e4eaf0;color:#193047}}header{{position:sticky;top:0;background:white;padding:12px;border-bottom:1px solid #b5c5d5}}nav{{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin-top:8px}}a{{color:#145587}}img{{display:block;width:100%;height:auto;max-width:1300px;margin:12px auto}}input{{width:65px}}form{{display:flex;gap:8px;align-items:center}}</style></head><body><header><strong>{html.escape(doc['title'])}</strong><nav><span>Page {number} of {total} · Local archived PDF</span>{' '.join(links)}<form action="/document">{''.join(f'<input type="hidden" name="{k}" value="{html.escape(v)}">' for k,v in query.items())}<label for="page">Page</label><input id="page" name="page" type="number" min="1" max="{total}" value="{number}"><button>Go</button></form><a href="{html.escape(doc['url'])}" target="_blank" rel="noopener noreferrer">Original PDF ↗</a></nav></header><img src="{html.escape(image_url)}" alt="Rendered source PDF page {number} of {total}"></body></html>'''
                return self.send(page_html.encode(), content_type='text/html; charset=utf-8')
            if url.path.startswith('/reference/'):
                relative = unquote(url.path[len('/reference/'):])
                base = (self.server.root / 'docs').resolve()
                path = (base / relative).resolve()
                if not path.is_relative_to(base) or path.is_symlink() or not path.is_file():
                    return self.send({'error': 'Not found'}, 404)
                mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
                if path.suffix in ('.js', '.mjs'):
                    mime = 'text/javascript'
                return self.send(path.read_bytes(), content_type=mime)
            return self.send({'error': 'Not found'}, 404)
        except (ValueError, FileNotFoundError, json.JSONDecodeError):
            return self.send({'error': 'Meeting or source unavailable'}, 404)

    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin') != f'http://{self.headers.get("Host")}':
            return self.send({'error': 'Origin not allowed'}, 403)
        url = urlsplit(self.path)
        if url.path == '/api/package/file':
            if not self.authenticated():return self.send({'error':'Unlock first'},401)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=200*1024*1024:return self.send({'error':'Draft PDF limit is 200 MB per file'},413)
                params=parse_qs(url.query)
                payload=self.rfile.read(length)
                if len(payload)!=length:raise ValueError('Incomplete upload')
                return self.send(self.server.store.packages.upload(params.get('stage',[''])[0],params.get('filename',[''])[0],payload))
            except (ValueError,FileNotFoundError) as error:return self.send({'error':str(error)},400)
            except OSError:return self.send({'error':'Could not store draft PDF'},500)
        if url.path == '/api/upload':
            if not self.authenticated():
                return self.send({'error': 'Unlock the workspace first'}, 401)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_UPLOAD:
                    return self.send({'error': 'Upload a PDF no larger than 50 MB'}, 413)
                params = parse_qs(url.query)
                payload = self.rfile.read(length)
                if len(payload) != length:
                    raise ValueError('Incomplete upload')
                values = [params.get(k, [''])[0] for k in ('date', 'item', 'filename', 'title')]
                return self.send(self.server.store.upload(*values, payload))
            except (ValueError, FileNotFoundError) as error:
                return self.send({'error': str(error)}, 400)
            except OSError:
                return self.send({'error': 'Could not store the PDF. Please try again.'}, 500)
        if self.headers.get('Content-Type') != 'application/json':
            return self.send({'error': 'JSON required'}, 415)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 80000:
                return self.send({'error': 'Request too large'}, 413)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, json.JSONDecodeError):
            return self.send({'error': 'Invalid request'}, 400)
        if self.path == '/api/unlock':
            code = body.get('code')
            if not isinstance(code, str) or not secrets.compare_digest(code, self.server.access_code):
                return self.send({'error': 'Invalid access code'}, 401)
            token = secrets.token_urlsafe(32)
            self.server.sessions.add(token)
            return self.send({'ok': True}, cookie=f'agenda_session={token}; HttpOnly; SameSite=Strict; Path=/')
        if not self.authenticated():
            return self.send({'error': 'Unlock the workspace first'}, 401)
        if self.path.startswith('/api/package/'):
            try:
                flow=self.server.store.packages
                if self.path=='/api/package/start':result=flow.start(body.get('date'),body.get('title'),body.get('label',''))
                elif self.path=='/api/package/analyze':result=flow.analyze(body.get('stage',''))
                elif self.path=='/api/package/confirm':result=flow.commit(body.get('stage',''),body.get('matches'),body.get('acknowledged'))
                elif self.path=='/api/package/issue':result=flow.update_issue(body.get('date'),body.get('revision'),body.get('id'),body.get('status'),body.get('note'),body.get('doc'),body.get('page'),body.get('version'))
                elif self.path=='/api/package/add-issue':result=flow.add_issue(body.get('date'),body.get('revision'),body.get('title'),body.get('detail'),body.get('item'),body.get('version'))
                else:return self.send({'error':'Not found'},404)
                return self.send(result)
            except (ValueError,TypeError,KeyError,FileNotFoundError) as error:return self.send({'error':str(error)},400)
            except OSError:return self.send({'error':'Could not save draft review'},500)
        if self.path == '/api/logout':
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            self.server.sessions.discard(cookie['agenda_session'].value)
            return self.send({'ok': True}, cookie='agenda_session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/')
        if self.path in ('/api/create-meeting', '/api/add-item'):
            try:
                if self.path == '/api/create-meeting':
                    self.server.store.create_meeting(body.get('date'), body.get('title'))
                else:
                    self.server.store.add_item(body.get('date'), body.get('item'), body.get('title'), body.get('section'))
                return self.send({'ok': True})
            except (ValueError, FileNotFoundError) as error:
                return self.send({'error': str(error)}, 400)
            except OSError:
                return self.send({'error': 'Could not save meeting details'}, 500)
        if self.path == '/api/save':
            try:
                saved = self.server.store.save(body.get('date', ''), body.get('item', ''), body.get('review', {}))
                if saved is None:
                    return self.send({'error': 'This item changed in another tab. Reload before saving.'}, 409)
                return self.send({'saved': saved})
            except (ValueError, FileNotFoundError, TypeError):
                return self.send({'error': 'Invalid review data'}, 400)
            except OSError:
                return self.send({'error': 'Could not save. Your edits remain in the browser.'}, 500)
        return self.send({'error': 'Not found'}, 404)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = WorkspaceServer(('127.0.0.1', args.port))
    print(f'Private agenda workspace: http://127.0.0.1:{server.server_port}', flush=True)
    print(f'Access code: {server.access_code}', flush=True)
    print('Local only. Notes are saved under private-workspace/agenda-reviews; nothing is published.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()

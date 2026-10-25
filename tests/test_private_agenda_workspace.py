"""Private persistence, provenance and HTTP access boundaries."""
import hashlib
import importlib.util
import json
import io
from pathlib import Path
import tempfile
import threading
import unittest
import sys
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('agenda_workspace', ROOT/'scripts/serve_agenda_workspace.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.base = ROOT / 'tmp/private-agenda-tests'
        self.base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.base)
        self.store = module.Store(ROOT, Path(self.temp.name)/'reviews')

    def tearDown(self):
        self.assertTrue(Path(self.temp.name).resolve().is_relative_to(self.base.resolve()))
        self.temp.cleanup()

    def review(self):
        return dict(status='in-progress',notes='Private working finding <script>not executable</script>',clarifications='Need the final agreement.',reviewedDocuments=[],resolvedFlags=[],version=0)

    def pdf(self):
        from pypdf import PdfWriter
        writer=PdfWriter();writer.add_blank_page(width=300,height=400)
        out=io.BytesIO();writer.write(out);return out.getvalue()

    def test_user_created_meeting_upload_validation_dedup_and_review_reset(self):
        self.store.create_meeting('2026-11-17','Council meeting')
        self.assertIn('2026-11-17',self.store.dates())
        self.assertEqual(self.store.meeting('2026-11-17')['items'][0]['item'],'MEETING')
        self.store.add_item('2026-11-17','J.1','Example budget decision','Action')
        review=dict(self.review(),status='ready')
        self.store.save('2026-11-17','J.1',review)
        result=self.store.upload('2026-11-17','J.1','../../example.pdf','Staff report',self.pdf())
        self.assertFalse(result['duplicate']);self.assertEqual(result['document']['filename'],'example.pdf')
        self.assertTrue(self.store.document_path(result['document']).is_relative_to(Path(self.temp.name)))
        self.assertTrue(self.store.upload('2026-11-17','J.1','example.pdf','Staff report',self.pdf())['duplicate'])
        meeting=self.store.meeting('2026-11-17')
        self.assertEqual(len(next(i for i in meeting['items'] if i['item']=='J.1')['documents']),1)
        saved=self.store.read('2026-11-17')['items']['J.1']
        self.assertEqual(saved['status'],'in-progress');self.assertEqual(saved['version'],2)
        self.assertIsNone(self.store.save('2026-11-17','J.1',dict(review,version=1)))
        for payload in [b'<html>not a PDF</html>',b'%PDF-fake']:
            with self.assertRaises(ValueError):self.store.upload('2026-11-17','J.1','bad.pdf','Bad',payload)
        with self.assertRaises(ValueError):self.store.create_meeting('2026-02-31','Bad date')
        with self.assertRaises(ValueError):self.store.add_item('2026-11-17','../../bad','Bad','Action')

    def test_sources_flags_and_outcomes_are_separate_from_private_status(self):
        meeting=module.load_meeting(ROOT,'2026-10-20')
        self.assertEqual(len(meeting['items']),23)
        self.assertEqual(sum(len(i['documents']) for i in meeting['items']),78)
        rental=next(i for i in meeting['items'] if i['item']=='I.2')
        self.assertTrue(rental['flags'])
        self.assertTrue(rental['outcome'])
        self.assertEqual(self.store.read(meeting['date'])['items'],{})
        october6=module.load_meeting(ROOT,'2026-10-06')
        self.assertEqual(sum(len(i['documents']) for i in october6['items']),70)

    def test_atomic_persistence_conflicts_validation_and_source_integrity(self):
        path=ROOT/'data/council/2026-10-20-agenda.json'
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        saved=self.store.save('2026-10-20','I.2',self.review())
        self.assertEqual(saved['version'],1)
        self.assertEqual(self.store.read('2026-10-20')['items']['I.2']['notes'],self.review()['notes'])
        self.assertIsNone(self.store.save('2026-10-20','I.2',self.review()))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
        for changes in [dict(status='published'),dict(notes='x'*20001),dict(reviewedDocuments=['invented']),dict(resolvedFlags=['fake'])]:
            with self.assertRaises(ValueError):
                self.store.save('2026-10-20','I.2',dict(self.review(),**changes))
        with self.assertRaises(ValueError):module.load_meeting(ROOT,'../../secret')
        self.assertFalse(list(Path(self.temp.name).glob('*.tmp')))

    def test_http_auth_origin_exports_and_path_boundaries(self):
        server=module.WorkspaceServer(('127.0.0.1',0),ROOT,Path(self.temp.name)/'reviews')
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        opener=build_opener(ProxyHandler({}))
        def call(path,body=None,cookie=None,origin=None):
            headers={}
            if cookie:headers['Cookie']=cookie
            if body is not None:headers.update({'Content-Type':'application/json','Origin':origin or base})
            request=Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
            try:return opener.open(request)
            except HTTPError as error:return error
        try:
            self.assertEqual(call('/').status,200)
            self.assertEqual(call('/api/meetings').status,401)
            self.assertEqual(call('/reference/documents/viewer.html').status,401)
            self.assertEqual(call('/api/unlock',{'code':'wrong'}).status,401)
            self.assertEqual(call('/api/unlock',{'code':server.access_code},origin='http://evil.test').status,403)
            response=call('/api/unlock',{'code':server.access_code})
            self.assertEqual(response.status,200)
            cookie=response.headers['Set-Cookie'].split(';')[0]
            self.assertIn('HttpOnly',response.headers['Set-Cookie'])
            self.assertTrue(json.load(call('/api/meetings',cookie=cookie))['meetings'])
            self.assertEqual(call('/api/create-meeting',{'date':'2026-11-17','title':'New private meeting'},cookie=cookie).status,200)
            self.assertEqual(call('/api/add-item',{'date':'2026-11-17','item':'J.1','title':'New item','section':'Action'},cookie=cookie).status,200)
            upload_url='/api/upload?date=2026-11-17&item=J.1&filename=report.pdf&title=Report'
            self.assertEqual(call('/api/create-meeting',{'date':'2026-12-01','title':'Unauthorized'}).status,401)
            upload_request=Request(base+upload_url,data=self.pdf(),headers={'Cookie':cookie,'Origin':base,'Content-Type':'application/pdf'})
            uploaded=json.load(opener.open(upload_request))['document']
            self.assertEqual(call(uploaded['url']).status,401)
            self.assertEqual(call(uploaded['url'],cookie=cookie).read()[:5],b'%PDF-')
            meeting=module.load_meeting(ROOT,'2026-10-20')
            local=next(d for d in meeting['items'][0]['documents'] if d['localAvailable'])
            route=f'/document?date=2026-10-20&item=G.1&doc={local["id"]}'
            self.assertEqual(call(route).status,401)
            viewed=call(route,cookie=cookie)
            self.assertEqual(viewed.status,200)
            self.assertIn('Page 1 of',viewed.read().decode())
            image=call(route.replace('/document?', '/api/document-page?'),cookie=cookie)
            self.assertEqual(image.status,200)
            self.assertEqual(image.read()[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(call(route+'&page=999999',cookie=cookie).status,404)
            intake=json.load(call('/api/package/start',{'date':'2099-12-31','title':'Prepared draft','label':'Initial'},cookie=cookie))['id']
            upload_request=Request(base+f'/api/package/file?stage={intake}&filename=draft.pdf',data=self.pdf(),headers={'Cookie':cookie,'Origin':base,'Content-Type':'application/pdf'})
            self.assertEqual(opener.open(upload_request).status,200)
            analysis=json.load(call('/api/package/analyze',{'stage':intake},cookie=cookie))['analysis']
            preview=f'/document?stage={intake}&doc=packet'
            self.assertEqual(call(preview).status,401)
            self.assertEqual(call(preview,cookie=cookie).status,200)
            matches=[dict(id=d['id'],item=d['item'],confirmed=True) for d in analysis['documents']]
            committed=json.load(call('/api/package/confirm',{'stage':intake,'matches':matches,'acknowledged':True},cookie=cookie))
            self.assertEqual(committed['number'],1)
            self.assertEqual(json.load(call('/api/meeting?date=2099-12-31&revision=1',cookie=cookie))['meeting']['package']['number'],1)
            self.assertEqual(call('/api/package/add-issue',{'date':'2099-12-31','revision':1,'title':'Check attachment','detail':'Confirm correctness','item':'MEETING','version':0},cookie=cookie).status,200)
            self.assertEqual(call('/reference/../private-workspace/secret.json',cookie=cookie).status,404)
            self.assertEqual(call('/api/save',dict(date='2026-10-20',item='I.2',review=self.review()),cookie=cookie).status,200)
            self.assertEqual(call('/api/save',dict(date='2026-10-20',item='I.2',review=self.review()),cookie=cookie).status,409)
            exported=json.load(call('/api/export?date=2026-10-20',cookie=cookie))
            self.assertEqual(exported['state']['items']['I.2']['version'],1)
            self.assertEqual(call('/api/logout',{},cookie=cookie).status,200)
            self.assertEqual(call('/api/meetings',cookie=cookie).status,401)
        finally:
            server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()

"""Prepared draft -> checks -> external correction -> revised draft -> recheck."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from serve_agenda_workspace import Store
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

def packet(corrected=False, amount='100'):
    raw=io.BytesIO();c=canvas.Canvas(raw)
    c.drawString(40,780,'CITY COUNCIL DRAFT AGENDA')
    c.drawString(40,700,'Prepared draft agenda for staff attachment review before release to the public.')
    c.drawString(40,750,'G.1 Example professional services agreement 2');c.showPage()
    c.drawString(40,780,'Staff Report: Example professional services agreement')
    c.drawString(40,750,'Motion: approve agreement not to exceed $'+amount)
    c.drawString(40,720,'Attachments: Attachment A - Agreement');c.showPage()
    if corrected:
        c.drawString(40,780,'Attachment A - Agreement')
        c.drawString(40,750,'Compensation not to exceed $'+amount);c.showPage()
    c.save();reader=PdfReader(io.BytesIO(raw.getvalue()));writer=PdfWriter()
    for page in reader.pages:writer.add_page(page)
    writer.add_outline_item('Agenda',0)
    writer.add_outline_item('G.1. Staff Report - Example agreement',1)
    if corrected:writer.add_outline_item('G.1. Attachment A - Agreement',2)
    result=io.BytesIO();writer.write(result);return result.getvalue()

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.base=ROOT/'tmp/package-tests';self.base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=self.base)
        self.store=Store(ROOT,Path(self.temp.name)/'reviews');self.flow=self.store.packages;self.date='2026-12-01'
    def tearDown(self):
        self.assertTrue(Path(self.temp.name).resolve().is_relative_to(self.base.resolve()));self.temp.cleanup()
    def intake(self,data,label='Draft'):
        token=self.flow.start(self.date,'Prepared Council agenda',label)['id']
        self.flow.upload(token,'complete-draft.pdf',data)
        analysis=self.flow.analyze(token)['analysis']
        matches=[dict(id=d['id'],item=d['item'],confirmed=True) for d in analysis['documents']]
        return token,analysis,matches
    def commit(self,data,label='Draft'):
        token,a,m=self.intake(data,label)
        return self.flow.commit(token,m,True)
    def test_initial_package_checks_and_required_confirmation(self):
        token,a,m=self.intake(packet())
        self.assertEqual(a['items'][0]['item'],'G.1')
        self.assertEqual(len(a['documents']),2)
        self.assertTrue(any(i['code']=='reference' for i in a['issues']))
        with self.assertRaises(ValueError):self.flow.commit(token,m,False)
        with self.assertRaises(ValueError):self.flow.commit(token,[dict(d,confirmed=False) for d in m],True)
        r=self.flow.commit(token,m,True);self.assertEqual(r['number'],1)
        self.assertEqual(self.flow.commit(token,m,True)['number'],1)
        self.assertEqual(self.store.meeting(self.date)['package']['number'],1)
        self.assertFalse((ROOT/f'data/council/{self.date}-agenda.json').exists())
    def test_corrected_revision_carries_notes_reopens_findings_and_preserves_history(self):
        first=self.commit(packet(), 'Initial draft')
        review=dict(status='needs-clarification',notes='Keep this private note across revisions.',clarifications='Need Attachment A',reviewedDocuments=[],resolvedFlags=[],version=0,packageRevision=1)
        self.store.save(self.date,'G.1',review)
        issue=first['analysis']['issues'][0]
        self.flow.update_issue(self.date,1,issue['id'],'resolved','Reviewed the initial source; correction remains tracked.', 'packet',1,0)
        second=self.commit(packet(True,'200'),'Corrected draft')
        self.assertEqual(second['number'],2)
        carried=next(i for i in second['analysis']['issues'] if i['id']==issue['id'])
        self.assertEqual(carried['status'],'needs-recheck');self.assertIsNone(carried['resolution'])
        self.assertTrue(carried['history'])
        self.assertTrue(second['comparison']['changed']);self.assertTrue(second['comparison']['added'])
        old=self.flow.revision(self.date,1)
        self.assertEqual(old['analysis']['issues'][0]['status'],'resolved')
        self.assertEqual(self.store.read(self.date)['items']['G.1']['notes'],review['notes'])
        self.assertEqual(self.store.read(self.date)['items']['G.1']['reviewedDocuments'],[])
        self.assertTrue(self.store.meeting(self.date,1)['readOnly'])
        with self.assertRaises(ValueError):self.flow.update_issue(self.date,1,issue['id'],'open','Old edit rejected','packet',1,1)
        with self.assertRaises(ValueError):self.store.save(self.date,'G.1',review)
        final=self.flow.update_issue(self.date,2,issue['id'],'resolved','Attachment A is now present on page 3.','packet',3,0)
        self.assertTrue(all(i['status']=='resolved' for i in final['analysis']['issues']))
    def test_resolution_requires_real_current_source_and_valid_revision(self):
        r=self.commit(packet());issue=r['analysis']['issues'][0]
        for note,doc,page in [('', 'packet',1),('Claim','invented',1),('Claim','packet',999)]:
            with self.assertRaises(ValueError):self.flow.update_issue(self.date,1,issue['id'],'resolved',note,doc,page,0)
        self.flow.add_issue(self.date,1,'Amount conflict','Compare report and agreement amounts.','G.1',0)
        with self.assertRaises(ValueError):self.flow.update_issue(self.date,1,issue['id'],'resolved','Stale form','packet',1,0)
        with self.assertRaises(ValueError):self.store.save(self.date,'G.1',dict(status='ready',notes='',clarifications='',reviewedDocuments=[],resolvedFlags=[],version=0,packageRevision=1))
    def test_unchanged_and_removed_documents_and_stale_intakes(self):
        self.commit(packet(True))
        token,a,m=self.intake(packet(True),'Pending correction')
        self.commit(packet(False),'Another reviewer draft')
        with self.assertRaises(ValueError):self.flow.commit(token,m,True)
        third=self.commit(packet(False),'Same content')
        self.assertTrue(third['comparison']['unchanged'])
        second=self.flow.revision(self.date,2)
        self.assertTrue(second['comparison']['removed'])
    def test_unsearchable_pdf_is_flagged_and_ambiguous_file_remains_unmatched(self):
        writer=PdfWriter();writer.add_blank_page(width=300,height=400);out=io.BytesIO();writer.write(out)
        token=self.flow.start(self.date,'Scanned draft','Initial')['id']
        self.flow.upload(token,'agenda.pdf',out.getvalue())
        a=self.flow.analyze(token)['analysis']
        self.assertTrue(any(i['code']=='extraction' for i in a['issues']))
        self.assertTrue(any(i['code']=='text' for i in a['issues']))
        with self.assertRaises(ValueError):self.flow.stage('../../secret')

    def test_unbookmarked_packet_uses_page_references_without_claiming_attachment_completeness(self):
        reader=PdfReader(io.BytesIO(packet(True)));writer=PdfWriter()
        for page in reader.pages:writer.add_page(page)
        output=io.BytesIO();writer.write(output)
        token,a,m=self.intake(output.getvalue())
        self.assertTrue(any(d['item']=='G.1' for d in a['documents']))
        self.assertTrue(any(i['code']=='boundaries' for i in a['issues']))

    def test_corrected_item_association_is_rechecked_and_unmatched_files_stay_open(self):
        token,a,m=self.intake(packet())
        self.flow.upload(token,'g-1-attachment-a-agreement.pdf',packet(True))
        a=self.flow.analyze(token)['analysis']
        matches=[dict(id=d['id'],item=d['item'],confirmed=True) for d in a['documents']]
        r=self.flow.commit(token,matches,True)
        self.assertFalse(any(i['code']=='reference' for i in r['analysis']['issues']))

if __name__=='__main__':unittest.main()

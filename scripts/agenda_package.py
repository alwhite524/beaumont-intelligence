"""Versioned draft-package intake and evidence-backed issue rechecking."""
from copy import deepcopy
from datetime import datetime, timezone, date as Date
import hashlib
import io
import json
from pathlib import Path
import re
import secrets
from urllib.parse import urlencode
from pypdf import PdfReader, PdfWriter

ITEM = re.compile(r'^\s*([A-Z]\.\d+)\.?\s+(.+)', re.I)
def now(): return datetime.now(timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def norm(text): return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
def validate_date(value):
    Date.fromisoformat(value)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value): raise ValueError('Invalid date')
    return value
def read(path, default): return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def inspect_pdf(payload):
    if not payload.startswith(b'%PDF-') or len(payload)>200*1024*1024:
        raise ValueError('Choose an unlocked PDF no larger than 200 MB')
    try:
        pdf=PdfReader(io.BytesIO(payload), strict=True)
        if pdf.is_encrypted or not len(pdf.pages): raise ValueError()
        return pdf
    except Exception:
        raise ValueError('The PDF is damaged, empty or password-protected') from None

def fingerprint(pdf, start, end):
    # Include PDF content and image resources, not just extracted text.
    writer=PdfWriter()
    for i in range(start-1,end): writer.add_page(pdf.pages[i])
    output=io.BytesIO();writer.write(output)
    return digest(output.getvalue())

def analyze(files, storage):
    primary=files[0]
    pdf=PdfReader(storage(primary['sha256']), strict=True)
    bookmarks=[]
    def walk(rows):
        for row in rows:
            if isinstance(row,list): walk(row);continue
            title=str(row.get('/Title',''))
            if title.lower().startswith('back to'): continue
            try: page=pdf.get_destination_page_number(row)+1
            except Exception: continue
            if 1<=page<=len(pdf.pages): bookmarks.append(dict(title=title,page=page))
    walk(pdf.outline)
    first_doc=min((b['page'] for b in bookmarks if ITEM.match(b['title'])),default=min(len(pdf.pages)+1,16))
    agenda_pages=min(first_doc-1,len(pdf.pages),30)
    agenda_text='\n'.join(pdf.pages[i].extract_text() or '' for i in range(agenda_pages))
    page_refs={}
    if not any(ITEM.match(b['title']) for b in bookmarks):
        lines=agenda_text.splitlines()
        for index,line in enumerate(lines):
            match=ITEM.match(line)
            if not match:continue
            candidates=[]
            tail=re.search(r'\s(\d+)\s*$',match[2])
            if tail:candidates.append(int(tail[1]))
            for following in lines[index+1:index+4]:
                if ITEM.match(following):break
                if following.strip().isdigit():candidates.append(int(following.strip()));break
            valid=[p for p in candidates if 1<p<=len(pdf.pages)]
            if valid:page_refs.setdefault(match[1].upper(),valid[0])
        if page_refs:
            agenda_pages=min(page_refs.values())-1
            agenda_text='\n'.join(pdf.pages[i].extract_text() or '' for i in range(agenda_pages))
    items={}
    for line in agenda_text.splitlines():
        match=ITEM.match(line)
        if match:
            key=match[1].upper();title=re.sub(r'\s+\d+\s*$','',match[2]).strip()
            items.setdefault(key,dict(item=key,title=title,section='Detected agenda'))
    documents=[]
    issue_rows=[]
    def issue(code,item,title,detail):
        identity=digest(f'{code}|{item}|{title}'.encode())[:20]
        issue_rows.append(dict(id=identity,code=code,item=item,title=title,detail=detail,status='open',resolution=None,history=[]))
    documents.append(dict(id='packet',logicalKey='packet',title=primary['filename'],item='MEETING',file=primary['sha256'],pageStart=1,pageEnd=len(pdf.pages),fingerprint=primary['sha256'],confirmed=True,matchBasis='Primary complete draft package'))
    useful=sorted({(b['page'],b['title']) for b in bookmarks if ITEM.match(b['title'])})
    boundaries=sorted({b['page'] for b in bookmarks if not b['title'].lower().startswith('back to')})
    for page,title in useful:
        match=ITEM.match(title);key=match[1].upper();label=match[2].strip()
        end=min((p-1 for p in boundaries if p>page),default=len(pdf.pages))
        known=key in items
        if not known: items[key]=dict(item=key,title=label,section='Bookmark item — confirm')
        logical=f'{key}|{norm(label)}'
        doc=dict(id=digest(logical.encode())[:20],logicalKey=logical,title=label,item=key,file=primary['sha256'],pageStart=page,pageEnd=end,fingerprint=fingerprint(pdf,page,end),confirmed=False,matchBasis='PDF bookmark; confirm range and item')
        documents.append(doc)
    if not useful:
        starts=sorted(set(page_refs.values()))
        for key,page in page_refs.items():
            if key not in items:continue
            end=min((p-1 for p in starts if p>page),default=len(pdf.pages))
            logical=f'{key}|packet section'
            documents.append(dict(id=digest(logical.encode())[:20],logicalKey=logical,title='Packet section - '+items[key]['title'],item=key,file=primary['sha256'],pageStart=page,pageEnd=end,fingerprint=fingerprint(pdf,page,end),confirmed=False,matchBasis='Agenda page reference; attachment boundaries require review'))
            issue('boundaries',key,'Attachment boundaries need manual review','An agenda page reference located this item’s packet section, but no attachment bookmarks were available. Check the report and attachment boundaries on the PDF pages; individual attachment completeness has not been established.')
    for source in files[1:]:
        attached=PdfReader(storage(source['sha256']),strict=True)
        match=ITEM.match(source['filename'])
        if not match:
            alias=re.match(r'^([A-Z])[._-](\d+)[._-]',source['filename'],re.I)
            if alias:match=ITEM.match(alias[1]+'.'+alias[2]+' '+source['filename'])
        key=match[1].upper() if match and match[1].upper() in items else 'UNASSIGNED'
        logical=f'{key}|{norm(source["filename"])}'
        documents.append(dict(id=digest(logical.encode())[:20],logicalKey=logical,title=source['filename'],item=key,file=source['sha256'],pageStart=1,pageEnd=len(attached.pages),fingerprint=source['sha256'],confirmed=False,matchBasis='Filename item number' if key!='UNASSIGNED' else 'No reliable item match'))
    repeated={}
    for doc in documents:
        key=doc['logicalKey'];repeated[key]=repeated.get(key,0)+1
        if repeated[key]>1:
            doc['logicalKey']=key+f'|copy{repeated[key]}'
            doc['id']=digest(doc['logicalKey'].encode())[:20]
    if not items:
        issue('extraction','MEETING','Agenda structure needs confirmation','No numbered agenda items could be reliably extracted. This may be a scanned or unnumbered PDF. Review the full packet and confirm the inventory; completeness cannot be certified automatically.')
    if len(agenda_text.strip())<100:
        issue('text','MEETING','Agenda text unavailable or sparse','The agenda may be scanned. No OCR is applied; inspect the PDF manually or upload a searchable version before relying on automated reference checks.')
    for key in items:
        matches=[d for d in documents if d['item']==key]
        if not matches:
            issue('inventory',key,'No supporting document detected', 'No bookmark or separately uploaded file was associated with this item. Confirm whether supporting documents are required; this is not proof an attachment is missing.')
        reports=[d for d in matches if 'staff report' in norm(d['title'])]
        for report in reports:
            source=pdf if report['file']==primary['sha256'] else PdfReader(storage(report['file']),strict=True)
            text='\n'.join(source.pages[i].extract_text() or '' for i in range(report['pageStart']-1,min(report['pageEnd'],report['pageStart']+7)))
            if len(text.strip())<80:
                issue('text',key,'Staff-report text unavailable','This report has little extractable text. Reference checks require manual review or OCR outside this app.')
            refs=set(re.findall(r'\bAttachment\s+([A-Z])\b',text,re.I))
            for ref in sorted(r.upper() for r in refs):
                if not any(re.search(rf'\battachment\s+{ref.lower()}\b',norm(d['title'])) for d in matches):
                    issue('reference',key,f'Attachment {ref} reference not matched',f'The staff-report text refers to Attachment {ref}, but no detected document label matches it. Confirm the attachment label or supply the missing file.')
    for doc in documents[1:]:
        if doc['item']=='UNASSIGNED':
            issue('matching','MEETING',f'Unmatched file: {doc["title"]}','Choose its agenda item in the intake inventory before confirming the package.')
    seen={}
    for doc in documents[1:]:
        if doc['fingerprint'] in seen:
            issue('duplicate',doc['item'],f'Possible duplicate: {doc["title"]}',f'Identical document content also appears as {seen[doc["fingerprint"]]}. Confirm whether the repetition is intentional.')
        seen[doc['fingerprint']]=doc['title']
    return dict(items=list(items.values()),documents=documents,issues=issue_rows,agendaPages=agenda_pages,limits=['Checks cover detected item/document structure, PDF readability, repeated content and explicit Attachment A–Z references in detected staff reports.','No OCR, legal review, invoice audit or automatic verification of every dollar/date across attachments is performed. Staff must review document content and uncertain matches.'])

class PackageWorkflow:
    def __init__(self,store): self.store=store;self.base=store.path.parent
    def path(self,date): return self.base/'packages'/f'{validate_date(date)}.json'
    def data(self,date): return read(self.path(date),dict(date=date,revisions=[],active=0))
    def stage_path(self,token):
        if not re.fullmatch(r'[a-f0-9]{32}',token): raise ValueError('Invalid intake')
        return self.base/'intake'/f'{token}.json'
    def stage(self,token):
        stage=read(self.stage_path(token),None)
        if not stage: raise ValueError('Intake not found')
        return stage
    def blob(self,sha):
        if not re.fullmatch(r'[a-f0-9]{64}',sha):raise ValueError('Invalid document')
        return self.base/'documents'/f'{sha}.pdf'
    def start(self,date,title,label):
        validate_date(date)
        if not isinstance(title,str) or not 1<=len(title.strip())<=200:raise ValueError('Enter a meeting title')
        if not isinstance(label,str) or len(label)>200:raise ValueError('Use a revision label up to 200 characters')
        token=secrets.token_hex(16)
        with self.store.lock:
            self.store.write_json(self.stage_path(token),dict(id=token,date=date,title=title.strip(),label=label.strip(),baseRevision=self.data(date)['active'],files=[],createdAt=now()))
        return dict(id=token)
    def upload(self,token,filename,payload):
        pdf=inspect_pdf(payload);sha=digest(payload)
        filename=filename.replace('\\','/').split('/')[-1][:200]
        if not filename.lower().endswith('.pdf'):raise ValueError('Only PDFs are supported')
        with self.store.lock:
            stage=self.stage(token)
            if stage.get('committed') or any(r.get('stageId')==token for r in self.data(stage['date'])['revisions']):raise ValueError('Intake already confirmed')
            if len(stage['files'])>=100 or sum(f['bytes'] for f in stage['files'])+len(payload)>500*1024*1024:raise ValueError('Intake limit: 100 PDFs and 500 MB total')
            if any(f['sha256']==sha for f in stage['files']):return dict(duplicate=True)
            path=self.blob(sha);path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():
                temp=path.with_suffix('.tmp');temp.write_bytes(payload);temp.replace(path)
            stage['files'].append(dict(filename=filename,sha256=sha,pages=len(pdf.pages),bytes=len(payload)))
            stage.pop('analysis',None)
            self.store.write_json(self.stage_path(token),stage)
        return dict(duplicate=False)
    def analyze(self,token):
        stage=self.stage(token)
        if not stage['files']:raise ValueError('Upload the complete draft PDF first')
        analysis=analyze(stage['files'],self.blob)
        with self.store.lock:
            current=self.stage(token)
            if current['files']!=stage['files']:raise ValueError('Intake changed; analyze again')
            current['analysis']=analysis;self.store.write_json(self.stage_path(token),current)
        return dict(stage=current,analysis=analysis)
    def commit(self,token,matches,acknowledged):
        if acknowledged is not True:raise ValueError('Confirm that the detected inventory was checked')
        with self.store.lock:
            stage=self.stage(token)
            receipt=next((r for r in self.data(stage['date'])['revisions'] if r.get('stageId')==token),None)
            if receipt:return receipt
            analysis=deepcopy(stage.get('analysis'))
            if not analysis or stage.get('committed'):raise ValueError('Analyze an unconfirmed intake first')
            package=self.data(stage['date'])
            if package['active']!=stage['baseRevision']:raise ValueError('A newer revision was saved. Start a fresh intake.')
            allowed={i['item'] for i in analysis['items']}|{'MEETING','UNASSIGNED'}
            if not isinstance(matches,list):raise ValueError('Confirm document matches')
            supplied={m.get('id'):m for m in matches if isinstance(m,dict)}
            if len(supplied)!=len(analysis['documents']) or set(supplied)!={d['id'] for d in analysis['documents']}:raise ValueError('Confirm every detected document')
            for doc in analysis['documents']:
                row=supplied[doc['id']]
                if row.get('item') not in allowed or row.get('confirmed') is not True:raise ValueError('Confirm each item match, including unresolved matches')
                if doc['id']=='packet' and row['item']!='MEETING':raise ValueError('Keep the complete packet under Meeting documents')
                doc['item']=row['item'];doc['confirmed']=row['item']!='UNASSIGNED'
            # Recheck item/reference findings after staff correct the proposed associations.
            analysis['issues']=[i for i in analysis['issues'] if i['code'] not in ('inventory','reference')]
            def finding(code,key,title,detail):
                analysis['issues'].append(dict(id=digest(f'{code}|{key}|{title}'.encode())[:20],code=code,item=key,title=title,detail=detail,status='open',resolution=None,history=[]))
            for item in analysis['items']:
                key=item['item'];docs=[d for d in analysis['documents'] if d['item']==key]
                if not docs:finding('inventory',key,'No supporting document detected','Confirm whether supporting documents are required for this item; no matching document range was confirmed.')
                for report in [d for d in docs if 'staff report' in norm(d['title'])]:
                    pdf=PdfReader(self.blob(report['file']),strict=True)
                    text='\n'.join(pdf.pages[i].extract_text() or '' for i in range(report['pageStart']-1,min(report['pageEnd'],report['pageStart']+7)))
                    for ref in sorted(set(r.upper() for r in re.findall(r'\bAttachment\s+([A-Z])\b',text,re.I))):
                        if not any(re.search(rf'\battachment\s+{ref.lower()}\b',norm(d['title'])) for d in docs):finding('reference',key,f'Attachment {ref} reference not matched',f'Staff report refers to Attachment {ref}; the confirmed inventory has no matching label.')
            # A reviewer may confirm an uncertain match, but an unresolved one remains visible.
            analysis['issues']=[i for i in analysis['issues'] if i['code']!='matching']
            for doc in analysis['documents']:
                if doc['item']=='UNASSIGNED':analysis['issues'].append(dict(id=digest(('unmatched|'+doc['id']).encode())[:20],code='matching',item='MEETING',title='Unmatched document: '+doc['title'],detail='The item association remains unresolved.',status='open',resolution=None,history=[]))
            old=package['revisions'][-1] if package['revisions'] else None
            prior={d['logicalKey']:d for d in old['analysis']['documents']} if old else {}
            current={d['logicalKey']:d for d in analysis['documents']}
            comparison=dict(added=[k for k in current if k not in prior],removed=[k for k in prior if k not in current],changed=[k for k in current if k in prior and (current[k]['fingerprint']!=prior[k]['fingerprint'] or current[k]['item']!=prior[k]['item'])],unchanged=[k for k in current if k in prior and current[k]['fingerprint']==prior[k]['fingerprint'] and current[k]['item']==prior[k]['item']])
            revision=package['active']+1
            issues={i['id']:i for i in analysis['issues']}
            if old:
                for issue in old['analysis']['issues']:
                    carried=deepcopy(issue)
                    carried['history'].append(dict(revision=old['number'],status=issue['status'],resolution=issue.get('resolution')))
                    # All prior findings receive an explicit recheck, even if the check no longer triggers.
                    carried['status']='needs-recheck';carried['resolution']=None
                    carried['detail']=(issues[issue['id']]['detail'] if issue['id'] in issues else 'Earlier draft finding: '+issue['detail']+' The structural check no longer triggers in this revision’s confirmed inventory; verify the correction against the sources.')+' Recheck against this revision; no automatic closure.'
                    issues[issue['id']]=carried
            analysis['issues']=list(issues.values())
            result=dict(number=revision,stageId=token,label=stage['label'] or f'Draft {revision}',uploadedAt=now(),files=stage['files'],analysis=analysis,comparison=comparison,reviewVersion=0)
            if old: self.store.write_json(self.base/'revision-history'/stage['date']/f'r{old["number"]}.json',old)
            package['revisions'].append(result);package['active']=revision
            package['title']=stage['title']
            # Carry notes, reset document checks/status; source findings are never overwritten.
            previous=self.store.read(stage['date'])
            next_state=deepcopy(previous)
            for review in next_state.get('items',{}).values():
                review.update(status='in-progress',reviewedDocuments=[],resolvedFlags=[],version=review.get('version',0)+1)
            next_state['revision']=revision
            self.store.write_json(self.store.path/f'{stage["date"]}-r{revision}.json',next_state)
            self.store.write_json(self.path(stage['date']),package)
            stage['committed']=revision
            try:self.store.write_json(self.stage_path(token),stage)
            except OSError:pass  # The committed manifest's stageId is the authoritative receipt.
            return result
    def revision(self,date,number=None):
        data=self.data(date)
        number=data['active'] if number is None else int(number)
        result=next((r for r in data['revisions'] if r['number']==number),None)
        if not result:raise ValueError('Draft revision not found')
        return result
    def update_issue(self,date,number,issue_id,status,note,doc_id,page,version):
        with self.store.lock:
            data=self.data(date)
            if number!=data['active']:raise ValueError('Earlier revisions are read-only')
            revision=data['revisions'][-1]
            if version!=revision['reviewVersion']:raise ValueError('Findings changed in another tab. Reload before saving.')
            issue=next((i for i in revision['analysis']['issues'] if i['id']==issue_id),None)
            if not issue or status not in ('open','resolved'):raise ValueError('Invalid issue update')
            if not isinstance(note,str) or not 1<=len(note.strip())<=5000:raise ValueError('Explain the issue or resolution')
            if status=='resolved':
                doc=next((d for d in revision['analysis']['documents'] if d['id']==doc_id),None)
                if not doc or not isinstance(page,int) or not doc['pageStart']<=page<=doc['pageEnd']:raise ValueError('Choose a document and a valid source page supporting the correction')
            issue['history'].append(dict(revision=number,status=issue['status'],resolution=issue.get('resolution'),detail=issue['detail'],reviewNote=issue.get('reviewNote'),at=now()))
            issue.update(status=status,resolution=dict(note=note.strip(),doc=doc_id,page=page,at=now()) if status=='resolved' else None)
            if status=='open':issue['reviewNote']=note.strip()
            revision['reviewVersion']+=1
            self.store.write_json(self.path(date),data)
            return revision
    def add_issue(self,date,number,title,detail,item,version):
        with self.store.lock:
            data=self.data(date)
            if data['active']!=number:raise ValueError('Earlier revisions are read-only')
            revision=data['revisions'][-1]
            if version!=revision['reviewVersion']:raise ValueError('Findings changed. Reload first.')
            if not all(isinstance(v,str) and v.strip() for v in (title,detail,item)) or len(title)>200 or len(detail)>5000:raise ValueError('Enter a title and issue details')
            allowed={i['item'] for i in revision['analysis']['items']}|{'MEETING','UNASSIGNED'}
            if item not in allowed:raise ValueError('Choose a detected agenda item')
            revision['analysis']['issues'].append(dict(id=secrets.token_hex(10),code='reviewer',item=item,title=title,detail=detail,status='open',resolution=None,history=[]))
            revision['reviewVersion']+=1;self.store.write_json(self.path(date),data);return revision
    def meeting(self,date,number=None):
        revision=self.revision(date,number);analysis=revision['analysis'];data=self.data(date)
        items=[dict(item='MEETING',title='Complete draft agenda and packet',section='Meeting documents')]+analysis['items']
        if any(d['item']=='UNASSIGNED' for d in analysis['documents']):items.append(dict(item='UNASSIGNED',title='Unmatched documents — needs confirmation',section='Intake'))
        for item in items:
            key=item['item'];item.update(summary='Uploaded draft for attachment review. Correct documents outside this app, then upload a new revision.',funding='',question='',flags=[],outcome=None,documents=[])
            for d in analysis['documents']:
                if d['item']!=key:continue
                query=urlencode(dict(date=date,item=key,doc=d['id'],revision=revision['number']))
                item['documents'].append(dict(id=d['id'],title=d['title'],url='/api/uploaded?'+query,uploaded=True,sha256=d['file'],pages=d['pageEnd']-d['pageStart']+1,bytes=self.blob(d['file']).stat().st_size,pageStart=d['pageStart'],pageEnd=d['pageEnd'],localAvailable=True,packageRevision=revision['number']))
        return dict(date=date,title=data.get('title',f'{date} Draft agenda'),items=items,audit={},officialAgendaUrl=None,reviewDate=None,reviewScope='',outcomeEvidence='',package=revision,revisions=[dict(number=r['number'],label=r['label'],uploadedAt=r['uploadedAt']) for r in data['revisions']],activeRevision=data['active'],readOnly=revision['number']!=data['active'])

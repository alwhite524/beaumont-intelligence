"""Screen collected agenda/review entries and minutes for project relevance.

Source matches do not establish approval, expenditure or project status.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENTERS = {
    'stewart-park': ('Stewart Park', r'\bstewart\s+park\b|\bCIP\s*P-10\b'),
    'pennsylvania-grade-separation': ('Pennsylvania Grade Separation', r'pennsylvania.{0,100}grade\s+separation|\b2017-0?12\b'),
    'potrero-interchange': ('Potrero Interchange', r'\bpotrero\b|\b2016-0?03\b'),
    'downtown-revitalization': ('Downtown Revitalization', r'\bdowntown\b|\b500\s+grace\b|\b105\s+(?:w\.?\s*)?(?:sixth|6th)\b|\bpass\s+area\s+(?:biz|business)\b'),
    'police': ('Police', r'\bpolice\b|\bPS-0?7\b|tilden.coil'),
    'animal-control': ('Animal Control', r'\banimal\s+(?:control|shelter|services)\b|haven\s+pet|\bpetdata\b'),
    'budget': ('Budget', r'\bbudget\b|\bcapital\s+improvement\b|\bfinanc\w*\b|\baudit\w*\b|\bgrant\w*\b|\bCFD\b'),
    'land-policy': ('Land Policy', r'(?-i:\bPLUS\b)|land\s+use\s+and\s+sensitive|\btruck\s+route|\bAB\s*98\b'),
    'wrcog-restitution': ('WRCOG and Restitution', r'\bWRCOG\b|western\s+riverside\s+council|\brestitution\b'),
}


def matching(text):
    return [key for key, (_, pattern) in CENTERS.items() if re.search(pattern,text,re.I|re.S)]


def inventory():
    entries, inputs = {}, []
    for p in sorted((ROOT/'data/council').glob('*.json')):
        if not re.match(r'\d{4}-\d{2}-\d{2}',p.name):
            continue
        d=json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(d,dict):
            continue
        rows=d.get('items')
        if not isinstance(rows,list) and p.name.endswith('-agenda.json'):
            rows=[{**r,'title':r.get('itemTitle',r.get('title',''))} for r in d.get('documents',[])]
        if not isinstance(rows,list):
            continue
        day=p.name[:10]
        inputs.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),entries=len(rows)))
        for row in rows:
            key=str(row.get('item',row.get('number',row.get('item_number',''))))
            if not key:
                continue
            r=entries.setdefault((day,key),dict(date=day,item=key,title=row.get('title',''),text='',inputs=[]))
            if p.name.endswith('-agenda.json') and row.get('title'):
                r['title']=row['title']
            r['inputs'].append(p.relative_to(ROOT).as_posix())
            r['text']+=' '.join(str(row.get(k,'')) for k in ['title','description','recommendation','summary','outcome','minutesRecord','funding','evidenceLimit'])+'\n'
    project_data=ROOT/'docs/data.js'
    if project_data.exists():
        d=json.loads(project_data.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
        timeline=[r for group in d.get('timeline',[]) for r in group.get('records',[])]
        inputs.append(dict(path='docs/data.js',sha256=hashlib.sha256(project_data.read_bytes()).hexdigest(),entries=len(timeline)))
        for row in timeline:
            day,key=row['meeting_date'],row['item_number']
            r=entries.setdefault((day,key),dict(date=day,item=key,title=row['title'],text='',inputs=[]))
            r['text']+=' '.join(str(row.get(k,'')) for k in ['title','recommendation','action_taken_summary','notes'])+'\n'
            r['inputs'].append('docs/data.js')
    linked_centers={}
    review_paths=[ROOT/'data/council/recent-center-findings.json',ROOT/'data/center-recent-actions.json',*sorted((ROOT/'data/council').glob('*-center-review.json'))]
    for p in review_paths:
        if not p.exists(): continue
        d=json.loads(p.read_text(encoding='utf-8'))
        rows=d.get('findings',d.get('records',[]))
        inputs.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),entries=len(rows)))
        for row in rows:
            centers=[c for c in CENTERS if row.get('center')==c or row.get('page')==c+'.html' or c+'.html' in row.get('pages',[])]
            for item in row.get('items',[row.get('item','')]):
                linked_centers.setdefault((row.get('date'),item),set()).update(centers)
    records=[]
    for r in entries.values():
        r['centers']=sorted(set(matching(r['text']))|linked_centers.get((r['date'],r['item']),set()))
        agenda=ROOT/f'docs/briefings/{r["date"]}-sources.html'
        r['url']=f'briefings/{r["date"]}-sources.html' if agenda.exists() else 'council-meeting-sources.html?year='+r['date'][:4]
        if agenda.exists():
            anchor='item-'+r['item'].lower().replace('.','-')
            if f'id="{anchor}"' in agenda.read_text(encoding='utf-8'):
                r['url']+='#'+anchor
        r['textHash']=hashlib.sha256(r.pop('text').encode()).hexdigest()
        r['inputs']=sorted(set(r['inputs']))
        records.append(r)
    register=ROOT/'data/council/minutes-register.json'
    minutes=json.loads(register.read_text(encoding='utf-8'))['documents']
    inputs.append(dict(path=register.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(register.read_bytes()).hexdigest(),entries=len(minutes)))
    matches=[]
    for m in minutes:
        pages={}
        for n,text in enumerate(m.get('textPages',[]),1):
            for center in matching(text):
                pages.setdefault(center,[]).append(n)
        if pages:
            matches.append(dict(date=m['date'],title=m['title'],url=m['url'],kind=m['kind'],pagesByCenter=pages))
    return dict(reviewedOn='2026-11-13',scope='All dated structured Council agenda/review item arrays, the project timeline, existing center associations and collected searchable minutes. Text matches and reviewed center links screen relevance; they are not substantive verification of every attachment or current-status claims.',inputs=inputs,agendaMeetingCount=len({r['date'] for r in records}),agendaItemCount=len(records),minutesDocumentCount=len(minutes),entries=sorted(records,key=lambda r:(r['date'],r['item'])),minutesMatches=matches)


if __name__=='__main__':
    data=inventory()
    (ROOT/'data/council/project-center-inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(data['agendaMeetingCount'],'agenda dates;',data['agendaItemCount'],'unique entries;',data['minutesDocumentCount'],'minutes records screened')

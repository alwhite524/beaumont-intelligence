"""Publish four source-audited spring packets without overwriting reviewed outcomes."""
import ast
import hashlib
import json
import re
from datetime import date as Date
from html import escape
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
DATES=['2025-03-04','2025-03-18','2025-04-01','2025-04-15']
SECTIONS=['Public Hearing','Action','Consent','Presentation','Reports','Closed Session']
START='<!-- spring-2025-agendas:start -->'
END='<!-- spring-2025-agendas:end -->'

def label_for(date):
    d=Date.fromisoformat(date)
    return f'{d:%B} {d.day}, {d.year}'

def load_packet(date):
    return json.loads((ROOT/f'data/council/{date}-agenda.json').read_text(encoding='utf-8'))

def load_review(date):
    path=ROOT/f'data/council/{date}-interactive-agenda.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

def merged_items(packet,review):
    outcomes={i['item']:i for i in (review or {}).get('items',[])}
    rows=[]
    for item in packet['items']:
        row=dict(item)
        prior=outcomes.get(item['item'],{})
        row.update({k:prior[k] for k in ['outcome','page','timestampSeconds'] if k in prior})
        rows.append(row)
    present={i['item'] for i in rows}
    rows.extend(i for i in outcomes.values() if i['item'] not in present)
    return rows

def viewer(url,title):
    return '../documents/viewer.html?'+escape(urlencode(dict(url=url,title=title)),quote=True)

def build_page(date):
    packet=load_packet(date);review=load_review(date);items=merged_items(packet,review)
    label=label_for(date)
    manifest=json.loads((ROOT/'data/document-storage-manifest.json').read_text(encoding='utf-8'))
    verified={r['url'] for r in manifest['documents'] if r.get('sha256') and r.get('publication_status')!='pending-upload'}
    required=[packet['agendaUrl'],packet['packetArchiveUrl']]+[d['archiveUrl'] for d in packet['documents']]
    packet['audit']['archiveComplete']=all(url in verified for url in required)
    (ROOT/f'data/council/{date}-agenda.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    minutes=json.loads((ROOT/'data/council/minutes-register.json').read_text(encoding='utf-8'))['documents']
    minute=next((m for m in minutes if m['date']==date and m['kind']=='regular'),None)
    video=(review or {}).get('videoUrl')
    transcript=ROOT/f'docs/transcripts/{date}-city-council-transcript.txt'
    if not video and transcript.exists():
        match=re.search(r'https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]+',transcript.read_text(encoding='utf-8')[:1500])
        if match:video=match[0]
    groups=[]
    for section in SECTIONS:
        rows=[]
        for item in items:
            if item['section']!=section:continue
            key=item['item'];title=item['title'];anchor='item-'+key.lower().replace('.','-')
            docs=[d for d in packet['documents'] if d['item']==key]
            body=''
            if item.get('description'):body+='<p><strong>Published agenda description:</strong> '+escape(item['description'])+'</p>'
            if item.get('recommendation'):body+='<p><strong>Published recommendation:</strong> '+escape(item['recommendation'])+'</p>'
            if item.get('outcome'):
                body+='<p><strong>Minutes record:</strong> '+escape(item['outcome'])+'</p><p class="source-note">Official minutes · PDF page '+str(item['page'])+'. Item video timestamp not verified.</p>'
                body+=f'<button class="btn small secondary" data-minutes-page="{item["page"]}" data-title="{escape(label+" minutes · "+key,quote=True)}">View minutes page {item["page"]}</button>'
            elif minute:
                body+='<p class="source-note">Official minutes are available above; an item-specific outcome review is not included here. A recommendation is not a Council decision.</p>'
            if video:body+=f'<p><a class="text-link" href="{escape(video,quote=True)}" target="_blank" rel="noopener">Open meeting video ↗</a> · Item video timestamp not verified.</p>'
            if docs:
                body+=f'<h3>Staff reports and attachments ({len(docs)})</h3><div class="packet-documents">'
                for d in docs:
                    body+=f'<article class="packet-document"><div><strong>{escape(d["title"])}</strong><p class="source-note">Packet pages {d["packet_page_start"]}–{d["packet_page_end"]}</p><a href="{escape(d["officialUrl"],quote=True)}" target="_blank" rel="noopener">Original City source ↗</a></div><button class="btn small" data-document-url="{escape(d["archiveUrl"],quote=True)}" data-title="{escape(d["title"],quote=True)}">View document</button></article>'
                body+='</div>'
            else:body+='<p class="source-note">No attachment is listed for this entry in the audited City HTML agenda.</p>'
            rows.append(f'<details class="agenda-record" id="{anchor}" data-section="{escape(section,quote=True)}"><summary><span class="agenda-number">{escape(key)}</span><strong>{escape(title)}</strong></summary><div class="agenda-body">{body}</div></details>')
        if rows:groups.append(f'<section class="agenda-section"><h2>{escape(section)}</h2>{"".join(rows)}</section>')
    actions='<div class="status-actions">'
    if video:actions+=f'<a class="btn" href="{escape(video,quote=True)}" target="_blank" rel="noopener">Open meeting video ↗</a>'
    actions+=f'<button class="btn secondary" data-document-url="{packet["agendaUrl"]}" data-title="{escape(label+" published agenda",quote=True)}">View published agenda ({packet["agendaPageCount"]} pages)</button><button class="btn secondary" data-document-url="{packet["packetArchiveUrl"]}" data-title="{escape(label+" full agenda packet",quote=True)}">View full packet ({packet["packetPages"]:,} pages)</button>'
    if minute:actions+=f'<button class="btn secondary" data-minutes-page="1" data-title="{escape(label+" official minutes",quote=True)}">View official minutes ({len(minute["textPages"])} pages)</button>'
    if transcript.exists():actions+=f'<a class="btn secondary" href="../transcripts/reader.html?date={date}">Read collected transcript</a>'
    actions+=f'<a class="btn secondary" href="{escape(packet["officialAgendaUrl"],quote=True)}" target="_blank" rel="noopener">Official City agenda ↗</a><a class="btn secondary" href="../council-meeting-sources.html">Available meeting sources</a></div>'
    coverage=f'All {len(packet["documents"])} City-listed supporting documents matched item by item to the supplied {packet["packetPages"]:,}-page packet bookmarks. Every report and attachment is linked with its original City URL and packet page range. This verifies the source inventory, not the substantive accuracy of every page.'
    if review:coverage+=' The existing '+str(len(review['items']))+' minutes-backed entries, recorded decisions and video link are preserved; published recommendations appear separately.'
    if review:
        review['sourceCoverage']=coverage
        review['packetArchiveUrl']=packet['packetArchiveUrl']
        review['documentsSource']=f'data/council/{date}-agenda.json'
        (ROOT/f'data/council/{date}-interactive-agenda.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    nav='Item-level video timestamps have not been independently verified. Clock times printed in the minutes are not video offsets.'
    if date=='2025-03-18':nav='YouTube advertises automatic English captions, but a usable caption track was not retrieved. '+nav
    elif not video:nav+=' No meeting video is linked for this date.'
    recording=''
    if video:
        vid=video.split('v=')[1]
        recording=f'<details class="meeting-recording"><summary>Watch the collected meeting recording</summary><iframe title="{escape(label)} City Council recording" loading="lazy" src="https://www.youtube-nocookie.com/embed/{vid}" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></details>'
    tree=ast.parse((ROOT/'scripts/build_video_interactive_agendas.py').read_text(encoding='utf-8'))
    template=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='page' for t in n.targets) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and n.value.value.startswith('<!doctype'))
    template=template.replace('Historical meeting · Official minutes and video','Historical meeting · Published agenda and supporting documents')
    template=template.replace('Search COUNT recorded agenda entries, expand an item, and open its official minutes page or the meeting recording.','Search COUNT agenda entries, expand an item, and open its reports, attachments, minutes or collected video.')
    template=re.sub(r'<p class="source-note"><strong>Video navigation:</strong>.*?</p>',lambda m:'<p class="source-note"><strong>Video navigation:</strong> '+escape(nav)+'</p>',template)
    template=re.sub(r'<details class="meeting-recording">.*?</details>',lambda m:recording,template)
    template=template.replace('Search items and minutes outcomes','Search agenda items, attachments and minutes outcomes').replace('Outcomes above are attributed to the official minutes.','Published recommendations and cited minutes outcomes are separate.')
    config=json.dumps(dict(date=date,minutesUrl=minute['url'] if minute else '',label=label)).replace('<','\\u003c')
    values=dict(LABEL=escape(label),COUNT=str(len(items)),ACTIONS=actions,COVERAGE=escape(coverage),VIDEOID='',OPTIONS=''.join(f'<option>{escape(s)}</option>' for s in SECTIONS),GROUPS=''.join(groups),MINUTESURL=escape(minute['url'] if minute else packet['agendaUrl'],quote=True),CONFIG=config)
    page=re.sub(r'\b(?:'+'|'.join(values)+r')\b',lambda m:values[m[0]],template)
    version=hashlib.sha256((ROOT/'docs/briefings/video-agendas.js').read_bytes()).hexdigest()[:12]
    page=page.replace('src="video-agendas.js"',f'src="video-agendas.js?v={version}"')
    page=page.replace('</head>','<style>.packet-document{display:grid;grid-template-columns:1fr auto;gap:15px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}.packet-document p{margin:6px 0}.packet-document strong{overflow-wrap:anywhere}@media(max-width:650px){.packet-document{grid-template-columns:1fr}}</style></head>')
    (ROOT/f'docs/briefings/{date}-sources.html').write_text(page,encoding='utf-8')
    name='BI_SPRING_'+date.replace('-','_')+'_SOURCES'
    (ROOT/f'docs/briefings/{date}-sources.js').write_text('window.'+name+'='+json.dumps(packet['documents'],ensure_ascii=False)+';\n',encoding='utf-8')
    print(date,len(items),'entries;',len(packet['documents']),'supporting documents; archive verified:',packet['audit']['archiveComplete'])
    return packet,items

def build():
    packets=[build_page(date) for date in DATES]
    cards=''.join(f'<article class="card"><h3>{label_for(p["date"])}</h3><p>{p["packetPages"]:,}-page packet · {len(p["documents"])} supporting documents. Published recommendations and any reviewed minutes outcomes are shown separately.</p><a class="btn" href="briefings/{p["date"]}-sources.html">Open interactive agenda</a></article>' for p,_ in packets)
    block=START+'<section class="section compact" id="spring-2025-agendas"><div class="wrap"><h2>March and April 2025 interactive agendas</h2><p>City HTML attachment inventories matched to the supplied packets, with staff reports, attachments and original-source links.</p><div class="story-grid">'+cards+'</div></div></section>'+END
    path=ROOT/'docs/council-intelligence.html';page=path.read_text(encoding='utf-8')
    page=re.sub(re.escape(START)+'.*?'+re.escape(END),'',page,flags=re.S)
    anchor='<!-- video-agenda-records:start -->' if '<!-- video-agenda-records:start -->' in page else '<section class="section compact" id="past-briefings">'
    page=page.replace(anchor,block+anchor,1);path.write_text(page,encoding='utf-8')
    path=ROOT/'docs/search-index.js';prefix='window.BI_SEARCH_INDEX = '
    records=json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    for p,items in packets:
        url=f'briefings/{p["date"]}-sources.html'
        description=f'{p["packetPages"]:,}-page Council packet and {len(p["documents"])} City-listed supporting documents with original-source links.'
        replacement=dict(title=label_for(p['date'])+' Interactive Council Agenda',url=url,category='Council Intelligence',description=description,text=description+' '+' '.join(i['title']+' '+i.get('recommendation','')+' '+i.get('outcome','') for i in items))
        found=False
        for record in records:
            for row in record.get('value',[]) if 'value' in record else [record]:
                if row.get('url')==url:row.update(replacement);found=True
        if not found:records.append(replacement)
    path.write_text(prefix+json.dumps(records,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

if __name__=='__main__':build()

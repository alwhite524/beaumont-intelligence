"""Build minutes-backed agenda navigation for three user-supplied Council videos."""
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
DATES = ['2025-03-18', '2024-04-02', '2024-06-04']
SECTIONS = ['Public Hearing', 'Action', 'Consent', 'Presentation', 'Reports', 'Closed Session']
START = '<!-- video-agenda-records:start -->'
END = '<!-- video-agenda-records:end -->'

def build():
    meetings=[]
    for date in DATES:
        data=json.loads((ROOT/f'data/council/{date}-interactive-agenda.json').read_text(encoding='utf-8'))
        meetings.append(data)
        if (ROOT/f'data/council/{date}-agenda.json').exists():
            from build_2025_spring_agendas import build_page
            build_page(date)
            continue
        groups=[]
        for section in SECTIONS:
            rows=[]
            for item in data['items']:
                if item['section']!=section: continue
                anchor='item-'+item['item'].lower().replace('.','-')
                video=data['videoUrl']+(f'&t={item["timestampSeconds"]}s' if item.get('timestampSeconds') is not None else '')
                watch='Watch verified item time ↗' if item.get('timestampSeconds') is not None else 'Open meeting video ↗'
                rows.append(f'<details class="agenda-record" id="{anchor}" data-section="{escape(section,quote=True)}"><summary><span class="agenda-number">{escape(item["item"])}</span><strong>{escape(item["title"])}</strong></summary><div class="agenda-body"><p><strong>Minutes record:</strong> {escape(item["outcome"])}</p><p class="source-note">Official minutes · PDF page {item["page"]}. Item video timestamp not verified.</p><div class="status-actions"><a class="btn small" href="{escape(video,quote=True)}" target="_blank" rel="noopener">{watch}</a><button class="btn small secondary" data-minutes-page="{item["page"]}" data-title="{escape(data["label"],quote=True)} minutes · {escape(item["item"],quote=True)}">View minutes page {item["page"]}</button></div></div></details>')
            if rows: groups.append(f'<section class="agenda-section"><h2>{escape(section)}</h2>{"".join(rows)}</section>')
        minutes_query=urlencode(dict(url=data['minutesUrl'],title=data['label']+' Council minutes'))
        official=f'<a class="btn secondary" href="../documents/viewer.html?{escape(urlencode(dict(url=data["officialAgendaUrl"],title=data["label"]+" official agenda")),quote=True)}">Published City agenda</a>' if data.get('officialAgendaUrl') else ''
        vid=data['videoUrl'].split('v=')[1]
        label=escape(data['label'])
        page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LABEL Interactive Agenda | Beaumont Intelligence</title><meta name="description" content="Search the LABEL Council meeting agenda, read official minutes outcomes and open the supplied meeting video."><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="video-agendas.css"><script defer src="../app.js"></script></head><body><a class="skip-link" href="#main">Skip to content</a><header class="app-header"><div class="wrap header-row"><a class="brand" href="../index.html"><img class="brand-logo" src="../mbf-logo.png" alt=""><span class="brand-copy"><strong><span class="red">BEAUMONT</span> <span class="blue">INTELLIGENCE</span></strong><small>Council Intelligence</small></span></a></div></header><main id="main"><section class="section compact"><div class="wrap narrow"><div class="eyebrow">Historical meeting · Official minutes and video</div><h1>LABEL interactive Council agenda</h1><p class="lead-copy">Search COUNT recorded agenda entries, expand an item, and open its official minutes page or the meeting recording.</p>ACTIONS<p class="source-note"><strong>Source coverage:</strong> COVERAGE</p><p class="source-note"><strong>Video navigation:</strong> YouTube advertises automatic English captions, but a usable caption track was not retrieved. Item timestamps and full recording coverage have not been independently verified. Item links open the supplied video from its beginning. Clock times printed in the minutes are not video offsets. Closed-session entries report only the public minutes record.</p><details class="meeting-recording"><summary>Watch the supplied meeting recording</summary><iframe title="LABEL City Council recording" loading="lazy" src="https://www.youtube-nocookie.com/embed/VIDEOID" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></details><p>Voting sections appear in Public Hearing, Action, Consent order for browsing; this does not change the official meeting order.</p><div class="agenda-toolbar"><div><label for="agenda-search">Search items and minutes outcomes</label><input id="agenda-search" type="search" placeholder="Search topic, item number or decision…"></div><div><label for="agenda-section">Section</label><select id="agenda-section"><option value="all">All sections</option>OPTIONS</select></div></div><p id="agenda-count" role="status" aria-live="polite"></p><div id="agenda-empty" hidden>No agenda entries match. Try another term or section.</div><div id="agenda-results">GROUPS</div><p class="source-note">Source review: November 13, 2026. Outcomes above are attributed to the official minutes. A listed authorization is not evidence of payment, delivery, grant receipt or construction completion.</p><p><a href="../council-intelligence.html">Council Intelligence</a> · <a href="../council-meeting-sources.html">Available meeting sources</a></p></div></section></main><dialog class="viewer-dialog" id="viewer-dialog" aria-label="Official minutes viewer"><header><strong id="viewer-title">Official minutes</strong><button class="btn small" id="viewer-close" type="button">Close document</button></header><p class="viewer-fallback"><a id="viewer-original" href="MINUTESURL" target="_blank" rel="noopener">Open original minutes PDF ↗</a></p><iframe id="viewer-frame" title="Official minutes PDF viewer"></iframe></dialog><script type="application/json" id="agenda-config">CONFIG</script><script src="video-agendas.js" defer></script></body></html>'''
        actions=f'<div class="status-actions"><a class="btn" href="{escape(data["videoUrl"],quote=True)}" target="_blank" rel="noopener">Open meeting video ↗</a><button class="btn secondary" data-minutes-page="1" data-title="{label} official minutes">View official minutes ({data["minutesPageCount"]} pages)</button>{official}<a class="btn secondary" href="../council-meeting-sources.html">Available meeting sources</a></div>'
        config=json.dumps(dict(date=date,minutesUrl=data['minutesUrl'],label=data['label'])).replace('<','\\u003c')
        # Replace fixed template tokens in one pass so source content is never reinterpreted.
        values=dict(LABEL=label,COUNT=str(len(data['items'])),ACTIONS=actions,COVERAGE=escape(data['sourceCoverage']),VIDEOID=vid,OPTIONS=''.join(f'<option>{escape(s)}</option>' for s in SECTIONS),GROUPS=''.join(groups),MINUTESURL=escape(data['minutesUrl'],quote=True),CONFIG=config)
        page=re.sub(r'\b(?:'+ '|'.join(values)+r')\b',lambda m:values[m[0]],page)
        (ROOT/f'docs/briefings/{date}-sources.html').write_text(page,encoding='utf-8')
        print(date,len(data['items']),'minutes-backed agenda entries')
    registry_path=ROOT/'data/council/video-links.json'
    registry=json.loads(registry_path.read_text(encoding='utf-8'))
    for data in meetings:
        entry=dict(date=data['date'],url=data['videoUrl'],title=data['videoTitle'],durationSeconds=data['durationSeconds'],verificationStatus='verified-youtube-oembed-player-metadata-and-official-minutes-date',transcriptStatus='Automatic English captions advertised; retrieval unsuccessful; no verified item video timestamps')
        prior=next((v for v in registry['videos'] if v['date']==data['date']),None)
        if prior: prior.update(entry)
        else: registry['videos'].append(entry)
    registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cards=''.join(f'<article class="card"><h3>{escape(d["label"])}</h3><p>{len(d["items"])} minutes-backed agenda entries · meeting video and exact minutes-page links.</p><a class="btn" href="briefings/{d["date"]}-sources.html">Open interactive agenda</a></article>' for d in meetings if not (ROOT/f'data/council/{d["date"]}-agenda.json').exists())
    block=START+'<section class="section compact" id="video-agenda-records"><div class="wrap"><h2>More interactive meeting records</h2><p>Browse the supplied recordings with official minutes. Item timestamps and complete packet inventories remain unverified.</p><div class="story-grid">'+cards+'</div></div></section>'+END
    path=ROOT/'docs/council-intelligence.html'
    page=path.read_text(encoding='utf-8')
    page=re.sub(re.escape(START)+'.*?'+re.escape(END),'',page,flags=re.S)
    page=page.replace('<section class="section compact" id="past-briefings">',block+'<section class="section compact" id="past-briefings">',1)
    path.write_text(page,encoding='utf-8')
    path=ROOT/'docs/search-index.js';prefix='window.BI_SEARCH_INDEX = '
    records=json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
    for d in meetings:
        url=f'briefings/{d["date"]}-sources.html'
        replacement=dict(title=d['label']+' Interactive Council Agenda',url=url,category='Council Intelligence',description=f'{len(d["items"])} recorded entries with official minutes outcomes and the supplied meeting video.',text=' '.join(i['title']+' '+i['outcome'] for i in d['items']))
        found=False
        for record in records:
            for row in record.get('value',[]) if 'value' in record else [record]:
                if row.get('url')==url:row.update(replacement);found=True
        if not found:records.append(replacement)
    path.write_text(prefix+json.dumps(records,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

if __name__=='__main__':
    build()

"""Publish spring packet findings and cross-agenda project evidence routes."""
import json
import re
from html import escape as esc
from pathlib import Path
from urllib.parse import urlencode
from project_center_inventory import inventory, CENTERS

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
PAGE='project-center-record-review.html'
KEY='project-center-record-review'
FEATURED={
 'potrero-interchange':['potrero-costs','potrero-landscape','sb125-project-label'],
 'pennsylvania-grade-separation':['pennsylvania-grants','sb125-project-label','appropriations-requests'],
 'stewart-park':['stewart-latest-packet','stewart-orlp'],
 'downtown-revitalization':['downtown-parking','beaumont-nights','october-draft-minutes'],
 'police':['october-draft-minutes','appropriations-requests','police-november-equipment'],
 'budget':['budget-november-adjustments','beaumont-nights','fairway-million'],
 'land-policy':['plus-ab98','planning-follow-through'],
 'wrcog-restitution':['potrero-tumf'],
}


def publish(path,body,near_top=False):
 text=path.read_text(encoding='utf-8')
 block=f'<!-- {KEY}:start -->\n{body}\n<!-- {KEY}:end -->'
 pattern=rf'<!-- {KEY}:start -->.*?<!-- {KEY}:end -->'
 if re.search(pattern,text,re.S): text=re.sub(pattern,lambda _:block,text,flags=re.S)
 elif near_top:
  pos=text.index('</section>',text.index('<main'))+len('</section>')
  text=text[:pos]+'\n'+block+text[pos:]
 else:
  assert text.count('</main>')==1,path
  text=text.replace('</main>',block+'\n</main>')
 css=('../' if path.parent!=DOCS else '')+'autumn-2024-centers.css?v=20261113'
 if 'autumn-2024-centers.css' not in text: text=text.replace('</head>',f'<link rel="stylesheet" href="{css}"></head>')
 path.write_text(text,encoding='utf-8')


def section(title,body,id='project-record-updates'):
 return f'<section class="section compact alt" id="{id}"><div class="wrap"><h2>{esc(title)}</h2>{body}</div></section>'


def viewer(url,title,page=None):
 params=dict(url=url,title=title)
 if page: params['page']=page
 return 'documents/viewer.html?'+urlencode(params)


def card(r,packets):
 links=[]
 for item in r['items']:
  anchor='item-'+item.lower().replace('.','-')
  url=f'briefings/{r["date"]}-sources.html'
  if f'id="{anchor}"' in (DOCS/url).read_text(encoding='utf-8'): url+='#'+anchor
  links.append(f'<a href="{url}">Agenda {esc(item)} and attachments</a>')
 if r['minutesPages']:
  url=r.get('minutesUrl',f'https://documents.beaumontintelligence.com/official-documents/{r["date"]}/council-minutes.pdf')
  label=r.get('minutesLabel','Minutes')
  links.extend(f'<a href="{esc(viewer(url,label,page),quote=True)}">{esc(label)}, page {page}</a>' for page in r['minutesPages'])
 sources=[d for d in packets[r['date']]['documents'] if d['item'] in r['items']]
 if r.get('documentTitles'): sources=[d for d in sources if d['title'].strip() in r['documentTitles']]
 else:
  first={}
  for d in sources: first.setdefault(d['item'],d)
  sources=list(first.values())
 for d in sources:
  page=r.get('documentPages',{}).get(d['title'].strip())
  reference=str(d['packet_page_start']+page-1) if page else f'{d["packet_page_start"]}–{d["packet_page_end"]}'
  links.append(f'<a href="{esc(viewer(d["archiveUrl"],d["title"],page),quote=True)}">{esc(d["title"])} · packet {reference}</a>')
 for d in r.get('relatedSources',[]):
  links.append(f'<a href="{esc(viewer(d["url"],d["title"],d.get("page")),quote=True)}">{esc(d["title"])}</a>')
 return f'<article class="story-card" id="{r["id"]}"><div class="eyebrow">{r["date"]} · {esc(", ".join(r["items"]) or "Late-added emergency item")}</div><h3>{esc(r["title"])}</h3><p><strong>{esc(r["status"])}</strong></p><p>{esc(r["summary"])}</p><p><strong>Evidence limit / next records:</strong> {esc(r["limit"])}</p><p>'+ ' · '.join(links)+'</p></article>'


def main():
 data=json.loads((ROOT/'data/council/2025-spring-center-review.json').read_text(encoding='utf-8'))
 prior=json.loads((ROOT/'data/council/2024-autumn-center-review.json').read_text(encoding='utf-8'))
 rows=data['findings']
 corpus=inventory()
 (ROOT/'data/council/project-center-inventory.json').write_text(json.dumps(corpus,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 packets={day:json.loads((ROOT/f'data/council/{day}-agenda.json').read_text(encoding='utf-8')) for day in data['dates']+data['additionalDates']}
 for r in rows:
  assert set(r['items']) <= {i['item'] for i in packets[r['date']]['items']},r['id']
  for title in r.get('documentTitles',[]): assert any(d['title'].strip()==title and d['item'] in r['items'] for d in packets[r['date']]['documents']),title
  assert all((DOCS/p).exists() for p in r['pages']),r['id']
 intro=f'<p>Reviewed November 13, 2026. All four March–April 2025 packets are now included, alongside the five previously reviewed 2024 packets. This adds {len(rows)} findings, including targeted later project comparisons. Historical records, upcoming recommendations and current documented status remain separate.</p>'
 coverage=f'<p>The broader source screen covers {corpus["agendaItemCount"]} distinct agenda/review entries across {corpus["agendaMeetingCount"]} dates and {corpus["minutesDocumentCount"]} collected minutes records. Source matches identify relevance, not verified outcomes; scanned or otherwise non-searchable content requires visual review. This is not a claim to have substantively audited every attachment.</p>'
 grid='<div class="story-grid archive-review-grid">'
 pages=sorted({p for r in rows for p in r['pages']}|{c+'.html' for c in CENTERS}|{c+'-evidence.html' for c in CENTERS})
 for page in pages:
  selected=[r for r in rows if page in r['pages']]
  center=next((c for c in sorted(CENTERS,key=len,reverse=True) if page==c+'.html' or page.startswith(c+'-')),None)
  overview=page==center+'.html' if center else False
  if overview: selected=[next(r for r in rows if r['id']=='project-review-'+slug) for slug in FEATURED.get(center,[])]
  body=intro
  if selected: body+=grid+''.join(card(r,packets) for r in selected)+'</div>'
  if center:
   n=sum(center in r['centers'] for r in corpus['entries'])
   m=sum(center in r['pagesByCenter'] for r in corpus['minutesMatches'])
   body+=f'<p><a class="text-link" href="{PAGE}#center-{center}">Explore this center across collected agendas and minutes →</a> · {n} matched entries and {m} minutes records. Matches can include procedural mentions and do not establish a project action.</p>'
  if not selected: body+='<p>No additional project-specific outcome from the four spring packets is asserted here. The source inventory links the wider record for follow-up.</p>'
  body+=f'<p><a href="{PAGE}">Review all new findings and nine-packet coverage →</a></p>'
  target='budget-records.html' if page=='budget.html' else page
  publish(DOCS/target,section('Additional project records reviewed',body),near_top=overview)
 # One central source route per center, including older agenda records and minutes.
 groups=''
 directory=intro+'<div class="feature-grid">'
 for center,(label,_) in CENTERS.items():
  records=[r for r in corpus['entries'] if center in r['centers']]
  minutes=[m for m in corpus['minutesMatches'] if center in m['pagesByCenter']]
  directory+=f'<article class="feature"><h3>{esc(label)}</h3><p>{len(records)} matched agenda entries · {len(minutes)} minutes records</p><a href="{PAGE}#center-{center}">Review project evidence →</a></article>'
  selected=[r for r in rows if center+'.html' in r['pages']]
  older=[r for r in prior['findings'] if center+'.html' in r['pages']]
  body='<p><a href="'+center+'.html">Open center overview →</a></p>'
  if selected: body+='<h3>Newly reviewed findings</h3><ul>'+''.join(f'<li><a href="#{r["id"]}">{r["date"]}: {esc(r["title"])}</a></li>' for r in selected)+'</ul>'
  if older: body+='<h3>Previously reviewed 2024 findings</h3><ul>'+''.join(f'<li><a href="autumn-2024-center-review.html#{r["id"]}">{r["date"]}: {esc(r["title"])}</a></li>' for r in older)+'</ul>'
  body+='<details><summary>All matched agenda entries — source relevance only</summary><p>Includes historical, procedural and possible closed-session references. Open the source to determine disposition; a match is not approval.</p><ul>'
  body+=''.join(f'<li><a href="{esc(r["url"],quote=True)}">{r["date"]} · {esc(r["item"])}: {esc(r["title"])}</a></li>' for r in records)+'</ul></details>'
  body+='<details><summary>Matched collected minutes</summary><p>Page matches are navigation aids, not item-level decision findings. Annual compilations may cover multiple meeting dates. Word documents open in their native format.</p><ul>'
  for m in minutes:
   url=viewer(m['url'],m['title'],m['pagesByCenter'][center][0]) if m['url'].endswith('.pdf') else m['url']
   body+=f'<li><a href="{esc(url,quote=True)}">{esc(m["title"])}</a> · matching pages {", ".join(map(str,m["pagesByCenter"][center]))}</li>'
  body+='</ul></details>'
  groups+=section(label,body,'center-'+center)
 directory+='</div>'+coverage
 publish(DOCS/'intelligence-centers.html',section('Project review across the collected record',directory))
 publish(DOCS/'council-intelligence.html',section('Four more packets reviewed for the project centers',intro+f'<a class="btn" href="{PAGE}">Open project findings and source coverage →</a>'))
 table='<table><thead><tr><th>Meeting</th><th>Entries screened</th><th>Supporting documents</th><th>Review</th></tr></thead><tbody>'
 for batch in [prior,data]:
  for day in batch['dates']:
   p=json.loads((ROOT/f'data/council/{day}-agenda.json').read_text(encoding='utf-8'))
   table+=f'<tr><td><a href="briefings/{day}-sources.html">{day}</a></td><td>{len(p["items"])}</td><td>{len(p["documents"])}</td><td>{"Previously reviewed" if batch is prior else "Newly reviewed"}</td></tr>'
 table+='</tbody></table>'
 header=(DOCS/'budget-records.html').read_text(encoding='utf-8')
 header=header[header.index('<header'):header.index('</header>')+len('</header>')]
 body='<section class="section compact"><div class="wrap"><div class="eyebrow">Project evidence · November 13, 2026</div><h1>Project centers: review across collected Council records</h1>'+intro+coverage+'<h2>All nine recently added packets</h2>'+table+'<p>The March 4 late-added sewer emergency is reviewed from the minutes as an additional item outside the published packet. Later comparisons include November 17 proposals and draft October 20 minutes; neither is treated as a future meeting outcome.</p><nav aria-label="Project centers">'+' · '.join(f'<a href="#center-{c}">{esc(label)}</a>' for c,(label,_) in CENTERS.items())+'</nav></div></section>'
 body+=groups+section('New findings and primary records',grid+''.join(card(r,packets) for r in rows)+'</div>','new-findings')
 html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Project Center Record Review | Beaumont Intelligence</title><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="autumn-2024-centers.css?v=20261113"><link rel="icon" href="favicon.png"></head><body><a class="skip-link" href="#main">Skip to content</a>'+header+'<main id="main">'+body+'</main><footer class="footer"><div class="wrap"><a href="intelligence-centers.html">Intelligence Centers</a> · <a href="council-meeting-sources.html">Meeting source archive</a></div></footer><script src="app.js"></script></body></html>\n'
 (DOCS/PAGE).write_text(html,encoding='utf-8')
 for day in data['dates']+data['additionalDates']:
  selected=[r for r in rows if r['date']==day]
  body=f'<p>{len(selected)} new findings link this meeting to the project centers, with separate recommendations, recorded dispositions and evidence limits.</p><ul>'+''.join(f'<li><a href="../{PAGE}#{r["id"]}">{esc(r["title"])}</a></li>' for r in selected)+'</ul>'
  publish(DOCS/f'briefings/{day}-sources.html',section('Project center findings from this meeting',body))
 path=DOCS/'search-index.js';prefix='window.BI_SEARCH_INDEX = '
 records=json.loads(path.read_text(encoding='utf-8')[len(prefix):].strip().removesuffix(';'))
 records=[r for r in records if r.get('sourceReview')!='project-center-record-review']
 for r in rows: records.append(dict(title=r['title'],url=PAGE+'#'+r['id'],category='Intelligence Centers',description=r['summary'],text=r['date']+' '+r['status']+' '+r['summary']+' '+r['limit'],sourceReview='project-center-record-review'))
 path.write_text(prefix+json.dumps(records,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 print(f'Published {len(rows)} additional findings on {len(pages)} center pages; screened {corpus["agendaItemCount"]} entries and {corpus["minutesDocumentCount"]} minutes records.')


if __name__=='__main__': main()

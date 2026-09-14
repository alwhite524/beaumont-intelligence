"""Generate the Center and search records from the existing financial Source Register."""
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
CENTER = 'wrcog-restitution'
register = json.loads((ROOT / 'data/budget/source-register.json').read_text(encoding='utf-8'))
sources = [s for s in register['sources'] if CENTER in s.get('relatedCenters', [])]
ids = [s['sourceId'] for s in register['sources']]
assert len(ids) == len(set(ids)), 'Duplicate Source IDs'

def page(title, body):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Beaumont Intelligence</title><link rel="stylesheet" href="styles.css"><link rel="icon" href="favicon.png"></head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header class="app-header"><div class="wrap header-row"><a class="brand" href="index.html">Beaumont Intelligence</a><nav aria-label="Primary navigation"><a href="intelligence-centers.html">Intelligence Centers</a> · <a href="documents/index.html">Research Library</a> · <a href="search.html">Search</a></nav></div></header>
<main class="wrap section" id="main"><p class="eyebrow">Research active · Phase 1</p><h1>{escape(title)}</h1>
<nav aria-label="Center navigation"><a href="wrcog-restitution.html">Overview</a> · <a href="wrcog-restitution-evidence.html">Source Register</a></nav>{body}</main>
<footer class="footer"><div class="wrap">Beaumont Intelligence · Documentary evidence for independent review</div></footer></body></html>'''

overview = '''<p>This Center will document the WRCOG litigation and settlement, criminal restitution, and other recoveries involving the City of Beaumont. It is the documentary research layer that My Story can cite.</p>
<p><strong>Source verification pending.</strong> No recovery amounts or settlement terms have been verified for this Center. An empty ledger means records have not been loaded; it does not mean no money was recovered.</p>
<section><h2>Keep the financial tracks separate</h2><ol>
<li>WRCOG judgment and settlement: exposure and the terms resolving it.</li>
<li>Criminal restitution orders: amounts a court ordered.</li>
<li>Restitution collected: documented payments actually received.</li>
<li>Civil litigation recoveries: separately documented civil settlements.</li>
<li>Insurance and professional-liability settlements.</li>
<li>Other recoveries or reimbursements, including separately classified loan repayments.</li>
<li>WRCOG’s contractual share of qualifying recoveries.</li>
<li>Beaumont’s net recovery after documented allocations and costs.</li></ol>
<p><strong>Ordered does not mean paid. Gross recovery does not mean Beaumont’s net recovery.</strong> An unknown amount will remain unknown, never silently become zero.</p></section>
<section><h2>Records needed</h2><p>The amended settlement and dismissal records; audited financial statements; sentencing and restitution orders; payment and receipt records; third-party settlement agreements; allocation and legal-cost schedules.</p><p>Settlement thresholds, guarantees, and cost provisions require the actual agreement and page citations before calculation or publication.</p></section>
<section><h2>My Story evidence links</h2><p>Chapters can link to this Center now. Individual evidence references will connect a chapter or passage to permanent Source IDs, recoveries, people, organizations, cases, and timeline events as those records are registered. Narrative recollections will be labeled separately from contemporary records.</p><a href="wrcog-restitution-evidence.html">View evidence</a></section>
<section><h2>Related personnel and pension records</h2><p>The Kapanicas employment agreement, City staff correspondence, and underlying CalPERS determinations remain a separate evidence request. They are not entered as restitution or recovery. The disposition of the contemplated service-credit purchase remains unresolved pending documents.</p></section>
<section><h2>Evidence standards</h2><p>Allegations, charges, and convictions are distinct. Civil settlements are not criminal restitution. City receipts and WRCOG allocations require separate support. Later recollections are not contemporary records. Confidential mediation or closed-session discussions will not be inferred.</p></section>'''
cards = []
search = [{'title': 'WRCOG & Restitution Intelligence Center', 'url': CENTER + '.html', 'category': 'Intelligence Center', 'description': 'Research shell: settlement, restitution orders, collections, and allocation evidence awaiting verification.', 'text': 'WRCOG restitution Urban Logic Beaumont recoveries My Story evidence CalPERS', 'aliases': []}]
for s in sources:
    sid = s['sourceId']
    url = s.get('archivePath') or s.get('officialUrl')
    target = url if url and 'portal.laserfiche.com/' in url else f'documents/viewer.html?url={quote(url or "", safe="")}'
    link = f'<a href="{escape(target, quote=True)}">Open source document</a>' if url else '<p>Document not yet available.</p>'
    link += ''.join(f' <a href="{escape(path, quote=True)}">Related evidence record</a>' for path in s.get('crossLinks', []))
    cards.append(f'<article id="{escape(sid)}"><h2>{escape(sid)} · {escape(s["title"])}</h2><p>{escape(s["verificationStatus"])} · {escape(s.get("publisher", ""))}</p><p>{escape(s.get("summary", ""))}</p>{link}</article>')
    search.append({'title': s['title'], 'url': CENTER + '-evidence.html#' + sid, 'category': 'Source Document', 'description': s.get('summary', ''), 'text': f'{sid} {s["verificationStatus"]} WRCOG restitution', 'aliases': []})
evidence = '<p>This view uses the existing financial Source Register and its permanent SRC identifiers. No separate source catalog is maintained.</p>' + (''.join(cards) or '<p><strong>No source documents registered for this Center yet.</strong> Working research supplied in the handoff is not a verified source record. Documents will appear here after registration and review.</p>') + '<p><a href="budget-evidence.html">Browse existing financial evidence</a></p>'
(DOCS / (CENTER + '.html')).write_text(page('WRCOG & Restitution Intelligence Center', overview), encoding='utf-8')
(DOCS / (CENTER + '-evidence.html')).write_text(page('WRCOG & Restitution Source Register', evidence), encoding='utf-8')
search.append({'title': 'WRCOG & Restitution Source Register', 'url': CENTER + '-evidence.html', 'category': 'Intelligence Center', 'description': 'Shared financial Source Register view; source acquisition pending.', 'text': 'WRCOG restitution source documents evidence My Story', 'aliases': []})
search.append({'title': 'November 3, 2015 Interactive Council Agenda', 'url': 'briefings/2015-11-03-sources.html', 'category': 'Council Intelligence', 'description': 'Official agenda, supporting records and meeting video. Outcomes and timestamps pending.', 'text': 'WRCOG RIC 536164 Urban Futures financial report quiet zones Interwest wastewater fire IT services climate plan', 'aliases': []})
(DOCS / 'evidence-search-index.js').write_text('window.BI_EVIDENCE_SEARCH_INDEX=' + json.dumps(search, ensure_ascii=False) + ';\n', encoding='utf-8')
print(f'Built WRCOG shell with {len(sources)} registered sources.')

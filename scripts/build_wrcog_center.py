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
<main class="wrap section" id="main"><p class="eyebrow">Research active · Source verification</p><h1>{escape(title)}</h1>
<nav aria-label="Center navigation"><a href="wrcog-restitution.html">Overview</a> · <a href="wrcog-restitution-evidence.html">Source Register</a></nav>{body}</main>
<footer class="footer"><div class="wrap">Beaumont Intelligence · Documentary evidence for independent review</div></footer></body></html>'''

overview = '''<p>This Center documents the WRCOG litigation and settlement, criminal restitution, and other recoveries involving the City of Beaumont. It is the documentary research layer that My Story can cite.</p>
<p><strong>Settlement approval text reviewed; collections unverified.</strong> The May 16, 2017 packet documents the proposed amended agreement terms, and the minutes document Council approval. A fully executed agreement and records of actual receipts remain needed. An empty ledger means records have not been loaded; it does not mean no money was recovered.</p>
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
<section><h2>Records needed</h2><p>The fully executed amended settlement, referenced exhibits and dismissal records; audited financial statements; sentencing and restitution orders; payment and receipt records; third-party settlement agreements; allocation and legal-cost schedules.</p><p>The approval-copy terms below are not proof of execution, actual recovery, or payments. Reconciliation requires receipt and allocation records.</p></section>
<section><h2>My Story evidence links</h2><p>Chapters can link to this Center now. Individual evidence references will connect a chapter or passage to permanent Source IDs, recoveries, people, organizations, cases, and timeline events as those records are registered. Narrative recollections will be labeled separately from contemporary records.</p><a href="wrcog-restitution-evidence.html">View evidence</a></section>
<section><h2>Related personnel and pension records</h2><p>The Kapanicas employment agreement, City staff correspondence, and underlying CalPERS determinations remain a separate evidence request. They are not entered as restitution or recovery. The disposition of the contemplated service-credit purchase remains unresolved pending documents.</p></section>
<section><h2>Evidence standards</h2><p>Allegations, charges, and convictions are distinct. Civil settlements are not criminal restitution. City receipts and WRCOG allocations require separate support. Later recollections are not contemporary records. Confidential mediation or closed-session discussions will not be inferred.</p></section>'''
milestones = json.loads((ROOT / 'data/council/2017-minutes-intake.json').read_text(encoding='utf-8'))
timeline = ''.join(f'<li><strong>{escape(event["date"])}</strong> — {escape(event["finding"])} <a href="wrcog-restitution-evidence.html#{milestones["sourceIds"][0]}">Minutes, PDF page {event["pdfPage"]}</a></li>' for event in milestones['findings'])
overview += f'<section id="council-actions"><h2>Documented Council actions</h2><p>The supplied minutes support these actions. Approval does not itself establish execution, dismissal, or payment.</p><ol>{timeline}</ol><p><a href="council-meeting-sources.html">Browse Council videos, agendas and minutes</a></p></section>'
terms = json.loads((ROOT / 'data/wrcog-restitution/settlement-terms.json').read_text(encoding='utf-8'))
source_link = f'wrcog-restitution-evidence.html#{terms["sourceId"]}'
rows = ''.join(f'<tr><th scope="row">{escape(t["range"])}</th><td>{t["wrcogPercent"]}%</td><td>{t["beaumontPercent"]}%</td></tr>' for t in terms['allocation']['tiers'])
findings = ''.join(f'<article><h3>{escape(f["title"])}</h3><p>{escape(f["text"])}</p><p><small>Packet pages {escape(f["packetPages"])}; Item 3 extract pages {escape(f["extractPages"])}</small></p></article>' for f in terms['findings'])
overview += f'<section><h2>May 2017 settlement approval copy</h2><p>The unsigned clean agreement appears after the comparison version in Item 3. <a href="{source_link}">View source and approval-copy limitations</a>.</p><h3>Third Party Claim recovery shares</h3><p>Section 1.3.5; packet page 164, extract page 20. These brackets apply to qualifying recoveries, not the entire amount at a single rate. No actual distribution is calculated here.</p><table><thead><tr><th>Recovery bracket</th><th>WRCOG</th><th>Beaumont</th></tr></thead><tbody>{rows}</tbody></table>{findings}</section>'
overview += f'<p><a href="wrcog-restitution-evidence.html#{terms["originalAgreementSourceId"]}">View the original April agreement and exhibits</a></p>'
cards = []
search = [{'title': 'WRCOG & Restitution Intelligence Center', 'url': CENTER + '.html', 'category': 'Intelligence Center', 'description': 'Settlement approval-copy terms and documented Council actions; actual collections and allocations remain unverified.', 'text': 'WRCOG restitution Urban Logic Beaumont recoveries My Story evidence CalPERS', 'aliases': []}]
for s in sources:
    sid = s['sourceId']
    url = s.get('archivePath') or s.get('officialUrl')
    target = url if url and 'portal.laserfiche.com/' in url else f'documents/viewer.html?url={quote(url or "", safe="")}'
    link = f'<a href="{escape(target, quote=True)}">Open source document</a>' if url else '<p>Document not yet available.</p>'
    link += ''.join(f' <a href="{escape(path, quote=True)}">Related evidence record</a>' for path in s.get('crossLinks', []))
    page_refs = ', '.join(s.get('pageReferences', []))
    citation = f'<p>Page reference: {escape(page_refs)}</p>' if page_refs else ''
    limitations = f'<p><strong>Review notes:</strong> {escape(s.get("notes") or "")}</p>' if s.get('notes') else ''
    cards.append(f'<article id="{escape(sid)}"><h2>{escape(sid)} · {escape(s["title"])}</h2><p>{escape(s["verificationStatus"])} · {escape(s.get("publisher", ""))}</p><p>{escape(s.get("summary", ""))}</p>{citation}{limitations}{link}</article>')
    search.append({'title': s['title'], 'url': CENTER + '-evidence.html#' + sid, 'category': 'Source Document', 'description': s.get('summary', ''), 'text': f'{sid} {s["verificationStatus"]} WRCOG restitution', 'aliases': []})
evidence = '<p>This view uses the existing financial Source Register and its permanent SRC identifiers. No separate source catalog is maintained.</p>' + (''.join(cards) or '<p><strong>No source documents registered for this Center yet.</strong> Working research supplied in the handoff is not a verified source record. Documents will appear here after registration and review.</p>') + '<p><a href="budget-evidence.html">Browse existing financial evidence</a></p>'
(DOCS / (CENTER + '.html')).write_text(page('WRCOG & Restitution Intelligence Center', overview), encoding='utf-8')
(DOCS / (CENTER + '-evidence.html')).write_text(page('WRCOG & Restitution Source Register', evidence), encoding='utf-8')
search.append({'title': 'WRCOG settlement and membership Council actions', 'url': 'wrcog-restitution.html#council-actions', 'category': 'Timeline Event', 'description': '2017 settlement approval, WRCOG membership and TUMF actions documented in Council minutes.', 'text': 'April 4 May 16 June 20 July 18 September 5 2017 WRCOG', 'aliases': []})
search.append({'title': 'WRCOG & Restitution Source Register', 'url': CENTER + '-evidence.html', 'category': 'Intelligence Center', 'description': 'Shared financial Source Register with Council records and settlement approval materials.', 'text': 'WRCOG restitution source documents evidence My Story', 'aliases': []})
search.append({'title': 'November 3, 2015 Interactive Council Agenda', 'url': 'briefings/2015-11-03-sources.html', 'category': 'Council Intelligence', 'description': 'Official agenda, supporting records and meeting video. Outcomes and timestamps pending.', 'text': 'WRCOG RIC 536164 Urban Futures financial report quiet zones Interwest wastewater fire IT services climate plan', 'aliases': []})
(DOCS / 'evidence-search-index.js').write_text('window.BI_EVIDENCE_SEARCH_INDEX=' + json.dumps(search, ensure_ascii=False) + ';\n', encoding='utf-8')
print(f'Built WRCOG shell with {len(sources)} registered sources.')

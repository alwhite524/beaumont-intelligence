"""Build the bounded evidence corpus for Budget questions; no API credentials."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    records = []
    def add(title, text, url, kind, date='', limitation=''):
        key = hashlib.sha256((url + title + text).encode()).hexdigest()[:14]
        if not any(x['id']==key for x in records):
            records.append(dict(id=key,title=title,text=text,url=url,kind=kind,date=date,limitation=limitation))
    source = json.loads((ROOT/'data/council/recent-center-findings.json').read_text(encoding='utf-8'))
    for r in source['records']:
        if r['center']=='budget':
            add(r['title'],r['summary'],r.get('meetingRecordUrl') or 'budget-council-actions.html#'+r['id'],'Council finding',r['date'],r['limits'])
    register = json.loads((ROOT/'data/budget/source-register.json').read_text(encoding='utf-8'))
    for r in register['sources']:
        url = r.get('officialUrl')
        if url and url.startswith('https://'):
            add(r['title'],r.get('notes','') or r['title'],url,'Source metadata',r.get('documentDate') or '', 'Catalog metadata is not extracted financial evidence. Open the document before claiming an amount.')
    raw=(ROOT/'docs/documents/library-index.js').read_text(encoding='utf-8')
    library=json.loads(raw[raw.index('=')+1:].rstrip(';\n'))
    for r in library:
        # Include event source discovery without treating title-only indexing as ledger data.
        if 'beaumont nights' in r.get('title','').lower() and r['type']!='Meeting transcript':
            add(r['title'],r.get('body','')[:2200],r['url'],'Source metadata',r.get('date',''),'This indexed source does not establish three annual actual-expenditure totals.')
    add('Beaumont Nights: spending coverage', 'The collected September 1, 2026 meeting record receives the 2026 recap and directs a proposed 15-date 2027 program. Future dates and contracts remain subject to annual budgeting and contracting. This answer corpus has no reconciled three-year actual-expenditure ledger for Beaumont Nights. Do not infer spending from visits, budgets, contracts or event counts.', 'briefings/2026-09-01.html#beaumont-nights', 'Coverage note', '2026-09-01', 'A three-year total requires year-specific expense detail, payroll/overtime scope, invoices and reconciliation. Specify calendar or fiscal years and gross cost or net cost after revenues.')
    add('FY 2026–27 adopted budget', 'Council adopted the FY 2026–27 budget on June 16, 2026. Projected all-fund revenues were $168 million and planned expenditures $162.5 million. General Fund planned revenues and expenditures were each $75.6 million. The General Fund is included within all funds; do not add them. These are budget plans, not actual expenditure.', 'briefings/2026-06-16.html#budget', 'Adopted budget summary', '2026-06-16')
    add('Budget, authorization and actual spending', 'An adopted budget is spending authority. A contract ceiling is not payment. A grant application is not an award. Audited actuals differ from interim budget-to-actual reports. Compare like funds, periods and accounting bases; disclose gross versus net cost. Do not add an amendment to the amended total, or a phase authorization to its overall ceiling.', 'budget.html#financial-terms', 'Reading guide')
    data=dict(reviewedOn='2026-10-24',scope='Collected Budget Council findings, financial source metadata and selected reviewed summaries. PDFs are not read live; no complete transaction ledger is included.',records=records,chartGroups=[dict(id='fy27-plan',title='FY 2026–27 all-funds budget plan',basis='Adopted budget plan · USD · not actual spending',sourceUrl='briefings/2026-06-16.html#budget',points=[dict(label='Planned revenue',value=168000000),dict(label='Planned expenditure',value=162500000)])])
    (ROOT/'docs/budget-answers-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Budget answers: {len(records)} evidence records; 1 comparable chart group.')

if __name__=='__main__':
    main()

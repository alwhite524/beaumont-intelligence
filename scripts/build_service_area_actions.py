"""Build a dated, bounded service-action register and directory routes."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
DATE = '2026-10-24'
AREAS = {
    'public-works-mobility': 'Public Works & Mobility',
    'public-safety': 'Public Safety',
    'growth-community-development': 'Growth & Community Development',
    'economic-development': 'Economic Development',
    'parks-community-services': 'Parks & Community Services',
    'finance-government': 'Finance & City Government',
    'utilities-environment': 'Utilities & Environment',
}
CRITERIA = {
    'scope': 'Dated action and service-area scope recorded',
    'sources': 'Decision record and supporting-document route linked',
    'minutes': 'Disposition checked against reviewed City minutes',
    'finance': 'Financial authority distinguished from estimates and expenditure',
    'instruments': 'Final instruments and material discrepancies reconciled',
}

def inventory():
    records = []
    outcomes = json.loads((ROOT / 'data/council/2026-10-20-outcomes.json').read_text(encoding='utf-8'))
    selections = {
        'I.2': ('short-term-rentals', ['growth-community-development'], 'Collect the final ordinance, second-reading disposition and executed fee resolution.'),
        'I.3': ('committee-ordinances', ['finance-government'], 'Collect adopted ordinances and subsequent appointment records.'),
        'J.3': ('downtown-design', ['economic-development'], 'Collect the corrected executed STB amendment and the later construction funding decision.'),
        'J.4': ('highland-springs', ['public-works-mobility'], 'Collect Banning approval, the executed cooperative agreement and reimbursement terms.'),
        'J.5': ('tyler-renewal', ['finance-government', 'utilities-environment'], 'Collect the corrected executed amendment and reconcile variable wastewater card fees against actual billing.'),
    }
    for row in outcomes['items']:
        if row['item'] not in selections:
            continue
        key, areas, todo = selections[row['item']]
        records.append(dict(id=key, date=outcomes['date'], areas=areas, title=row['title'], summary=row['summary'], limit=row['evidenceLimit'], evidence='Transcript-based; approved October 20 minutes not collected', recordUrl='briefings/2026-10-20.html#outcome-' + row['item'], documentsUrl='briefings/2026-10-20-sources.html', nextStep=todo, checks=dict(scope=True, sources=True, minutes=False, finance=True, instruments=False)))
    findings = json.loads((ROOT / 'data/council/recent-center-findings.json').read_text(encoding='utf-8'))['records']
    row = next(r for r in findings if r['id']=='minutes-2026-10-06-signal-technology')
    records.append(dict(id='smart-signals', date=row['date'], areas=['public-works-mobility'], title=row['title'], summary=row['summary'], limit=row['limits'], evidence='Supplied City minutes reviewed', recordUrl=row['meetingRecordUrl'], documentsUrl=row['agendaUrl'], nextStep='Collect the executed construction contract and subsequent implementation records.', checks=dict(scope=True,sources=True,minutes=True,finance=True,instruments=False)))
    for key, areas, title, summary, limit, todo in [
        ('emergency-services', ['public-safety'], 'County Emergency Services Coordinator agreement', 'On August 18, Council approved a two-year County agreement at $195,000 per year, with a 40-hour on-site week. The base cost is $390,000; overtime and extraordinary costs may be separate.', 'The meeting record reports approval 5–0. This inventory has not independently checked approved minutes or the executed agreement; authorization does not establish staffing or deliverables.', 'Collect the executed agreement, deployment status, deliverables and costs above the base agreement.'),
        ('recreation-center', ['parks-community-services'], 'Community Recreation Center feasibility study', 'On August 18, Council approved RHA Community Works at $176,945, with 5% contingency for total authority of $185,793, and a $150,000 carryforward. The study includes a community survey.', 'The meeting record reports approval 5–0. This funds study and planning, not facility construction. Approved minutes and final execution have not been independently checked in this inventory.', 'Collect the executed agreement, survey and study deliverables, and the later facility/funding decision.'),
        ('transit-yard', ['public-works-mobility', 'utilities-environment'], 'Transit yard environmental findings', 'On August 18, Council adopted the Mitigated Negative Declaration and Mitigation Monitoring and Reporting Program for the Fourth Street and Viele Avenue transit yard. The briefing describes a $16.14 million project estimate.', 'Environmental approval does not establish a construction award, expenditure or completed facility. Approved minutes and final instruments have not been independently checked in this inventory.', 'Collect the adopted environmental resolution, current funding schedule and subsequent procurement disposition.'),
    ]:
        records.append(dict(id=key,date='2026-08-18',areas=areas,title=title,summary=summary,limit=limit,evidence='Collected meeting outcome and linked agenda documents',recordUrl='briefings/2026-08-18.html#'+key,documentsUrl='briefings/2026-08-18-sources.html',nextStep=todo,checks=dict(scope=True,sources=True,minutes=False,finance=True,instruments=False)))
    return records

def replace_block(path, key, block, before):
    text = path.read_text(encoding='utf-8')
    content = f'<!-- {key}:start -->\n{block}\n<!-- {key}:end -->'
    pattern = rf'<!-- {key}:start -->.*?<!-- {key}:end -->'
    if re.search(pattern,text,re.S):
        text = re.sub(pattern,lambda _:content,text,flags=re.S)
    else:
        assert before in text, path
        text = text.replace(before,content+'\n'+before,1)
    path.write_text(text,encoding='utf-8')

def main():
    records = inventory()
    data = dict(reviewedOn=DATE, scope='Nine selected August–October 2026 actions; not a complete Council or service inventory.', criteria=CRITERIA, records=records)
    (ROOT/'data/service-area-actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    esc = html.escape
    intro = '''<section class="section compact"><div class="wrap"><div class="eyebrow">Reviewed October 24, 2026</div><h1>Service-area actions and research completion</h1><p class="lead-copy">Follow selected Council decisions by civic service, with dated research checks and the next records needed.</p><p>This initial register covers nine selected August–October 2026 actions. It is not a complete inventory of Council decisions or service performance. Scores describe research readiness for each action, not construction progress, factual certainty or permission to publish.</p><nav aria-label="Service areas">'''
    intro += ' · '.join(f'<a href="#{key}">{esc(label)}</a>' for key,label in AREAS.items()) + '</nav></div></section>'
    rubric = '<section class="section compact alt" id="scoring-method"><div class="wrap"><h2>How the dated score works</h2><p>Each completed check earns 20 points; incomplete or unverified checks earn zero. Score = completed checks ÷ 5 × 100. A source route earns discovery credit without certifying every attachment. Minutes credit requires a minutes-based review. The final-instrument check remains open until corrected agreements, resolutions and material financial discrepancies are reconciled. Every score is an October 24 snapshot and must be reviewed when new evidence arrives.</p><ol>' + ''.join('<li>'+esc(v)+'</li>' for v in CRITERIA.values()) + '</ol><p>A 100% checklist would complete this bounded action review only. Payments, delivery and service outcomes require their own evidence. Cross-listed actions retain one score and count once in the nine-action total; area totals overlap.</p></div></section>'
    sections = []
    for area,label in AREAS.items():
        rows = [r for r in records if area in r['areas']]
        cards=[]
        for r in rows:
            score=sum(r['checks'].values())*20
            checks=''.join(f'<li>{esc(CRITERIA[k])}: <strong>{"Complete" if v else "Open"}</strong></li>' for k,v in r['checks'].items())
            cards.append(f'<article class="story-card" id="{area}-{r["id"]}"><div class="eyebrow">{r["date"]} · Reviewed {DATE}</div><h3>{esc(r["title"])}</h3><p><strong>Research completion: {score}% · {sum(r["checks"].values())}/5 checks</strong></p><p>{esc(r["summary"])}</p><p><strong>Evidence:</strong> {esc(r["evidence"])}</p><p><strong>Limit:</strong> {esc(r["limit"])}</p><details><summary>Scoring evidence and open checks</summary><ul>{checks}</ul></details><p><strong>Next records:</strong> {esc(r["nextStep"])}</p><a href="{esc(r["recordUrl"])}">Decision record →</a> · <a href="{esc(r["documentsUrl"])}">Agenda and supporting documents →</a></article>')
        sections.append(f'<section class="section compact" id="{area}"><div class="wrap"><h2>{esc(label)}</h2><p>{len(rows)} selected action(s) · Review dated October 24, 2026</p><div class="story-grid">'+''.join(cards)+'</div></div></section>')
    page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Service-area Actions and Research Completion | Beaumont Intelligence</title><link rel="stylesheet" href="styles.css"><link rel="icon" href="favicon.png"></head><body><a class="skip-link" href="#main">Skip to content</a><header class="app-header"><div class="wrap header-row"><a class="brand" href="index.html">Beaumont Intelligence</a><nav aria-label="Primary navigation"><a href="intelligence-centers.html">Intelligence Centers</a> · <a href="council-intelligence.html">Council Intelligence</a> · <a href="documents/index.html">Research Library</a></nav></div></header><main id="main">'+intro+rubric+''.join(sections)+'</main><footer class="footer"><div class="wrap"><a href="intelligence-centers.html">Return to service areas</a></div></footer></body></html>'
    (DOCS/'service-area-actions.html').write_text(page+'\n',encoding='utf-8')
    path=DOCS/'intelligence-centers.html'
    text=path.read_text(encoding='utf-8')
    for area,label in AREAS.items():
        marker=f'<!-- service-route-{area}:start -->'
        link=f'<a href="service-area-actions.html#{area}"><span>Recent service-area actions</span><small>Dated research scores and next records →</small></a>'
        block=marker+link+f'<!-- service-route-{area}:end -->'
        if marker in text:
            text=re.sub(rf'{re.escape(marker)}.*?<!-- service-route-{area}:end -->',lambda _:block,text,flags=re.S)
        else:
            start=text.index(f'id="{area}"')
            pos=text.index('<div class="center-links">',start)+len('<div class="center-links">')
            text=text[:pos]+block+text[pos:]
    path.write_text(text,encoding='utf-8')
    banner='<section class="section compact alt"><div class="wrap"><h2>Dated service-area action reviews</h2><p>Nine selected actions across seven civic services, reviewed October 24, 2026. See research completion checks, decision records and outstanding evidence.</p><a class="text-link" href="service-area-actions.html">Explore actions and completion scoring →</a></div></section>'
    for name in ['index.html','intelligence-centers.html','council-intelligence.html']:
        replace_block(DOCS/name,'service-action-register',banner,'</main>')
    print('Built nine unique action reviews and seven service-area routes.')

if __name__=='__main__':
    main()

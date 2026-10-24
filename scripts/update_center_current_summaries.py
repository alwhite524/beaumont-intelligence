"""Maintain dated current summaries above the centers' historical body sections."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
ANIMAL = '''<p>On August 18, 2026, Council approved 5–0 a one-year Haven Pet Center agreement for interim sheltering and a Higginson Architects agreement to design a 24-kennel City shelter in Building E at 550 E. Sixth Street. Haven intake is limited to up to 50 animals per month.</p>
<p>The Haven ceiling is $246,000, including up to $36,000 for veterinary expenses; design is capped at $71,800. With the approved 10% contingencies, combined authority is $349,580. These amounts cover interim sheltering and design, not the full cost of constructing and operating the City facility.</p>
<p>Construction, equipment, seven-day staffing, the operating budget and the transition plan still require follow-up. Staff’s roughly three-month design forecast was not an opening date. On October 20, staff discussed a future shelter bid in the capital-priority outlook; that transcript-based forecast establishes no construction award or new appropriation.</p>
<p><a href="briefings/2026-08-18.html#animal-shelter">August 18 decision and agreements →</a> · <a href="briefings/2026-08-18-sources.html">Official agenda documents →</a> · <a href="briefings/2026-10-20.html#meeting-outcomes">October 20 transcript-based update →</a></p>'''
BUDGET = '''<p>September and October Council actions add contract and purchasing authority to the adopted budget. They do not establish payments or completed projects. September 15 and October 6 findings were checked against supplied City minutes; October 20 findings remain transcript-based pending approved minutes.</p>
<div class="story-grid">
<article class="story-card"><h3>September 15: staffing agreements and signal award</h3><p>Council authorized employment agreements for Finance Director Travis Hickey and Deputy City Manager Kari Mendoza, and awarded the Oak Valley Parkway/Palm Avenue signal work for $847,090 plus $84,710 contingency, totaling $931,800.</p><a href="briefings/2026-09-15.html#minutes-review">Minutes review and supporting records →</a></article>
<article class="story-card"><h3>October 6: contract capacity and equipment</h3><p>Dekra-Lite’s aggregate ceiling rose from $260,000 to $500,000 within the approved budget, with up to 5% amendment/change-order authority; LSL accounting increased from $65,000 to $165,000. Highland Springs smart-signal work was awarded at $795,869 including contingency.</p><p>Park equipment purchases total $972,933.56, with maximum combined authority of $1,021,580.23. The final motion uses P-04 savings for the playground purchase and contingency. Trevino skate amenities received competitive procurement authority up to $120,000, with a funding-source budget adjustment required to return.</p><a href="briefings/2026-10-06.html#minutes-review">Minutes review and funding-source corrections →</a></article>
<article class="story-card"><h3>October 20: phase limits and corrected amounts</h3><p>Police-station Phase I authority is $241,727 including contingency within a $5,437,851 overall agreement ceiling subject to later phase funding and authorization. The roughly $88.5 million project estimate is not a construction award or full funding commitment.</p><p>Council approved IOA sponsorship up to $80,000 and directed downtown Phase I design; the corrected combined STB design figure is $68,850, with construction funding to return. The Tyler three-year amendment was corrected to $631,892.87; estimated variable wastewater card fees of $346,144.50 are separate. Staff requested no additional appropriation for Tyler.</p><p>G.1 warrants were approved separately after discussion of missing Treasurer signatures; later ratification is not established.</p><a href="briefings/2026-10-20.html#meeting-outcomes">Transcript-based outcomes and evidence limits →</a></article>
</div><p><a href="budget-council-actions.html#recent-council-findings">Detailed dated Council findings →</a> · <a href="budget-evidence.html">Budget evidence →</a></p>'''

def section(key, title, body):
    return f'<!-- {key}:start -->\n<section class="section compact alt" id="{key}"><div class="wrap"><div class="section-heading"><div><div class="eyebrow">Current record · updated October 24, 2026</div><h2>{title}</h2></div></div>{body}</div></section>\n<!-- {key}:end -->'

def update(name, key, title, body):
    path = DOCS / name
    text = path.read_text(encoding='utf-8')
    block = section(key, title, body)
    pattern = rf'<!-- {key}:start -->.*?<!-- {key}:end -->'
    if re.search(pattern, text, re.S):
        text = re.sub(pattern, lambda _: block, text, flags=re.S)
    else:
        # Put the update after the hero/navigation, before the existing body.
        start = re.search(r'<main\b[^>]*>', text)
        assert start, name
        end = text.index('</section>', start.end()) + len('</section>')
        text = text[:end] + '\n' + block + text[end:]
    path.write_text(text, encoding='utf-8')

def update_notes():
    # Keep the maintained research notes aligned with the visible center.
    note = '''## August 18, 2026 shelter transition — updated October 24

Council approved 5–0 a one-year Haven Pet Center interim agreement (up to 50 animals per month; $246,000 including up to $36,000 veterinary expenses) and $71,800 for Higginson Architects to design a 24-kennel City shelter in Building E at 550 E. Sixth Street. Combined authority with 10% contingencies is $349,580. Construction, equipment, staffing, operating costs and the transition plan remain follow-up items; design authorization does not establish an open City shelter.

The October 20 shelter-bid discussion is a transcript-based forecast, not an award or new appropriation. Earlier descriptions of contracted sheltering below describe the operating model preceding completion of the planned City facility.

Sources: [August 18 outcome and agreements](../briefings/2026-08-18.html#animal-shelter), [agenda documents](../briefings/2026-08-18-sources.html), [October 20 outcomes](../briefings/2026-10-20.html#meeting-outcomes).

'''
    for name in ['sheltering.md', 'contracts.md', 'budget-and-staffing.md', 'operations.md']:
        path = DOCS / 'animal-control' / name
        text = path.read_text(encoding='utf-8')
        marker = '<!-- shelter-transition-note:start -->'
        block = marker + '\n' + note + '<!-- shelter-transition-note:end -->\n'
        if marker in text:
            text = re.sub(r'<!-- shelter-transition-note:start -->.*?<!-- shelter-transition-note:end -->\n', lambda _: block, text, flags=re.S)
        else:
            first, rest = text.split('\n', 1)
            text = first + '\n\n' + block + rest
        path.write_text(text, encoding='utf-8')

def main():
    update_notes()
    for name in ['animal-control.html', 'animal-control-sheltering.html', 'animal-control-contracts.html', 'animal-control-budget-staffing.html', 'animal-control-operations.html', 'animal-control-evidence.html']:
        update(name, 'shelter-transition', 'Interim sheltering and the planned City facility', ANIMAL)
    for name in ['budget.html', 'budget-funding.html', 'budget-council-actions.html', 'budget-evidence.html', 'budget-questions.html']:
        update(name, 'recent-authorizations', 'Recent spending and contract authorizations', BUDGET)
    path = DOCS / 'animal-control.html'
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'Animal Control research is substantially complete and has\s+transitioned into a maintained Intelligence Center\.', 'Council approved interim sheltering and design for a City facility on August 18, 2026.', text)
    text = text.replace('<span class="status-kicker">Research status</span>', '<span class="status-kicker">Shelter transition</span>')
    text = text.replace('<dt>Research maturity</dt>\n              <dd>Substantially complete</dd>', '<dt>City shelter</dt>\n              <dd>Design authorized; opening not established</dd>')
    text = text.replace('<dt>Current shelter partner</dt>', '<dt>Interim shelter partner</dt>')
    path.write_text(text, encoding='utf-8')

if __name__ == '__main__':
    main()

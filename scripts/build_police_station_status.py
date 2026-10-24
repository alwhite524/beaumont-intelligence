"""Keep the dated station status consistent across the seven Police center pages."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['police', 'police-facilities', 'police-history', 'police-operations',
         'police-staffing', 'police-questions', 'police-evidence']
START = '<!-- police-station-status:start -->'
END = '<!-- police-station-status:end -->'


def render(page):
    details = ''
    if page == 'police-facilities':
        details = '''<div class="project-metrics">
<div><span>October 20 planning estimate</span><strong>$88,475,000</strong><small>PS-07 total project estimate</small></div>
<div><span>Identified current funding</span><strong>$8,462,372</strong><small>Funding reported in the staff report</small></div>
<div><span>Unfunded difference</span><strong>$80,012,628</strong><small>Estimate less identified funding</small></div></div>
<p>These are planning and funding figures, not actual spending. The $5,437,851 ceiling covers program-management and owner’s representative services; it is not the total station budget. The City Manager may execute and amend within the $241,727 Phase I authority. Each later phase must return to Council for funding and authorization before services begin.</p>
<p>The October presentation describes construction management with multiple prime contracts held by the City. This is not a general-contractor construction award. Architect/design-team procurement will return separately. Staff’s roughly two-year readiness estimate is a forecast, not an adopted completion date.</p>
<p><strong>Site descriptions need reconciliation:</strong> October materials describe the approximately 30-acre Beaumont Avenue/Cougar Way property and a conceptual roughly 10-acre facility footprint. The FY2025 annual report describes nearly six acres. These dated descriptions do not establish final approved boundaries or a final space program.</p>'''
    elif page == 'police-evidence':
        details = '''<div class="story-grid">
<article class="story-card"><h3>Agenda packet: proposal and draft</h3><p>The October 20 J.1 staff report supplies the exact project estimate and funding totals. Agreement sections 4.01 and 4.01(a) use $237,752, including an optional $18,000 modeling service. That archived draft is not proof of the final executed terms.</p><a href="briefings/2026-10-20-sources.html">Open J.1 source documents</a></article>
<article class="story-card"><h3>Meeting transcript: conditional action</h3><p>The transcript records approval of $219,752 base services plus $21,975 contingency, exclusion of the $18,000 option, and staff’s commitment to correct the agreement. Automatic captions can misidentify names and numbers; approved minutes remain needed.</p><a href="transcripts/reader.html?date=2026-10-20">Read the meeting transcript</a></article>
<article class="story-card"><h3>Records still needed</h3><p>Collect approved October 20 minutes, the corrected executed Tilden-Coil agreement, later phase authorizations, an architect award, final site and space-program records, estimate basis, environmental path, financing strategy and any bond, construction-award or payment records. Their absence here does not establish that no such record exists.</p></article></div>'''
    elif page == 'police-questions':
        details = '''<div class="story-grid">
<article class="story-card"><h3>What is authorized now?</h3><p>Phase I program-management services and contingency totaling $241,727. The optional $18,000 modeling service was excluded. Later phases need separate Council funding and authorization.</p></article>
<article class="story-card"><h3>Is construction funded or awarded?</h3><p>The reviewed records do not establish a construction award or full funding. The October project estimate is $88,475,000 with $8,462,372 identified and an $80,012,628 gap. No expenditure is inferred from authorization.</p></article>
<article class="story-card"><h3>What would resolve the remaining questions?</h3><p>Approved minutes and a corrected executed agreement would confirm the recorded motion and final scope. Final site/program, environmental, design-procurement, financing and later-phase records are still needed to establish a reliable delivery schedule.</p></article></div>'''
    elif page == 'police-history':
        details = '<p><strong>October 20, 2026 milestone:</strong> The station advanced from the earlier space-needs, concept, readiness and strategic-priority actions to a conditional program-management agreement and present Phase I authority. Earlier cost and acreage descriptions below remain historical snapshots.</p>'
    elif page in ('police-operations', 'police-staffing'):
        details = '<p>This facility-planning action does not establish new operating capacity, additional authorized positions, filled staffing, or a station opening date. Operations and staffing figures below retain their own source dates.</p>'
    return f'''{START}
<section class="section compact" id="station-status"><div class="wrap">
<div class="section-heading"><div><div class="eyebrow">Station record · October 20, 2026 · Reviewed October 24</div><h2>Phase I authorized; later phases conditional</h2></div></div>
<p>Council approved the Tilden-Coil program-management and owner’s representative agreement with a <strong>$5,437,851 overall ceiling, subject to funding and Council authorization for each phase</strong>. Present Phase I authority is <strong>$219,752 plus $21,975 contingency, totaling $241,727</strong>. The optional <strong>$18,000 modeling service was excluded</strong>. This action does not establish a construction award, full project funding or actual expenditure.</p>
<p class="source-note"><strong>Evidence status:</strong> The action is transcript-based; approved October 20 minutes and the corrected executed agreement have not been collected. The archived draft includes the excluded option and must not be treated as the final contract.</p>
{details}
<p><a href="briefings/2026-10-20.html#outcome-J.1">October 20 action and limits</a> · <a href="briefings/2026-10-20-sources.html">J.1 agenda and supporting documents</a> · <a href="https://www.youtube.com/watch?v=UVsGQHIcdkA&amp;t=6636s" target="_blank" rel="noopener">Watch discussion · 1:50:36</a> · <a href="police-facilities.html#station-status">Station funding and delivery</a> · <a href="police-evidence.html#station-status">Source gaps</a></p>
</div></section>
{END}'''


def main():
    for page in PAGES:
        path = ROOT / 'docs' / f'{page}.html'
        text = path.read_text(encoding='utf-8')
        block = render(page)
        if START in text:
            text = re.sub(re.escape(START) + '.*?' + re.escape(END), lambda _: block, text, flags=re.S)
        else:
            text = text.replace('<main id="main">', '<main id="main">\n' + block, 1)
        if page == 'police-facilities':
            text = text.replace('Current capital plan', 'Earlier capital-plan snapshot · June 2026')
            text = text.replace('New station funding remains mostly unresolved', 'June figures precede the October estimate')
            text = text.replace('The future station remains a planning priority, not an awarded construction project.', 'Phase I services authorized; later phases require funding and Council authorization.')
            text = text.replace('Strategic priority and planning record; no construction award is established by the sources reviewed here.', 'Phase I program management authorized October 20; later phases conditional. Construction award not established.')
            text = text.replace('environmental and entitlement steps, delivery method, procurement schedule, and construction authorization.', 'environmental and entitlement steps, final delivery and procurement documents, procurement schedule, and construction authorization. October’s reported multi-prime approach does not resolve these final-document gaps.')
        text = text.replace('Review the August 2025 concept record and May 2026 discussion of design funding and readiness.', 'Review the October 20 conditional Phase I authorization, alongside the earlier concept and readiness records.')
        text = text.replace('What scope, funding, site, schedule, delivery method, and Council authorization will turn a planning priority into a construction project?', 'What final scope, site, financing and later-phase authorizations will advance the October 20 Phase I action to design and construction? See the dated station answers above.')
        text = text.replace('The current City capital-project page lists New Police Station Preliminary Design as coming soon. It does not publish a schedule or design package.', 'The archived City project-listing reference describes New Police Station Preliminary Design as coming soon. The listing was not rechecked for this review and does not supersede the October 20 conditional authorization above.')
        path.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()

"""Keep Council meeting cards linked to their cataloged agenda, transcript and video."""
import re
from html import escape,unescape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def update_council_card_links(records):
    catalog={r['date']:r for r in records}
    path=ROOT/'docs/council-intelligence.html'
    html=path.read_text(encoding='utf-8')
    count=0
    def card(match):
        nonlocal count
        text=match.group(0)
        date=re.search(r'briefings/(\d{4}-\d{2}-\d{2})(?:-sources)?\.html',text)
        if not date:return text
        record=catalog.get(date[1],{})
        targets=[('Interactive agenda',record.get('interactiveAgenda')),('Search transcript',record.get('transcript')),('Watch meeting',record.get('video'))]
        if not all(href for _,href in targets):raise ValueError(f'Missing card source: {date[1]}')
        for label,href in targets[:2]:
            local=href.split('?')[0]
            if not (ROOT/'docs'/local).is_file():raise ValueError(f'Missing destination: {href}')
        actions=re.search(r'<div class="status-actions">([\s\S]*?)</div>',text)
        existing=actions[1] if actions else ''
        urls={href for _,href in targets}
        target_labels={label for label,_ in targets}
        def remove_redundant_link(anchor):
            href=re.search(r'href="([^"]+)"',anchor[0])
            label=re.sub(r'<[^>]+>','',anchor[0]).strip().strip('→↗ ')
            if (href and unescape(href[1]) in urls) or label in target_labels:
                return ''
            if href and unescape(href[1]) == f'briefings/{date[1]}.html' and label.lower().endswith('meeting record'):
                return ''
            return anchor[0]
        existing=re.sub(r'<a\b[^>]*>[\s\S]*?</a>',remove_redundant_link,existing)
        agenda_label,agenda_href=targets[0]
        agenda_link=f'<a class="btn" href="{escape(agenda_href,quote=True)}">{agenda_label}</a>'
        source_links=''.join(f'<a href="{escape(href,quote=True)}">{label}</a>' for label,href in targets[1:])
        links=agenda_link+existing+source_links
        if actions:
            text=text[:actions.start(1)]+links+text[actions.end(1):]
        else:
            # Historical cards use their interactive agenda as their primary action.
            text=re.sub(r'<a\b[^>]*href="'+re.escape(escape(targets[0][1],quote=True))+r'"[^>]*>[\s\S]*?</a>','',text)
            text=text.rsplit('</article>',1)[0]+'<div class="status-actions">'+links+'</div></article>'
        count+=1
        return text
    html=re.sub(r'<details\b[^>]*class="[^"]*council-meeting-card[^"]*"[\s\S]*?</details>|<article\b[^>]*class="card"[\s\S]*?</article>',card,html)
    path.write_text(html,encoding='utf-8',newline='\n')
    return count

if __name__=='__main__':
    from build_council_meeting_sources import meeting_records
    print(f'Updated links on {update_council_card_links(meeting_records())} Council meeting cards.')

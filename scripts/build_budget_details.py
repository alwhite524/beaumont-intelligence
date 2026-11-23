"""Build searchable, page-cited budget detail from preserved City PDFs."""
import json
import re
from pathlib import Path
from pypdf import PdfReader
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/budget-details'

def build():
    OUT.mkdir(exist_ok=True)
    sources = {}
    for year in range(2021, 2025):
        sources[year] = [(f'Adopted budget book', f'budgets/city-of-beaumont-fy{year-1}-{str(year)[-2:]}-adopted-budget.pdf')]
    sources[2026] = [(title, f'official-documents/2025-06-03/item-i-1-{num:02}.pdf') for num, title in [(7,'General Fund expenditures by department'),(6,'General Fund revenues'),(8,'Wastewater Fund'),(9,'Transit Fund'),(10,'All funds')]]
    sources[2027] = [(title, 'official-documents/2026-06-16/i-1-attachment-' + filename + '.pdf') for title, filename in [
        ('General Fund expenditures by department','e-budget-detail-report-general-fund-expenditures-by-department'),
        ('General Fund revenues','d-budget-detail-report-general-fund-revenues'),
        ('Wastewater Fund','f-budget-detail-report-wastewater-fund'),
        ('Transit Fund','g-budget-detail-report-transit'),
        ('All funds','h-budget-detail-report-all-funds')]]
    manifest=[]
    for year in range(2021,2028):
        record={'year':year,'documents':[]}
        if year == 2025:
            record['notice']='The FY 2024–25 source is linked below. Its detailed pages have not yet been preserved for searching here.'
            record['externalSource']='https://pub-beaumont.escribemeetings.com/filestream.ashx?DocumentId=4367'
        for title, source in sources.get(year, []):
            reader=PdfReader(ROOT/'docs'/source)
            bookmarks=[]
            def walk(items):
                for item in items:
                    if isinstance(item,list): walk(item)
                    else:
                        page=reader.get_destination_page_number(item)
                        if page is not None: bookmarks.append((page,item.title))
            walk(reader.outline)
            bookmarks.sort(key=lambda b:b[0])
            pages=[]
            for index,page in enumerate(reader.pages):
                text=(page.extract_text(extraction_mode='layout', layout_mode_strip_rotated=False) or '').replace('\x00','').replace('\ufffd','')
                text='\n'.join(line.rstrip() for line in text.splitlines()).strip()
                text=re.sub(r'\n{4,}','\n\n\n',text)
                section=next((name for pos,name in reversed(bookmarks) if pos<=index),title)
                departments = list(dict.fromkeys(re.findall(r'Department:\s*\d+\s*-\s*([A-Z][A-Z &/()\-]+?)(?=\s{3,}|\n|$)', text)))
                pages.append({'page':index+1,'section':section,'sections':departments or [section],'text':text})
            record['documents'].append({'title':title,'source':source,'pages':pages})
        if year==2027:
            record['book']='official-documents/2026-09-15/g-13-attachment-b-fy2026-2027-budget-book-final.pdf'
        if year in (2026,2027):
            record['notice']=f'Detailed reports from the June {3 if year==2026 else 16}, {year-1} budget-adoption agenda. Budget authority is distinct from actual spending; column labels are retained from the source.'
        (OUT/f'{year}.json').write_text(json.dumps(record,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        manifest.append({'year':year,'documents':len(record['documents']),'pages':sum(len(d['pages']) for d in record['documents'])})
        print(year,manifest[-1]['pages'],'pages')
    (OUT/'index.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')

if __name__=='__main__': build()


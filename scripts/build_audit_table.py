"""Extract current ACFR core fund statements; reconcile displayed fund columns."""
import json,re
from pathlib import Path
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
SOURCE='official-documents/2025-12-16/j-6-attachment-a-fy2025-annual-comprehensive-financial-report.pdf'
GOV1=['General Fund','Development Impact Fees (DIF)','Community Facilities District (CFD)']
GOV2=['General Capital Projects','Beaumont Financing Authority','Other Governmental Funds','Total Governmental Funds']
PROP=['Sewer Fund','Transit Fund','Total Enterprise Funds','Internal Service Fund']
CONFIG={50:('Governmental balance sheet',[250,320,405,490],GOV1),51:('Governmental balance sheet',[260,330,395,465,540],GOV2),53:('Governmental revenues and expenditures',[240,300,380,465],GOV1),54:('Governmental revenues and expenditures',[280,330,400,470,545],GOV2),59:('Proprietary net position',[280,340,410,475,540],PROP),60:('Proprietary revenues and expenses',[290,345,410,475,540],PROP)}
def clean(text):return re.sub(r'\s+',' ',text).strip()
def amount(text):
    value=re.sub(r'[\s,$]','',text)
    if value=='-':return 0
    if not re.fullmatch(r'\(?-?\d+\)?',value):raise ValueError(f'Invalid amount: {text}')
    return -int(value[1:-1]) if value.startswith('(') else int(value)
def build():
    rows=[]
    with pdfplumber.open(ROOT/'docs'/SOURCE) as pdf:
        for page_num,(statement,bounds,funds) in CONFIG.items():
            section='';pending=''
            for line in pdf.pages[page_num-1].extract_text_lines():
                if not 155<=line['top']<720:continue
                chunks=[]
                for left,right in zip([0]+bounds,bounds+[612]):
                    chars=[c for c in line['chars'] if left<=(c['x0']+c['x1'])/2<right]
                    chunks.append(clean(pdfplumber.utils.extract_text(chars, x_tolerance=1) or ''))
                label=chunks[0].rstrip(' $');values=chunks[1:len(funds)+1]
                if not any(re.search(r'\d|^-',v) for v in values):
                    if label.isupper() or label.endswith(':'):section=label.rstrip(':');pending=''
                    elif label and not label.startswith('See accompanying'):pending=label
                    continue
                if not label:raise ValueError(f'Missing label {page_num}: {line["text"]}')
                label=clean(pending+' '+label);pending=''
                for fund,value in zip(funds,values):
                    rows.append(dict(statement=statement,section=section,metric=label,fund=fund,amount=amount(value),page=page_num,isTotal=fund.startswith('Total ')))
    reconciled=0
    for statement in {r['statement'] for r in rows}:
        group=[r for r in rows if r['statement']==statement]
        for total in [r for r in group if r['isTotal']]:
            parts=[r for r in group if r['metric']==total['metric'] and r['section']==total['section'] and not r['isTotal'] and (not statement.startswith('Proprietary') or r['fund']!='Internal Service Fund')]
            expected=2 if statement.startswith('Proprietary') else 6
            if len(parts)!=expected:raise ValueError(f'Unmatched total {statement}: {total["metric"]} ({len(parts)} components)')
            if sum(r['amount'] for r in parts)!=total['amount']:raise ValueError(f'Total mismatch: {total}')
            reconciled+=1
    output=dict(fiscalYear='2024–25',source=SOURCE,officialArchive='https://beaumontca.gov/921/Audits-and-Reports',verifiedOn='2026-11-22',scope='Core governmental and proprietary fund financial statements. Totals are included as separate rows; do not add them to the component funds. The full report includes additional statements, notes, and schedules.',rows=rows,reconciledTotals=reconciled)
    (ROOT/'docs/budget-details/audit-2025-table.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'{len(rows)} audit statement values; {reconciled} totals reconciled.')
if __name__=='__main__':build()

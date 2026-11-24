"""Extract FY27 account rows and reconcile them to every printed fund/type total."""
import json,re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
BASE='official-documents/2026-06-16/'
SOURCE=BASE+'i-1-attachment-h-budget-detail-report-all-funds.pdf'
ADJUSTMENT_SOURCE='official-documents/2026-11-17/g-16-attachment-a-budget-adjustment-1st-qtr.pdf'
# Account, budget before the November adjustment, adjustment, and new budget.
GENERAL_FUND_ADJUSTMENTS={
    '100-2150-7063-0000': (250000, -53000, 197000),
    '100-1350-7068-0000': (20000, 53000, 73000),
    '100-0000-8072-0000': (49617, -31047, 18570),
}
NUMBER=r'-?[\d,]+\.\d{2}'
TAIL=re.compile(rf'\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})\s*%$')
ACCOUNT=re.compile(r'^(\d{3}-\d{4}-\d{4}-[A-Za-z0-9]{4})\s+')
def money(v): return Decimal(v.replace(',',''))
def build():
    departments={}
    with pdfplumber.open(ROOT/'docs'/BASE/'i-1-attachment-e-budget-detail-report-general-fund-expenditures-by-department.pdf') as pdf:
        for page in pdf.pages:
            for line in page.extract_text().splitlines():
                m=re.fullmatch(r'Department: (\d{4}) - (.+)',line)
                if m and 'Total:' not in line: departments[m[1]]=m[2]
    rows=[]; totals={}; sums=defaultdict(lambda:[Decimal(0),Decimal(0)]); fund=None; kind=None
    with pdfplumber.open(ROOT/'docs'/SOURCE) as pdf:
        for page_num,page in enumerate(pdf.pages,1):
            for line in page.extract_text().splitlines():
                fund_match=re.fullmatch(r'Fund: (\d{3}) - (.+)',line)
                if fund_match: fund=fund_match.groups();kind=None;continue
                if line in ('Revenue','Expense'):kind=line;continue
                account=ACCOUNT.match(line)
                if re.match(r'^[0-9]{3}-',line) and not account: raise ValueError(f'Unknown account format: {line}')
                if account:
                    amounts=TAIL.search(line)
                    if not amounts or not fund or not kind: raise ValueError(f'Unparsed row on page {page_num}: {line}')
                    code=account[1];dept=code.split('-')[1]
                    original,current=map(money,amounts.groups()[:2])
                    rows.append(dict(account=code,description=line[account.end():amounts.start()].strip(),fund=f'{fund[0]} - {fund[1]}',department=f'{dept} - {departments[dept]}' if fund[0]=='100' and dept in departments else f'{dept} - Department code',type=kind,original=float(original),current=float(current),page=page_num))
                    sums[(fund[0],kind)][0]+=original;sums[(fund[0],kind)][1]+=current
                if re.match(r'^(Revenue|Expense) Total:',line):
                    amounts=TAIL.search(line)
                    if not amounts: raise ValueError(f'Unparsed total: {line}')
                    totals[(fund[0],line.split()[0])]=list(map(money,amounts.groups()[:2]))
    if len(rows)!=len({r['account'] for r in rows}): raise ValueError('Duplicate account rows')
    if sums.keys()!=totals.keys(): raise ValueError('Missing printed fund/type totals')
    for key,values in sums.items():
        if values!=totals[key]:raise ValueError(f'Reconciliation failed {key}: {values} != {totals[key]}')
    by_account={row['account']: row for row in rows}
    for account, (before, change, after) in GENERAL_FUND_ADJUSTMENTS.items():
        row=by_account[account]
        if row['type']!='Expense' or before+change!=after:
            raise ValueError(f'Invalid General Fund adjustment for {account}')
        row.update(current=after, beforeAdjustment=before, adjustment=change)
    for row in rows:
        row['change']=round(row['current']-row['original'],2)
    data=dict(year=2027,source=SOURCE,book='official-documents/2026-09-15/g-13-attachment-b-fy2026-2027-budget-book-final.pdf',basis='Original amounts come from the June 2026 adoption report. Latest shown includes three General Fund accounts updated from the November 17 adjustment. Other accounts show the June report amounts. Totals sum the listed accounts and are not certified amended fund totals.',adjustmentSource=ADJUSTMENT_SOURCE,reconciledTotals=len(totals),rows=rows)
    (ROOT/'docs/budget-details/2027-table.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'{len(rows)} unique account rows; {len(totals)} printed fund/type totals reconciled.')
if __name__=='__main__':build()

"""Install the local Budget question preview on Budget pages only."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
BLOCK='''<!-- budget-ask:start -->
<section class="section compact budget-ask" id="ask-budget"><div class="wrap"><div class="budget-ask-panel">
<div class="eyebrow">Budget questions · evidence first</div><h2>Ask about Beaumont’s budget</h2>
<p>Ask about City spending, funds, contracts and budget decisions. Answers cite collected records, identify missing evidence and include a chart when comparable figures support one.</p>
<form><label for="budget-question">Your budget question</label><textarea id="budget-question" name="question" maxlength="1000" required placeholder="What were total expenditures on Beaumont Nights over the last three years?"></textarea><div class="budget-ask-toolbar"><button class="btn" type="submit">Find a budget answer</button><span role="status" aria-live="polite"></span></div></form>
<div class="budget-ask-examples" aria-label="Example budget questions"><button type="button" data-question="What were total expenditures on Beaumont Nights over the last three years?">Beaumont Nights costs</button><button type="button" data-question="Compare planned revenue and expenditure in the FY 2026–27 all-funds budget.">Revenue and spending plan</button><button type="button" data-question="What did Council authorize for the police station Phase I?">Police station authorization</button></div>
<p class="source-note">When AI is enabled, your question and selected budget-record excerpts are sent to OpenAI to generate an answer. Avoid personal information. If AI is unavailable, this tool shows local reviewed summaries and related records instead. Specify fiscal or calendar years for totals; budgets and contract approvals are distinct from money spent.</p>
<div class="budget-answer" aria-live="polite" hidden></div><noscript><p>Enable JavaScript to ask a question, or <a href="budget-evidence.html">browse budget evidence</a>.</p></noscript>
</div></div></section>
<!-- budget-ask:end -->'''
for name in ['budget.html','budget-questions.html']:
    p=ROOT/'docs'/name
    text=p.read_text(encoding='utf-8')
    if '<!-- budget-ask:start -->' in text:
        text=re.sub(r'<!-- budget-ask:start -->.*?<!-- budget-ask:end -->',lambda _:BLOCK,text,flags=re.S)
    else:
        pos=text.index('</section>',text.index('<main'))+len('</section>')
        text=text[:pos]+'\n'+BLOCK+text[pos:]
    if 'href="budget-ask.css"' not in text:text=text.replace('</head>','<link rel="stylesheet" href="budget-ask.css">\n</head>',1)
    if 'src="budget-ask.mjs"' not in text:text=text.replace('</body>','<script type="module" src="budget-ask.mjs"></script>\n</body>',1)
    p.write_text(text,encoding='utf-8')
print('Budget question preview installed on overview and Questions only.')

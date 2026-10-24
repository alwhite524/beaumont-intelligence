import {localAnswer, safeLink} from './budget-answer-core.mjs';
const host=document.querySelector('#ask-budget');
if (host) {
  const form=host.querySelector('form'), input=host.querySelector('textarea'), button=form.querySelector('button'), status=host.querySelector('[role="status"]'), output=host.querySelector('.budget-answer');
  let corpusPromise;
  const corpus=()=>corpusPromise ||= fetch('budget-answers-data.json').then(r=>{if(!r.ok)throw Error();return r.json();}).catch(e=>{corpusPromise=null;throw e;});
  const element=(tag,text,parent)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(parent)parent.append(e);return e;};
  function link(text,url,parent) { const href=safeLink(url);if(!href)return;const a=element('a',text,parent);a.href=href; }
  function render(answer) {
    output.replaceChildren();output.hidden=false;
    element('h3',answer.status==='clarify'?'Choose the scope':answer.status==='insufficient'?'What the records establish':answer.status==='out_of_scope'?'Ask a budget question':'Answer from collected records',output);
    element('p',answer.mode==='reviewed'?'Reviewed record summary · browser-only preview':'Records search · browser-only preview',output);
    const sources=Array.isArray(answer.sources)?answer.sources:[];
    for(const p of answer.paragraphs||[]) {
      const para=element('p',p.text,output);
      for(const id of p.sourceIds||[]) {const i=sources.findIndex(s=>s.id===id);if(i>=0){element('span',' ',para);link(`[${i+1}]`,sources[i].url,para);}}
    }
    if(answer.chart && answer.status==='answer') {
      const g=answer.chart;
      if(Array.isArray(g.points)&&g.points.length>=2&&g.points.length<=12&&g.points.every(p=>Number.isFinite(p.value)&&p.value>=0)) {
        const fig=element('figure',null,output);fig.className='budget-chart';element('figcaption',g.title,fig);element('p',g.basis,fig);
        const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(n),max=Math.max(...g.points.map(p=>p.value));
        for(const p of g.points){const row=element('div',null,fig);row.className='budget-chart-row';row.setAttribute('aria-hidden','true');element('div',`${p.label} · ${money(p.value)}`,row);const track=element('div',null,row);track.className='budget-chart-track';const bar=element('div',null,track);bar.className='budget-chart-bar';bar.style.width=`${max?p.value/max*100:0}%`;}
        const table=element('table',null,fig);element('caption','Chart data in US dollars',table);const tr=element('tr',null,element('thead',null,table));for(const label of ['Measure','Amount']){const th=element('th',label,tr);th.scope='col';}const tbody=element('tbody',null,table);for(const p of g.points){const tr=element('tr',null,tbody);element('td',p.label,tr);element('td',money(p.value),tr);}link('Chart source',g.sourceUrl,fig);
      }
    }
    if(answer.gaps?.length){element('h4','What is still needed',output);const ul=element('ul',null,output);for(const gap of answer.gaps)element('li',gap,ul);}
    if(sources.length){element('h4','Sources to review',output);const ol=element('ol',null,output);ol.className='budget-answer-sources';for(const s of sources){const li=element('li',null,ol);link(s.title,s.url,li);element('small',[s.date,s.kind].filter(Boolean).join(' · '),li);if(answer.mode==='records')element('p',s.text,li);if(s.limitation)element('small',s.limitation,li);}}
    element('p',`Evidence snapshot: ${answer.reviewedOn}. Answers cover collected records; they are not an audit or a complete transaction search.`,output);
  }
  form.addEventListener('submit',async e=>{
    e.preventDefault();const question=input.value.trim();if(!question)return;
    button.disabled=true;output.hidden=true;status.textContent='Checking collected budget records…';
    try {
      const data=await corpus();const answer=localAnswer(question,data);
      render(answer);status.textContent=answer.mode==='reviewed'?'Reviewed summary ready.':'Related records ready.';
    }catch(error){status.textContent=error.busy?'The question limit has been reached. Please try again later.':'Could not load the budget records. Please try again.';}
    finally{button.disabled=false;}
  });
  for(const example of host.querySelectorAll('[data-question]'))example.addEventListener('click',()=>{input.value=example.dataset.question;input.focus();});
}

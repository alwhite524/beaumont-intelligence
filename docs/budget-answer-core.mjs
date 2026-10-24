// Shared retrieval and answer validation. Never accept model-supplied URLs or chart values.
export const normalize = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const stop = new Set('what how why when where is are was were the a an of on in to for and over last years year total expenditures expenditure spending spent budget beaumont city much did does do can you me tell about'.split(' '));
export function retrieve(question, corpus) {
  const q = normalize(question);
  const terms = [...new Set(q.split(' ').filter(t => t.length > 2 && !stop.has(t)))];
  if (!terms.length && !/budget|revenue|expenditure|spending|fund/.test(q)) return [];
  return corpus.records.map(record => {
    const title = normalize(record.title), text = normalize(record.text);
    if (q.includes('beaumont nights') && !`${title} ${text}`.includes('beaumont nights')) return {record, score: 0};
    const hits = terms.filter(t => `${title} ${text}`.includes(t));
    let score = hits.reduce((n,t) => n + (title.includes(t) ? 6 : 2),0);
    if (!terms.length && record.kind==='Adopted budget summary') score=10;
    if (q.includes('beaumont nights') && record.kind==='Coverage note') score+=25;
    return {record,score};
  }).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,10).map(x=>x.record);
}
export function safeLink(value) {
  if (typeof value !== 'string') return null;
  if (/^https:\/\//.test(value)) return value;
  if (/^(?!\/|.*(?:\.\.|:|\\))[a-zA-Z0-9_/-]+\.html(?:[?#].*)?$/.test(value)) return value;
  return null;
}
export function validatedAnswer(raw, evidence, corpus) {
  if (!raw || !['answer','insufficient','clarify','out_of_scope'].includes(raw.status) || !Array.isArray(raw.paragraphs) || !Array.isArray(raw.gaps)) throw new Error('Invalid answer');
  const allowed=new Map(evidence.map(r=>[r.id,r]));
  const paragraphs=raw.paragraphs.slice(0,8).map(p=> {
    if (typeof p.text!=='string' || p.text.length>2500 || !Array.isArray(p.sourceIds) || p.sourceIds.some(id=>!allowed.has(id))) throw new Error('Invalid citation');
    if (raw.status==='answer' && !p.sourceIds.length) throw new Error('Uncited answer');
    return {text:p.text,sourceIds:p.sourceIds};
  });
  if (!paragraphs.length || raw.gaps.some(x=>typeof x!=='string')) throw new Error('Empty answer');
  const ids=new Set(paragraphs.flatMap(p=>p.sourceIds));
  // Only a curated homogeneous dataset can produce a chart. No model-generated numbers.
  const chart=raw.status==='answer' ? corpus.chartGroups.find(g=>g.id===raw.chartGroupId) || null : null;
  return {status:raw.status,paragraphs,gaps:raw.gaps.slice(0,8),sources:[...ids].map(id=>allowed.get(id)).filter(s=>safeLink(s.url)),chart,reviewedOn:corpus.reviewedOn};
}
export function recordsOnly(question, corpus) {
  const evidence=retrieve(question,corpus);
  const nights=normalize(question).includes('beaumont nights');
  return {status:'insufficient',paragraphs:[{text:nights ? 'The collected records do not establish a reconciled three-year total for Beaumont Nights. Choose the exact calendar or fiscal years and whether you mean gross expenditure or net City cost. Budgets, approvals and attendance estimates cannot substitute for actual spending.' : 'AI answers are not enabled here yet. These collected budget records may help answer your question; review their evidence limits before using a figure.',sourceIds:[]}],gaps:nights ? ['Needed: annual expense ledgers, invoices, payroll/overtime scope, and revenues or reimbursements for the chosen period.'] : [],sources:evidence,chart:null,reviewedOn:corpus.reviewedOn,mode:'records'};
}

export function localAnswer(question, corpus) {
  const q=normalize(question);
  const evidence=retrieve(question,corpus);
  // A reviewed comparison can be answered directly without an external model.
  if (/2026|2027|fy 27/.test(q) && /budget|plan/.test(q) && /revenue|expenditure|spending/.test(q) && !/actual|spent|beaumont nights/.test(q)) {
    const source=corpus.records.find(r=>r.kind==='Adopted budget summary');
    return {status:'answer',paragraphs:[{text:source.text,sourceIds:[source.id]}],gaps:[],sources:[source],chart:q.includes('general fund') ? null : corpus.chartGroups.find(g=>g.id==='fy27-plan'),reviewedOn:corpus.reviewedOn,mode:'reviewed'};
  }
  if(evidence[0]?.kind==='Council finding' && !/total|three years|last.*years/.test(q)) {
    const rows=evidence.filter(r=>r.kind==='Council finding').slice(0,3);
    return {status:'answer',paragraphs:rows.map(r=>({text:r.text,sourceIds:[r.id]})),gaps:rows.map(r=>r.limitation).filter(Boolean),sources:rows,chart:null,reviewedOn:corpus.reviewedOn,mode:'reviewed'};
  }
  return recordsOnly(question,corpus);
}

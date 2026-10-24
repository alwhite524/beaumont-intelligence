import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {handleBudgetRequest} from '../server/budget-api.mjs';
import worker from '../server/budget-worker.mjs';
import {retrieve} from '../docs/budget-answer-core.mjs';
import {askBudget} from '../docs/budget-transport.mjs';
const corpus=JSON.parse(fs.readFileSync(new URL('../docs/budget-answers-data.json',import.meta.url)));
const url='https://example.test/api/budget-ask';
const req=q=>new Request(url,{method:'POST',headers:{Origin:'https://example.test','Content-Type':'application/json','CF-Connecting-IP':'192.0.2.1'},body:JSON.stringify({question:q})});
const env=()=>({BUDGET_AI_ENABLED:'true',OPENAI_API_KEY:'test-only-secret',OPENAI_MODEL:'configured-model',BUDGET_RATE_LIMITER:{limit:async()=>({success:true})},BUDGET_GLOBAL_LIMITER:{limit:async()=>({success:true})}});
const q='Compare planned revenue and expenditure in the 2027 all-funds budget';
const evidence=retrieve(q,corpus);
const answer=(changes={})=>({status:'answer',paragraphs:[{text:'These figures are budget plans, not actual spending.',sourceIds:[evidence[0].id]}],gaps:[],chartGroupId:'fy27-plan',...changes});
const mock=raw=>async()=>Response.json({status:'completed',output:[{content:[{type:'output_text',text:JSON.stringify(raw)}]}]});
test('disabled and missing configuration never call OpenAI',async()=>{
 let called=false;const opts={corpus,fetchAPI:async()=>{called=true;throw Error();}};
 assert.deepEqual(await (await handleBudgetRequest(new Request(url),{})).json(),{enabled:false});
 assert.equal((await handleBudgetRequest(req(q),{},opts)).status,503);
 const e=env();delete e.BUDGET_RATE_LIMITER;
 assert.equal((await handleBudgetRequest(req(q),e,opts)).status,503);assert.equal(called,false);
});
test('origin, input size, method, and quotas are enforced before provider call',async()=>{
 const bad=new Request(url,{method:'POST',headers:{Origin:'https://other.test','Content-Type':'application/json'},body:'{}'});
 assert.equal((await handleBudgetRequest(bad,env(),{corpus})).status,403);
 assert.equal((await handleBudgetRequest(new Request(url,{method:'DELETE'}),env(),{corpus})).status,405);
 assert.equal((await handleBudgetRequest(req('x'.repeat(6000)),env(),{corpus})).status,400);
 assert.equal((await handleBudgetRequest(req('tiny'),env(),{corpus})).status,400);
 for(const binding of ['BUDGET_RATE_LIMITER','BUDGET_GLOBAL_LIMITER']){
  const e=env();e[binding].limit=async()=>({success:false});assert.equal((await handleBudgetRequest(req(q),e,{corpus})).status,429);
 }
});
test('provider receives only bounded server-selected evidence and server-held key',async()=>{
 const response=await handleBudgetRequest(req(q),env(),{corpus,fetchAPI:async(destination,options)=>{
  assert.equal(destination,'https://api.openai.com/v1/responses');assert.equal(options.headers.Authorization,'Bearer test-only-secret');
  const body=JSON.parse(options.body);assert.equal(body.store,false);assert.equal(body.text.format.strict,true);assert.equal(body.max_output_tokens,1800);
  const input=JSON.parse(body.input);assert(input.evidence.length<=10);assert(input.evidence.every(r=>corpus.records.some(s=>s.id===r.id)));assert(input.evidence.every(r=>r.text.length<=2500));
  return mock(answer())();
 }});assert.equal(response.status,200);const output=await response.json();assert.equal(output.mode,'ai');assert.equal(output.chart.points[0].value,168000000);assert(!JSON.stringify(output).includes('test-only-secret'));
});
test('invalid citations, refusal, incomplete output and provider failures produce safe errors',async()=>{
 for(const fetchAPI of [mock(answer({paragraphs:[{text:'False source',sourceIds:['invented']}]})),async()=>Response.json({status:'incomplete'}),async()=>Response.json({status:'completed',output:[{content:[{type:'refusal',refusal:'no'}]}]}),async()=>new Response('secret upstream detail',{status:500}),async()=>{throw Error('test-only-secret');}]){
  const response=await handleBudgetRequest(req(q),env(),{corpus,fetchAPI});assert.equal(response.status,502);assert(!JSON.stringify(await response.json()).includes('test-only-secret'));
 }
});
test('actual expenditure, General Fund and missing-data questions cannot receive all-funds plan charts',async()=>{
 for(const question of ['2027 General Fund budget revenue','2027 budget actual spending','Beaumont Nights total spending']){
  const selected=retrieve(question,corpus);const raw=answer({paragraphs:[{text:'Limited evidence.',sourceIds:[selected[0].id]}]});
  const response=await handleBudgetRequest(req(question),env(),{corpus,fetchAPI:mock(raw)});assert.equal((await response.json()).chart,null);
 }
});
test('transport does not POST disabled questions; falls back on unavailable/rate-limited AI',async()=>{
 let calls=0;const result=await askBudget(q,corpus,async()=>{calls++;return Response.json({enabled:false});});assert.equal(calls,1);assert.equal(result.mode,'reviewed');
 for(const code of [429,502]){
  let n=0;const result=await askBudget(q,corpus,async()=>++n===1?Response.json({enabled:true}):new Response('',{status:code}));assert.equal(result.mode,'reviewed');assert(result.serviceNote);
 }
 const ai={...answer(),sources:[],mode:'ai'};let n=0;assert.equal((await askBudget(q,corpus,async()=>Response.json(++n===1?{enabled:true}:ai))).mode,'ai');
});
test('Worker keeps static routes and API status separate',async()=>{
 assert.equal((await worker.fetch(new Request(url),{})).status,200);
 const response=await worker.fetch(new Request('https://example.test/budget.html'),{ASSETS:{fetch:async()=>new Response('budget page')}});assert.equal(await response.text(),'budget page');
});

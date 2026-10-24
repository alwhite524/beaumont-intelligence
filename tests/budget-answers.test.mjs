import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {retrieve,localAnswer,validatedAnswer,safeLink} from '../docs/budget-answer-core.mjs';
const corpus=JSON.parse(fs.readFileSync(new URL('../docs/budget-answers-data.json',import.meta.url)));
test('Beaumont Nights never fabricates three-year expenditures or charts',()=>{
 const rows=retrieve('total expenditures on Beaumont Nights over the last three years',corpus);
 assert(rows.length>0);assert(rows.every(r=>/beaumont nights/i.test(r.title+' '+r.text)));
 const answer=localAnswer('Beaumont Nights over three years',corpus);
 assert.equal(answer.chart,null);assert.equal(answer.status,'insufficient');assert.match(answer.paragraphs[0].text,/do not establish/);
});
test('plan comparison uses reviewed values, not actual expenditure',()=>{
 const answer=localAnswer('Compare planned revenue and expenditure in the FY 2026–27 budget',corpus);
 assert.equal(answer.chart.points[0].value,168000000);assert.equal(answer.chart.points[1].value,162500000);
 assert.match(answer.chart.basis,/not actual/);
 assert.equal(localAnswer('2027 budget actual spending',corpus).chart,null);
 assert.equal(localAnswer('2027 General Fund budget revenue',corpus).chart,null);
});
test('police station retrieves the phase limitation',()=>{assert(retrieve('police station Phase I authorization',corpus).some(r=>/241,727/.test(r.text)));});
test('unknown citations and unsafe links rejected; missing evidence cannot chart',()=>{
 const evidence=retrieve('2027 budget revenue',corpus);
 assert.throws(()=>validatedAnswer({status:'answer',paragraphs:[{text:'Invented',sourceIds:['fake']}],gaps:[],chartGroupId:null},evidence,corpus));
 assert.equal(validatedAnswer({status:'insufficient',paragraphs:[{text:'Missing',sourceIds:[]}],gaps:[],chartGroupId:'fy27-plan'},evidence,corpus).chart,null);
 for(const url of ['javascript:alert(1)','//evil.test','../private.html'])assert.equal(safeLink(url),null);
});

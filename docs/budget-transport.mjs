import {localAnswer} from './budget-answer-core.mjs';

export async function askBudget(question,corpus,fetcher=fetch) {
  const fallback=message=>({...localAnswer(question,corpus),serviceNote:message});
  try {
    const status=await fetcher('/api/budget-ask',{headers:{Accept:'application/json'},signal:AbortSignal.timeout(5000)});
    if(!status.ok || !(await status.json()).enabled)return fallback('AI answers are not enabled. Showing reviewed summaries and related records.');
    const response=await fetcher('/api/budget-ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question}),signal:AbortSignal.timeout(30000)});
    if(response.status===429)return fallback('The AI question limit has been reached. Showing local records instead; try AI again later.');
    if(!response.ok)return fallback('AI answers are temporarily unavailable. Showing local records instead.');
    const answer=await response.json();
    if(answer.mode!=='ai'||!Array.isArray(answer.paragraphs)||!Array.isArray(answer.sources))throw Error('Invalid answer');
    return answer;
  }catch{return fallback('AI answers are unavailable. Showing reviewed summaries and related records.');}
}

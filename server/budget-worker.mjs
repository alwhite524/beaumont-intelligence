import {handleBudgetRequest} from './budget-api.mjs';
import corpus from '../docs/budget-answers-data.json' with {type:'json'};

export default {
  async fetch(request,env) {
    if(new URL(request.url).pathname==='/api/budget-ask')return handleBudgetRequest(request,env,{corpus});
    return env.ASSETS ? env.ASSETS.fetch(request) : new Response('Not found',{status:404});
  }
};

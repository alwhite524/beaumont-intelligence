window.PackageReview=(()=>{
  const $=id=>document.getElementById(id),node=(tag,text,parent)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(parent)parent.append(e);return e;};
  let api,leave,refresh,current,stage=null,busy=false,pending=false,disabledBefore=[];
  const freeze=value=>{busy=value;if(value){disabledBefore=[...document.querySelectorAll('#workspace input,#workspace button,#workspace select,#workspace textarea,#logout')].map(e=>[e,e.disabled]);disabledBefore.forEach(([e])=>e.disabled=true);}else{disabledBefore.forEach(([e,disabled])=>{if(e.isConnected)e.disabled=disabled;});document.querySelectorAll('#review-form input,#review-form textarea,#review-form select,#review-form button,[data-doc],[data-flag]').forEach(e=>e.disabled=!!current?.readOnly);}};
  async function reload(number){await refresh(current.date,number);}
  function updateReviewState(state){
    if(!current?.package)return;
    const r=current.package,open=r.analysis.issues.filter(i=>i.status!=='resolved').length;
    const remaining=current.items.reduce((n,i)=>n+i.documents.filter(d=>!(state.items[i.item]?.reviewedDocuments||[]).includes(d.id)).length,0);
    $('revision-summary').textContent=`${current.readOnly?'Earlier revision — read-only. ':''}Uploaded ${new Date(r.uploadedAt).toLocaleString()} · ${open} unresolved issue(s) · ${remaining} source range(s) not marked reviewed. ${open||remaining?'Review is not cleared.':'All recorded checks are complete; staff still control release and publication.'}`;
  }
  function show(meeting,state={items:{}}){
    current=meeting;pending=false;$('package-date').value=meeting.date;$('package-title').value=meeting.title||`${meeting.date} City Council`;
    $('revision-panel').hidden=!meeting.package;if(!meeting.package)return;
    const r=meeting.package;$('revision').replaceChildren();for(const v of meeting.revisions){const o=node('option',`Revision ${v.number} · ${v.label}`,$('revision'));o.value=v.number;}$('revision').value=r.number;
    const open=r.analysis.issues.filter(i=>i.status!=='resolved').length;
    updateReviewState(state);
    $('revision-comparison').replaceChildren();for(const type of ['added','removed','changed','unchanged']){node('h4',`${type}: ${r.comparison[type].length}`,$('revision-comparison'));const ul=node('ul',null,$('revision-comparison'));for(const key of r.comparison[type])node('li',key,ul);}
    $('check-limits').replaceChildren();for(const limit of r.analysis.limits)node('p',limit,$('check-limits'));
    $('package-issues').replaceChildren();
    for(const issue of r.analysis.issues){
      const card=node('article',null,$('package-issues'));card.className='flag';node('h4',`${issue.item} · ${issue.title}`,card);node('p',issue.detail,card);node('strong',`Status: ${issue.status}`,card);
      if(issue.resolution)node('p',`Resolution: ${issue.resolution.note} · source ${issue.resolution.doc}, page ${issue.resolution.page}`,card);
      if(issue.reviewNote)node('p',`Review note: ${issue.reviewNote}`,card);
      if(issue.history.length){const history=node('details',null,card);node('summary','Earlier review history',history);for(const h of issue.history)node('p',`Revision ${h.revision||r.number}: ${h.status}${h.resolution?` · ${h.resolution.note}`:''}`,history);}
      if(meeting.readOnly)continue;
      const form=node('form',null,card),sourceLabel=node('label','Supporting document (for resolution)',form),select=node('select',null,sourceLabel);
      for(const d of r.analysis.documents){const o=node('option',`${d.item} · ${d.title} · pages ${d.pageStart}–${d.pageEnd}`,select);o.value=d.id;}
      const pageLabel=node('label','Packet / PDF page',form),page=node('input',null,pageLabel);page.type='number';page.min='1';page.value=r.analysis.documents[0].pageStart;
      select.addEventListener('change',()=>{const d=r.analysis.documents.find(d=>d.id===select.value);page.min=d.pageStart;page.max=d.pageEnd;page.value=d.pageStart;});
      const noteLabel=node('label','Evidence for correction, or why the issue remains open',form),note=node('textarea',null,noteLabel);note.maxLength=5000;note.rows=2;note.required=true;
      for(const [label,status] of [['Confirm resolved','resolved'],['Keep / reopen issue','open']]){const b=node('button',label,form);b.type='button';b.addEventListener('click',async()=>{if(!note.value.trim())return note.reportValidity();if(!leave(true))return;freeze(true);try{await api('/api/package/issue',{date:meeting.date,revision:r.number,id:issue.id,status,note:note.value,doc:select.value,page:Number(page.value),version:r.reviewVersion});await reload(r.number);$('issue-message').textContent='Issue review saved for this revision.';}catch(error){$('issue-message').textContent=error.message;}finally{freeze(false);}});}
    }
    if(!r.analysis.issues.length)node('p','No issues detected by the available structural checks. Review attachment contents and record anything that needs correction.',$('package-issues'));
    $('issue-item').replaceChildren();for(const item of meeting.items){const o=node('option',`${item.item} · ${item.title}`,$('issue-item'));o.value=item.item;}$('new-package-issue').hidden=meeting.readOnly;
  }
  function init(options){({api,leave,refresh}=options);
    $('revision-panel').addEventListener('input',e=>{if(e.target.closest('form'))pending=true;});
    $('correction-report').addEventListener('click',async()=>{
      if(!leave())return;
      try{const data=await api(`/api/export?${new URLSearchParams({date:current.date,revision:current.package.number})}`),r=data.meeting.package;
        const lines=[`# Correction checklist — ${data.meeting.title}`,`Meeting: ${current.date} · Revision ${r.number}: ${r.label}`,`Uploaded: ${r.uploadedAt}`,'','Correct files outside this app, then upload the complete corrected revision for the same date. This report contains saved findings and notes only.',''];
        for(const issue of r.analysis.issues){lines.push(`## ${issue.item} — ${issue.title}`,`Status: ${issue.status}`,issue.detail);if(issue.reviewNote)lines.push('Review note: '+issue.reviewNote);if(issue.resolution)lines.push(`Resolution: ${issue.resolution.note} (source ${issue.resolution.doc}, page ${issue.resolution.page})`);for(const d of r.analysis.documents.filter(d=>d.item===issue.item||d.id==='packet'))lines.push(`Source: ${d.title}, PDF/packet pages ${d.pageStart}–${d.pageEnd}`);lines.push('');}
        for(const [key,note] of Object.entries(data.state.items)){if(note.notes||note.clarifications)lines.push(`## Saved working notes — ${key}`,note.notes||'',note.clarifications||'','');}
        lines.push('## Check limitations',...r.analysis.limits);const blob=new Blob([lines.join('\n')],{type:'text/markdown'}),url=URL.createObjectURL(blob),a=node('a',null,document.body);a.href=url;a.download=`correction-checklist-${current.date}-r${r.number}.md`;a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
      }catch(error){$('issue-message').textContent=error.message;}
    });
    $('confirm-detected-matches').addEventListener('click',()=>{for(const select of document.querySelectorAll('[data-match]'))if(select.value!=='UNASSIGNED')document.querySelector(`[data-confirm="${select.dataset.match}"]`).checked=true;});
    $('package-form').addEventListener('submit',async e=>{
      e.preventDefault();if(busy||!leave())return;const files=[...$('package-main').files,...$('package-extras').files];if(!files.length)return;
      if(files.some(f=>f.size>200*1024*1024||!f.name.toLowerCase().endsWith('.pdf'))){$('package-message').textContent='Choose PDFs up to 200 MB each.';return;}
      freeze(true);$('intake-preview').hidden=true;
      try{
        stage=await api('/api/package/start',{date:$('package-date').value,title:$('package-title').value,label:$('package-label').value});
        for(let i=0;i<files.length;i++){const f=files[i];$('package-message').textContent=`Uploading ${i+1}/${files.length}: ${f.name}`;const response=await fetch(`/api/package/file?${new URLSearchParams({stage:stage.id,filename:f.name})}`,{method:'POST',headers:{'Content-Type':'application/pdf'},body:f,signal:AbortSignal.timeout(120000)});const result=await response.json();if(!response.ok)throw Error(result.error||'Upload failed');}
        $('package-message').textContent='Checking PDF bookmarks, item matches and attachment references…';const result=await api('/api/package/analyze',{stage:stage.id});stage=result.stage;const a=result.analysis;
        $('intake-summary').replaceChildren();node('p',`${a.items.length} detected item(s), ${a.documents.length-1} supporting document range(s), ${a.issues.length} structural finding(s).`,$('intake-summary'));for(const limit of a.limits)node('p',limit,$('intake-summary'));
        $('intake-documents').replaceChildren();
        for(const d of a.documents){const row=node('tr',null,$('intake-documents')),cell=node('td',`${d.title} · pages ${d.pageStart}–${d.pageEnd}`,row),view=node('button','View range',cell);view.type='button';view.addEventListener('click',()=>{$('intake-viewer').src=`/document?${new URLSearchParams({stage:stage.id,doc:d.id})}`;});const select=node('select',null,node('td',null,row));select.dataset.match=d.id;select.setAttribute('aria-label',`Agenda item for ${d.title}`);for(const item of [{item:'MEETING',title:'Meeting documents'},...a.items,{item:'UNASSIGNED',title:'Unmatched — needs review'}]){const o=node('option',`${item.item} · ${item.title}`,select);o.value=item.item;}select.value=d.item;select.disabled=d.id==='packet';const check=node('input',null,node('td',null,row));check.type='checkbox';check.dataset.confirm=d.id;check.setAttribute('aria-label',`Confirm ${d.title}`);check.checked=d.id==='packet';}
        $('intake-ack').checked=false;$('intake-preview').hidden=false;$('intake-viewer').src=`/document?${new URLSearchParams({stage:stage.id,doc:'packet'})}`;$('package-message').textContent='Check the detected inventory. The active draft has not been replaced.';
      }catch(error){$('package-message').textContent=`${error.message}. The active draft is unchanged. Select the complete package and retry.`;}
      finally{freeze(false);}
    });
    $('confirm-package').addEventListener('click',async()=>{if(!stage||busy)return;const matches=[...document.querySelectorAll('[data-match]')].map(e=>({id:e.dataset.match,item:e.value,confirmed:document.querySelector(`[data-confirm="${e.dataset.match}"]`).checked}));freeze(true);try{const r=await api('/api/package/confirm',{stage:stage.id,matches,acknowledged:$('intake-ack').checked});$('intake-preview').hidden=true;$('intake-viewer').src='about:blank';await refresh(stage.date,r.number);$('package-message').textContent=`Draft revision ${r.number} saved. Review findings, correct files outside the app, then upload the complete corrected revision for the same date.`;$('package-main').value='';$('package-extras').value='';stage=null;}catch(error){$('package-message').textContent=error.message;}finally{freeze(false);}});
    $('revision').addEventListener('change',async()=>{if(!leave()){$('revision').value=current.package.number;return;}try{await reload(Number($('revision').value));}catch(error){$('issue-message').textContent=error.message;}});
    $('new-package-issue').addEventListener('submit',async e=>{e.preventDefault();if(!leave(true))return;const r=current.package;freeze(true);try{await api('/api/package/add-issue',{date:current.date,revision:r.number,title:$('issue-title').value,detail:$('issue-detail').value,item:$('issue-item').value,version:r.reviewVersion});$('new-package-issue').reset();await reload(r.number);$('issue-message').textContent='Issue recorded; it will carry forward to the next corrected draft.';}catch(error){$('issue-message').textContent=error.message;}finally{freeze(false);}});
  }
  return {init,show,updateReviewState,isBusy:()=>busy,hasUnsaved:()=>pending};
})();

(() => {
  const $=id=>document.getElementById(id);
  let meeting=null, state=null, selected=null, dirty=false, saving=false, uploading=false;
  const labels={'not-started':'Not started','in-progress':'In progress','needs-clarification':'Needs clarification',ready:'Ready for editorial review'};
  const node=(tag,text,parent)=>{const el=document.createElement(tag);if(text)el.textContent=text;if(parent)parent.append(el);return el;};
  const record=key=>state.items[key]||{status:'not-started',notes:'',clarifications:'',reviewedDocuments:[],resolvedFlags:[],version:0};
  const safeUrl=value=>typeof value==='string'&&(value.startsWith('https://')||value.startsWith('/api/uploaded?'))?value:null;
  async function api(path,body){const response=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const data=await response.json();if(!response.ok)throw Object.assign(Error(data.error||'Request failed'),{status:response.status});return data;}
  const leave=(savingIssue=false)=>!uploading&&!saving&&!PackageReview.isBusy()&&(!(dirty||(!savingIssue&&PackageReview.hasUnsaved()))||confirm('You have unsaved edits. Discard them and continue?'));
  function changed(){dirty=true;$('save-status').textContent='Unsaved changes';}
  function menu(){
    $('items').replaceChildren();const query=$('search').value.toLowerCase(),filter=$('filter').value;
    const all=meeting.items;const ready=all.filter(i=>record(i.item).status==='ready').length;
    $('progress').textContent=`${ready}/${all.length} ready for editorial review · ${all.reduce((n,i)=>n+i.documents.length,0)} collected documents`;
    let previous='',count=0;
    for(const item of all){const r=record(item.item),open=item.flags.filter(f=>!r.resolvedFlags.includes(f.id)).length+(meeting.package?.analysis.issues.filter(i=>i.item===item.item&&i.status!=='resolved').length||0);
      if(query&&!`${item.item} ${item.title} ${item.summary}`.toLowerCase().includes(query))continue;
      if(filter==='flagged'&&!open)continue;if(filter!=='all'&&filter!=='flagged'&&r.status!==filter)continue;
      if(item.section!==previous){node('div',item.section,$('items')).className='section-label';previous=item.section;}
      const button=node('button',`${item.item} · ${item.title}`,$('items'));button.type='button';button.setAttribute('aria-current',String(item.item===selected));node('small',`${labels[r.status]}${open?` · ${open} unresolved flag(s)`:''}`,button);
      button.addEventListener('click',()=>{if(leave())show(item.item);});count++;
    }
    if(!count)node('p','No items match this filter.',$('items'));
  }
  function show(key){
    selected=key;dirty=false;const item=meeting.items.find(i=>i.item===key),r=record(key);
    $('detail').hidden=false;$('empty').hidden=true;$('item-meta').textContent=`${meeting.date} · ${item.section} · ${key}`;$('item-title').textContent=item.title;$('summary').textContent=item.summary;
    $('funding').textContent=item.funding?`Funding analysis: ${item.funding}`:'No separate funding analysis collected.';
    $('source-question').textContent=item.question?`Collected review question: ${item.question}`:'';
    $('outcome').textContent=item.outcome?`Recorded outcome: ${item.outcome.summary} Vote: ${item.outcome.vote||'Not stated'}.`:'No item-specific outcome loaded. The agenda recommendation is not proof of approval.';
    $('evidence-limit').textContent=[meeting.reviewDate?`Source review: ${meeting.reviewDate}.`:'',meeting.reviewScope||'',item.outcome?meeting.outcomeEvidence||'':''].join(' ');
    $('official-agenda').hidden=!safeUrl(meeting.officialAgendaUrl);if(safeUrl(meeting.officialAgendaUrl))$('official-agenda').href=meeting.officialAgendaUrl;
    $('review-status').value=r.status;$('notes').value=r.notes;$('clarifications').value=r.clarifications;$('save-status').textContent='';$('saved-at').textContent=r.updatedAt?`Last saved ${new Date(r.updatedAt).toLocaleString()} · revision ${r.version}`:'No private review saved yet.';
    $('documents').replaceChildren();$('flags').replaceChildren();$('viewer').src='about:blank';$('viewer-title').textContent='Select a document';$('open-document').hidden=true;
    for(const doc of item.documents){
      const card=node('div',null,$('documents'));card.className='document';const button=node('button',doc.title,card);button.type='button';button.addEventListener('click',()=>openDocument(doc));
      if(doc.pageStart)node('small',`Packet pages ${doc.pageStart}–${doc.pageEnd||doc.pageStart}`,card);
      if(doc.uploaded)node('small',`Private upload · ${doc.pages} pages · ${Math.ceil(doc.bytes/1024)} KB`,card);
      const label=node('label',null,card),check=node('input',null,label);check.type='checkbox';check.dataset.doc=doc.id;check.checked=r.reviewedDocuments.includes(doc.id);label.append(document.createTextNode('Reviewed'));check.addEventListener('change',changed);
    }
    if(!item.documents.length)node('p','No item attachments collected in this structured inventory. Use the official agenda.',$('documents'));
    for(const flag of item.flags){const card=node('article',null,$('flags'));card.className='flag';node('h4',flag.title,card);node('p',flag.text,card);if(flag.packetPages?.length)node('small',`Packet pages ${flag.packetPages.join(', ')}`,card);const label=node('label',null,card),check=node('input',null,label);check.type='checkbox';check.dataset.flag=flag.id;check.checked=r.resolvedFlags.includes(flag.id);label.append(document.createTextNode('Resolved in my review (document the resolution below)'));check.addEventListener('change',changed);}
    if(!item.flags.length)node('p','No attention flags imported. Add new questions below as needed.',$('flags'));
    $('upload-files').value='';$('upload-message').textContent='';$('upload-form').hidden=true;
    document.querySelectorAll('#review-form input,#review-form textarea,#review-form select,#review-form button,[data-doc],[data-flag]').forEach(el=>el.disabled=!!meeting.readOnly);
    if(item.documents.length)openDocument(item.documents[0]);menu();
  }
  function openDocument(doc){const url=safeUrl(doc.url);if(!url)return;$('viewer-title').textContent=doc.title;$('open-document').href=url;$('open-document').hidden=false;const query={date:meeting.date,item:selected,doc:doc.id};if(doc.packageRevision)query.revision=doc.packageRevision;$('viewer').src=doc.localAvailable?`/document?${new URLSearchParams(query)}`:`/reference/documents/viewer.html?url=${encodeURIComponent(url)}&title=${encodeURIComponent(doc.title)}`;}
  async function load(date,revision){const query=new URLSearchParams({date});if(revision)query.set('revision',revision);const data=await api(`/api/meeting?${query}`);meeting=data.meeting;state=data.state;selected=null;show(meeting.items[0].item);PackageReview.show(meeting,state);$('global-message').textContent='';}
  async function refreshMeetings(preferred,revision){const {meetings}=await api('/api/meetings');$('meeting').replaceChildren();for(const m of meetings){const option=node('option',`${m.date} · ${m.title||'Meeting'} · ${m.count} items`,$('meeting'));option.value=m.date;}if(meetings.length){$('meeting').value=preferred&&meetings.some(m=>m.date===preferred)?preferred:meetings[0].date;await load($('meeting').value,revision);}else $('global-message').textContent='Upload a complete draft above to start its review.';}
  async function start(){$('unlock').hidden=true;try{await refreshMeetings();$('workspace').hidden=false;$('logout').hidden=false;}catch(error){$('unlock').hidden=false;throw error;}}
  $('unlock-form').addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/unlock',{code:$('code').value});$('code').value='';await start();}catch(error){$('unlock-message').textContent=error.message;}});
  $('meeting').addEventListener('change',async()=>{if(!leave()){$('meeting').value=meeting.date;return;}try{await load($('meeting').value);}catch(error){$('global-message').textContent=error.message;if(meeting)$('meeting').value=meeting.date;}});
  $('create-meeting-form').addEventListener('submit',async e=>{e.preventDefault();if(!leave())return;const date=$('new-date').value;try{await api('/api/create-meeting',{date,title:$('new-meeting-title').value});$('filter').value='all';$('search').value='';await refreshMeetings(date);$('manage-message').textContent='Meeting created. Select PDFs below to upload the agenda or full packet.';$('create-meeting-form').reset();}catch(error){$('manage-message').textContent=error.message;}});
  $('add-item-form').addEventListener('submit',async e=>{e.preventDefault();if(!meeting){$('manage-message').textContent='Create or select a meeting first.';return;}if(!leave())return;const key=$('new-item').value;try{await api('/api/add-item',{date:meeting.date,item:key,title:$('new-item-title').value,section:$('new-section').value});await refreshMeetings(meeting.date);$('filter').value='all';$('search').value='';show(key);$('manage-message').textContent='Agenda item added. Upload its staff report and attachments below.';$('add-item-form').reset();}catch(error){$('manage-message').textContent=error.message;}});
  $('upload-form').addEventListener('submit',async e=>{
    e.preventDefault();if(uploading||saving)return;if(dirty){$('upload-message').textContent='Save your notes before uploading documents.';return;}
    const files=[...$('upload-files').files];if(!files.length)return;
    if(files.some(file=>!file.name.toLowerCase().endsWith('.pdf')||file.size>50*1024*1024)){$('upload-message').textContent='Choose PDF files no larger than 50 MB each.';return;}
    uploading=true;const date=meeting.date,key=selected,controls=[...document.querySelectorAll('#workspace button,#workspace input,#workspace select,#workspace textarea,#logout')];controls.forEach(el=>el.disabled=true);
    let completed=0,duplicates=0,failure='';
    try{for(const file of files){$('upload-message').textContent=`Uploading ${completed+1} of ${files.length}: ${file.name}`;const query=new URLSearchParams({date,item:key,filename:file.name,title:file.name});const response=await fetch(`/api/upload?${query}`,{method:'POST',headers:{'Content-Type':'application/pdf'},body:file,signal:AbortSignal.timeout(120000)});const result=await response.json();if(!response.ok)throw Error(result.error||'Upload failed');completed++;if(result.duplicate)duplicates++;}}
    catch(error){failure=error.message;}
    finally{try{await refreshMeetings(date);show(key);$('upload-message').textContent=`${completed} file(s) received${duplicates?` (${duplicates} already attached)`:''}.${failure?` ${failure} Already received files are saved; select remaining files to retry.`:' Documents are ready to review.'}`;}catch(error){$('global-message').textContent=error.message;}controls.forEach(el=>el.disabled=false);uploading=false;}
  });
  for(const id of ['search','filter'])$(id).addEventListener('input',()=>{if(meeting)menu();});
  for(const id of ['notes','clarifications','review-status'])$(id).addEventListener('input',changed);
  $('review-form').addEventListener('submit',async e=>{e.preventDefault();if(saving)return;saving=true;$('save').disabled=true;const edit={status:$('review-status').value,notes:$('notes').value,clarifications:$('clarifications').value,reviewedDocuments:[...document.querySelectorAll('[data-doc]:checked')].map(e=>e.dataset.doc),resolvedFlags:[...document.querySelectorAll('[data-flag]:checked')].map(e=>e.dataset.flag),version:record(selected).version,packageRevision:meeting.package?.number};
    // Freeze navigation/editing during the write so the response cannot mark newer edits saved.
    const controls=[...document.querySelectorAll('#workspace button,#workspace input,#workspace select,#workspace textarea')];controls.forEach(el=>el.disabled=true);
    try{const data=await api('/api/save',{date:meeting.date,item:selected,review:edit});state.items[selected]=data.saved;dirty=false;$('save-status').textContent='Saved privately';$('saved-at').textContent=`Last saved ${new Date(data.saved.updatedAt).toLocaleString()} · revision ${data.saved.version}`;menu();PackageReview.updateReviewState(state);}catch(error){$('save-status').textContent=error.message;}
    finally{controls.forEach(el=>el.disabled=false);$('save').disabled=false;saving=false;}
  });
  $('export').addEventListener('click',async()=>{if(!meeting)return;if(dirty){$('global-message').textContent='Save your edits before exporting.';return;}try{const data=await api(`/api/export?date=${meeting.date}${meeting.package?'&revision='+meeting.package.number:''}`);const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=node('a',null,document.body);a.href=url;a.download=`private-agenda-review-${meeting.date}.json`;a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){$('global-message').textContent=error.message;}});
  $('logout').addEventListener('click',async()=>{if(!leave())return;try{await api('/api/logout',{});location.reload();}catch(error){$('global-message').textContent=error.message;}});
  PackageReview.init({api,leave,refresh:refreshMeetings});
  window.addEventListener('beforeunload',e=>{if(dirty||uploading||PackageReview.isBusy()||PackageReview.hasUnsaved()){e.preventDefault();e.returnValue='';}});
  start().catch(error=>{if(error.status!==401)$('unlock-message').textContent=error.message;});
})();

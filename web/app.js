'use strict';
const $ = id => document.getElementById(id);
const E = (tag, attrs={}, ...children) => {
  const node=document.createElement(tag);
  for(const [k,v] of Object.entries(attrs)) {
    if(k==='class') node.className=v;
    else if(k.startsWith('on')) node.addEventListener(k.slice(2),v);
    else if(k==='text') node.textContent=v;
    else if(v!==undefined) node.setAttribute(k,v);
  }
  for(const child of children.flat()) if(child!==null && child!==undefined) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  return node;
};
let state, cid=GlosaRoom.storage.getItem('study-course'), lid=GlosaRoom.storage.getItem('study-lesson'), view='study', filter='important', selection=null, editingAnnotation=null, busy=false;
let activeStarted=Date.now(), clockLesson=null, timer=null, studying=false;
const statusLabel={unseen:'Por explorar',pending:'Por comprobar',with_help:'Con ayuda',independent:'Comprobación independiente',self_review:'Revisada por vos'};
const kindLabel={annotation:'Anotación',answer:'Respuesta',chat_message:'Tu mensaje',tutor_reply:'Tutor',assessment:'Evaluación',feedback:'Feedback',study_time:'Tiempo de estudio',visit:'Lectura iniciada',self_review:'Revisión personal',self_review_cancel:'Revisión personal deshecha',annotation_resolved:'Duda marcada como resuelta',course_version:'Cambio de curso',schedule_updated:'Cambio de disponibilidad'};
kindLabel.tutor_note='Apunte del tutor';
kindLabel.continuation_requested='Continuación solicitada';
async function api(path,body) {
  const response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data=await response.json();
  if(!response.ok) throw new Error(data.error || 'No se completó la operación.');
  return data;
}
function notify(message) { $('notice').textContent=message; $('notice').style.display='block';clearTimeout(timer);timer=setTimeout(()=>$('notice').style.display='none',6500); }
function course() { return state.courses.find(c=>c.id===cid); }
function lesson() { return course()?.lessons.find(l=>l.id===lid); }
function records(kind=null,onlyLesson=true) {return state.events.filter(e=>e.courseId===cid && (!onlyLesson || e.lessonId===lid) && (!kind || e.kind===kind));}
function activeReviews(lessonId=lid){
  const version=course().version,events=records(null,false).filter(e=>(e.data.courseVersion||version)===version);
  const cancelled=new Set(events.filter(e=>e.kind==='self_review_cancel').flatMap(e=>Array.isArray(e.data.reviewIds)?e.data.reviewIds:[]));
  return events.filter(e=>e.kind==='self_review'&&e.lessonId===lessonId&&!cancelled.has(e.id));
}
async function undoReview(lessonId=lid){
  const ids=activeReviews(lessonId).map(e=>e.id);if(!ids.length)return;
  await api('/api/event',{id:crypto.randomUUID(),kind:'self_review_cancel',courseId:cid,lessonId,data:{reviewIds:ids,note:'El estudiante deshizo la marca de revisión; no debe contarse como lectura ni comprensión.'}});
  await reload();notify('Marca de revisión quitada.');
}
function dateLabel(iso) {return new Date(iso).toLocaleString('es-AR',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});}
async function reload() { state=await api('/api/state');if(!state.courses.length){cid=null;lid=null;}else{if(!course()) cid=state.courses[0].id;if(!lesson()) lid=state.room?.tutorial?course().lessons[0].id:state.recommendations[cid].lessonId;}render(); }
async function saveEvent(kind,data,target={courseId:cid,lessonId:lid}) {
  const item=await api('/api/event',{id:crypto.randomUUID(),kind,...target,data});state.events.push(item);return item;
}
function render() {
  window.WorkspaceKeys?.sync();
  document.title='Glosa · '+(state.room?.title||course()?.title||'Margen');
  $('environment-context').textContent=course()?.title||state.room?.title||'Glosa';
  $('main').classList.toggle('plan-view',view==='plan');
  $('workspace-mode-button').textContent=({study:'ESTUDIAR',notes:'NOTAS',notebook:'CUADERNO',plan:'PLAN'}[view]||'ESTUDIO')+(state.settings.keyboardProfile==='modal'?' · g m':'');
  if(view==='notes'){document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));ClassNotes.render();return;}
  ClassNotes.leave();
  if(!course()){
    $('course-select').replaceChildren();$('lesson-nav').replaceChildren();$('progress').replaceChildren();$('course-description').textContent='';$('note-count').textContent='';
    $('main').replaceChildren(E('span',{class:'eyebrow'},'UN PLIEGO EN BLANCO'),E('h1',{},state.room?.title||'Tu pliego'),E('p',{class:'lede'},'Empezá por un apunte, importá un curso o preparalo con tu agente.'),E('div',{class:'pliego-actions'},E('button',{class:'quiet',onclick:()=>{view='notes';render();}},'Escribir un apunte'),E('button',{class:'quiet',onclick:()=>$('course-file').click()},'Importar curso'),E('button',{class:'text-button',onclick:()=>GlosaRoom.activate('primer-trazo')},'Volver a Primer trazo')));
    $('tutor-dock').hidden=true;return;
  }
  $('tutor-dock').hidden=false;
  GlosaRoom.storage.setItem('study-course',cid);GlosaRoom.storage.setItem('study-lesson',lid);
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  $('course-select').replaceChildren(...state.courses.map(c=>E('option',{value:c.id},c.title)));$('course-select').value=cid;
  $('course-description').textContent=course().description || '';
  const statuses=state.recommendations[cid].statuses;
  const done=course().lessons.filter(l=>statuses[l.id]==='independent').length;
  $('progress').replaceChildren(E('div',{class:'muted'},`${done} de ${course().lessons.length} lecciones comprobadas`),E('div',{class:'progress-track'},E('div',{class:'progress-fill',style:`width:${Math.round(100*done/course().lessons.length)}%`})));
  const nav=[];let unit='';
  for(const l of course().lessons) {
    if(l.unit!==unit){unit=l.unit;nav.push(E('div',{class:'unit-label'},unit));}
    const status=statuses[l.id];
    nav.push(E('button',{class:'lesson-link'+(l.id===lid?' active':''),'aria-current':l.id===lid?'page':'false',onclick:()=>chooseLesson(l.id)},E('span',{class:'lesson-marker'+(status==='independent'?' done':'')},status==='independent'?'✓':status==='with_help'?'◐':status==='pending'?'·':'○'),l.title));
  }
  $('lesson-nav').replaceChildren(...nav);
  $('note-count').textContent=records('annotation',false).length || '';
  if(view==='study') renderStudy();else if(view==='notebook') renderNotebook();else renderPlan();
  renderChat();
}
async function chooseLesson(id) {
  await flushTime();window.WorkspaceKeys?.closePanels(false);lid=id;view='study';clockLesson=lid;activeStarted=Date.now();render();
  await saveEvent('visit',{courseVersion:course().version});
  window.scrollTo({top:0,behavior:'smooth'});
}
function safeSourceUrl(source,page) {const u=source.url || '';return (u.startsWith('/sources/') || u.startsWith('https://'))?GlosaRoom.url(u)+`#page=${page}`:null;}
function renderStudy() {
  const l=lesson(), recommendation=state.recommendations[cid];
  const days=Math.max(0,Math.round((Date.parse(state.settings.examDate)-Date.parse(state.localDate))/86400000));
  const nodes=[E('div',{class:'lesson-meta'},E('span',{class:'eyebrow'},l.unit)),E('h1',{},l.title),E('p',{class:'lede'},l.intro),E('details',{class:'reading-details'},E('summary',{},`${l.minutes} min de lectura · Recorrido y fuentes`),E('p',{class:'muted'},`${days} días hasta el parcial. `+(l.id===recommendation.lessonId?recommendation.reason:`La recomendación actual es «${course().lessons.find(x=>x.id===recommendation.lessonId)?.title}».`)),E('p',{class:'muted'},'v selecciona texto; a abre una anotación. También podés seleccionar una frase con el mouse. Las fuentes figuran debajo de cada bloque.'))];
  if(state.room?.tutorial){
    nodes[3]=E('details',{class:'reading-details'},E('summary',{},`${l.minutes} min · Probá a tu ritmo`),E('p',{class:'muted'},'Tus prácticas del tutorial quedan separadas de los pliegos. No hay un examen asociado a esta guía.'));
    nodes.push(E('div',{class:'pliego-actions'},E('button',{class:'text-button',onclick:()=>GlosaRoom.open()},'Abrir Margen'),E('button',{class:'text-button',onclick:()=>$('workspace-mode-button').click()},'Explorar modos · g m')));
  }
  if(l.warning) nodes.push(E('div',{class:'source-warning'},l.warning));
  function theorySection(b) {
    const text=E('div',{class:'theory','data-block-id':b.id,tabindex:0,'aria-label':b.title||'Bloque de teoría'});
    const annotations=records('annotation').filter(a=>a.data.blockId===b.id && a.data.courseVersion===course().version);
    highlight(text,b.text,annotations);
    const section=E('section',{class:'theory-section'},E('h2',{},b.title),text);
    if(b.references?.length) {
      const links=b.references.map(ref=>{const s=course().sources.find(x=>x.id===ref.sourceId);const url=s&&safeSourceUrl(s,ref.page);return url?E('a',{href:url,target:'_blank',rel:'noopener'},`${s.title.replace('.pdf','')} · pág. PDF ${ref.page} ↗`):null;});
      section.append(E('div',{class:'source-list'},...links));
    }
    for(const a of annotations.filter(a=>a.data.comment?.trim())) section.append(E('div',{class:'note-inline'},a.data.comment,E('div',{class:'muted'},a.data.shareWithTutor?'Compartida con el tutor':'Nota personal · fuera del contexto del tutor'),annotationActions(a)));
    return section;
  }
  const extras=[];
  if(l.simulation) extras.push(renderSimulation(l.simulation));
  for(const r of l.resources || []) {
    const resource=E('section',{},E('h2',{},r.title),E('p',{class:'muted'},r.task));
    if(r.kind==='video')resource.append(E('video',{src:r.src+(r.startSeconds?`#t=${r.startSeconds}`:''),class:'video-frame',controls:'',preload:'metadata',poster:r.src==='/media/glosa-demo.mp4'?'/media/glosa-demo-poster.jpg':undefined,'aria-label':r.title,playsinline:''}));
    else{
      const src=`https://www.youtube-nocookie.com/embed/${encodeURIComponent(r.videoId)}?start=${Math.max(0,r.startSeconds||0)}`;
      // YouTube requires a Referer; override no-referrer only for this embed, sending the origin.
      resource.append(E('iframe',{src,class:'video-frame',title:r.title,allow:'fullscreen',loading:'lazy',referrerpolicy:'strict-origin-when-cross-origin'}));
    }
    extras.push(resource);
  }
  const parts=l.sequence?l.sequence.map(part=>part.type==='block'?{node:theorySection(l.blocks.find(b=>b.id===part.id))}:{exercise:l.exercises.find(ex=>ex.id===part.id)}):[...l.blocks.map(b=>({node:theorySection(b)})),...extras.map(node=>({node})),...l.exercises.map(ex=>({exercise:ex}))];
  let group=[];
  const flush=()=>{if(!group.length)return;nodes.push(renderExerciseGroup(group));group=[];};
  for(const part of parts){if(part.exercise)group.push(part.exercise);else{flush();nodes.push(part.node);}}
  flush();if(l.sequence)nodes.push(...extras);
  const idx=course().lessons.findIndex(x=>x.id===lid);
  const reviewed=activeReviews().length>0;
  const target={courseId:cid,lessonId:lid},version=course().version,nextLesson=course().lessons[idx+1];
  nodes.push(E('footer',{class:'lesson-footer'},E('button',{class:'primary',onclick:async e=>{
    const button=e.currentTarget;button.disabled=true;
    try{
      if(!reviewed)await saveEvent('self_review',{courseVersion:version,note:'El estudiante siguió estudiando; registra revisión personal, no comprensión independiente.'},target);
      if(cid!==target.courseId||lid!==target.lessonId||view!=='study')return;
      await reload();
      if(cid!==target.courseId||lid!==target.lessonId||view!=='study')return;
      if(nextLesson)await chooseLesson(nextLesson.id);else{view='plan';render();}
    }catch(err){notify(err.message);}finally{button.disabled=false;}
  }},nextLesson?'Seguir estudiando →':'Ver pendientes →')));
  const applied=new Set(records('continuation_applied',false).map(e=>e.data.requestId));
  const pending=records('continuation_requested').some(e=>e.data.courseVersion===course().version&&!applied.has(e.id));
  nodes.push(E('details',{class:'continuation-handoff'},E('summary',{},pending?'Continuación solicitada':'Pedir continuación'),E('p',{class:'muted'},'El agente puede preparar un refuerzo con tus respuestas y dudas cuando retomes el trabajo con él.'),E('button',{class:'text-button',disabled:pending?'disabled':undefined,onclick:async e=>{e.target.disabled=true;try{await saveEvent('continuation_requested',{});renderStudy();notify('Solicitud guardada. Retomá con tu agente para preparar la continuación.');}catch(err){e.target.disabled=false;notify(err.message);}}},pending?'Continuación pendiente del agente':'Preparar continuación')));
  $('main').replaceChildren(...nodes);
}
function highlight(node,text,annotations) {
  const spans=[];
  for(const a of annotations){const d=a.data;if(Number.isInteger(d.start)&&Number.isInteger(d.end)&&d.end>d.start&&text.slice(d.start,d.end)===d.quote)spans.push({start:d.start,end:d.end,item:a});}
  const bounds=[...new Set([0,text.length,...spans.flatMap(s=>[s.start,s.end])])].sort((a,b)=>a-b);node.replaceChildren();
  for(let i=0;i<bounds.length-1;i++){
    const start=bounds[i],end=bounds[i+1],item=spans.findLast(s=>s.start<=start&&s.end>=end)?.item,value=text.slice(start,end);
    if(!item){node.append(document.createTextNode(value));continue;}
    const mark=E('mark',{tabindex:0,role:'button','data-annotation-id':item.id,'aria-label':'Resaltado: '+item.data.quote,onkeydown:e=>{if(e.key==='Enter'){e.preventDefault();mark.click();}},onclick:()=>showReadingActions(mark,()=>editAnnotation(item),()=>askTutor('Ayudame a entender este fragmento:\n\n'+item.data.quote),!!item.data.comment)},value);node.append(mark);
  }
}
function showReadingActions(anchor,note,tutor,hasNote=false){
  document.querySelector('.reading-highlight-actions')?.close();const rect=anchor.getBoundingClientRect();
  const dialog=E('dialog',{class:'reading-highlight-actions','aria-label':'Acciones del resaltado'},E('button',{type:'button',class:'text-button',onclick:()=>{dialog.close();Promise.resolve().then(note).catch(error=>notify(error.message));}},hasNote?'Editar nota':'Dejar una nota'),E('button',{type:'button',class:'text-button',onclick:()=>{dialog.close();Promise.resolve().then(tutor).catch(error=>notify(error.message));}},'Consultar al tutor'));
  const dismiss=event=>{if(!dialog.contains(event.target)&&!anchor.contains(event.target))dialog.close();};
  dialog.addEventListener('close',()=>{document.removeEventListener('pointerdown',dismiss,true);window.removeEventListener('resize',close);window.removeEventListener('scroll',close,true);dialog.remove();if(anchor.isConnected)anchor.focus({preventScroll:true});});
  const close=()=>dialog.close();document.body.append(dialog);dialog.show();const box=dialog.getBoundingClientRect();dialog.style.left=Math.max(12,Math.min(innerWidth-box.width-12,rect.left))+'px';dialog.style.top=(rect.bottom+box.height+12<innerHeight?rect.bottom+8:Math.max(12,rect.top-box.height-8))+'px';document.addEventListener('pointerdown',dismiss,true);window.addEventListener('resize',close);window.addEventListener('scroll',close,true);
}
function readingSelection(root){
  const selected=window.getSelection();if(!selected||selected.isCollapsed||!selected.rangeCount)return null;const range=selected.getRangeAt(0);
  if(!root?.contains(range.startContainer)||!root.contains(range.endContainer))return null;
  const quote=range.toString();if(!quote.trim()||quote.length>20000)return null;
  const prefix=range.cloneRange();prefix.selectNodeContents(root);prefix.setEnd(range.startContainer,range.startOffset);const start=prefix.toString().length;return {range,quote,start,end:start+quote.length};
}
async function captureReadingHighlight(){
  if(document.querySelector('dialog[open]'))return;
  if(view==='notes')return ClassNotes.highlightSelection();
  if(view!=='study'||document.body.classList.contains('tutor-open')||document.body.classList.contains('outline-open'))return;
  const anchor=window.getSelection()?.anchorNode,root=(anchor?.nodeType===Node.ELEMENT_NODE?anchor:anchor?.parentElement)?.closest('.theory'),chosen=readingSelection(root);if(!chosen)return;
  const block=lesson().blocks.find(b=>b.id===root.dataset.blockId);if(!block)return;const target={courseId:cid,lessonId:lid},version=course().version;
  const duplicate=records('annotation').some(e=>e.data.courseVersion===version&&e.data.blockId===block.id&&e.data.start===chosen.start&&e.data.end===chosen.end);window.getSelection().removeAllRanges();window.WorkspaceKeys?.clearVisual();if(duplicate)return;
  try{await saveEvent('annotation',{blockId:block.id,quote:chosen.quote,start:chosen.start,end:chosen.end,type:'highlight',comment:'',shareWithTutor:false},target);if(root.isConnected&&cid===target.courseId&&lid===target.lessonId)highlight(root,block.text,records('annotation').filter(e=>e.data.courseVersion===version&&e.data.blockId===block.id));}catch(error){notify(error.message);}
}
function renderExercise(ex) {
  const target={courseId:cid,lessonId:lid};
  const key=`draft:${cid}:${course().version}:${lid}:${ex.id}`;
  const prior=records('answer').filter(e=>e.data.exerciseId===ex.id).at(-1);
  const form=E('form',{class:'activity'},E('div',{class:'eyebrow'},ex.type==='choice'?'DISTINGUIR Y JUSTIFICAR':ex.type==='explain'?'CON TUS PALABRAS':'ARGUMENTAR Y APLICAR'),E('h3',{},ex.question));
  let input;
  if(ex.type==='choice') {
    const order=ex.orderedOptions?ex.options.map((_,i)=>i):ChoiceOrder.forAttempt(key,ex.options.length);
    for(const i of order){const opt=ex.options[i];
      const radio=E('input',{type:'radio',name:ex.id,value:i,required:'required'});radio.checked=String(GlosaRoom.storage.getItem(key)??prior?.data.selectedIndex)===String(i);
      radio.addEventListener('change',()=>GlosaRoom.storage.setItem(key,radio.value));
      form.append(E('label',{class:'choice-option'},radio,E('span',{class:'choice-text'},opt)));
    }
    input=E('textarea',{rows:3,placeholder:'¿Por qué elegiste esa opción? Una frase alcanza para empezar.','aria-label':'Justificación de la opción'});input.value=GlosaRoom.storage.getItem(key+':reason')??prior?.data.reasoning??'';
    input.addEventListener('input',()=>GlosaRoom.storage.setItem(key+':reason',input.value));
  } else {
    input=E('textarea',{rows:4,required:'required',placeholder:'Escribí tu explicación. También podés decir qué parte todavía no entendés.','aria-label':'Tu respuesta'});input.value=GlosaRoom.storage.getItem(key)??prior?.data.text??'';
    input.addEventListener('input',()=>GlosaRoom.storage.setItem(key,input.value));
  }
  form.append(input);
  const feedback=E('div');
  form.answerPayload=()=>{
    const selected=form.querySelector('input:checked');
    const payload={exerciseId:ex.id,question:ex.question,text:ex.type==='choice'?(selected?ex.options[Number(selected.value)]:''):input.value,reasoning:ex.type==='choice'?input.value:'',selectedIndex:ex.type==='choice'?Number(selected?.value):null,presentationOrder:ex.type==='choice'?(ex.orderedOptions?ex.options.map((_,i)=>i):ChoiceOrder.forAttempt(key,ex.options.length)):null,randomizationMethod:ex.type==='choice'?(ex.orderedOptions?'semantic-order':'crypto.getRandomValues / Fisher-Yates'):null};
    return payload;
  };
  form.saveAnswer=async(payload=form.answerPayload())=>{
    await saveEvent('answer',payload,target);
    if(ex.type==='choice') {
      const correct=payload.selectedIndex===ex.correctIndex;
      feedback.replaceChildren(E('div',{class:'answer-feedback'},(correct?'La opción coincide con el criterio. ':'Revisá esta distinción. ')+(ex.explanation||'Ahora justificá la respuesta.'),' Una opción por sí sola no demuestra comprensión.'));
      await saveEvent('feedback',{exerciseId:ex.id,kind:'choice_check',correct,explanation:ex.explanation,helpProvided:true},target);
    }
  };
  form.addEventListener('submit',ev=>{ev.preventDefault();form.closest('.exercise-group')?.querySelector('.group-conversation')?.click();});
  form.append(feedback);
  if(ex.type==='choice'&&!ex.orderedOptions)form.append(E('button',{type:'button',class:'text-button',onclick:async()=>{GlosaRoom.storage.setItem(key,'');GlosaRoom.storage.setItem(key+':reason','');GlosaRoom.storage.removeItem(key+':order');await saveEvent('feedback',{exerciseId:ex.id,kind:'practice_restart',helpProvided:!!prior});renderStudy();}},'Empezar otro intento'));
  return form;
}
function renderExerciseGroup(exercises){
  const target={courseId:cid,lessonId:lid};
  const forms=exercises.map(renderExercise),button=E('button',{type:'button',class:'primary group-conversation'},'Consultar al tutor');
  button.addEventListener('click',async()=>{
    if(busy){notify('El tutor está respondiendo.');return;}
    if(forms.some(form=>!form.reportValidity()))return;
    const answers=forms.map(form=>form.answerPayload());button.disabled=true;
    forms.forEach(form=>form.inert=true);
    try{
      for(let i=0;i<forms.length;i++)await forms[i].saveAnswer(answers[i]);
      if(cid!==target.courseId||lid!==target.lessonId){notify('Respuestas guardadas en la lección original.');return;}
      const message=answers.map(a=>a.question+'\n'+a.text+(a.reasoning?'\nMi justificación: '+a.reasoning:'')).join('\n\n');
      await askTutor(message,answers.length===1?answers[0].exerciseId:null);
    }catch(err){notify(err.message);}finally{button.disabled=false;forms.forEach(form=>form.inert=false);}
  });
  return E('section',{class:'exercise-group'},E('div',{class:'eyebrow'},'AHORA, HACÉ TUYA LA IDEA'),...forms,E('div',{class:'group-conversation-actions'},button));
}
// Old saved replies may contain an entire JSON envelope, including a cut-off tail.
// Decode for display only: preserve the original record for export and auditing.
function tutorVisibleText(raw){
  return raw.replace(/<(think|analysis|reasoning)\b[^>]*>[\s\S]*?<\/\1\s*>/gi,'').split(/<(?:think|analysis|reasoning)\b[^>]*>/i)[0].split(/<\/(?:think|analysis|reasoning)\s*>/i).at(-1).trim();
}
function internalTutorText(text){return /^(?:#{1,6}\s*)?(?:analysis\b|reasoning\b|thinking\b|análisis\s*:|razonamiento\s*:|el estudiante (?:envió|ha enviado|respondió|escribió)|analicemos contra la rúbrica|(?:i|we) (?:need to|must)\b|let.s (?:analyze|think)\b)/i.test(text);}
function readableTutor(raw,record={}){
  if(typeof raw!=='string')return '';
  const fallback='El tutor no devolvió una respuesta final completa. Podés reintentar; tu trabajo sigue guardado.';
  const clean=tutorVisibleText(raw).replace(/^```(?:json)?\s*\n?/,'').replace(/\s*```$/,'');
  const visible=reply=>{const text=tutorVisibleText(reply);return text&&!internalTutorText(text)?text:fallback;};
  // Read only an explicit final reply, even when an old provider put analysis
  // before its JSON. This changes presentation, never the persisted event.
  for(const match of clean.matchAll(/\{/g)){
    let depth=0,quoted=false,escaped=false;
    for(let i=match.index;i<clean.length;i++){
      const ch=clean[i];if(quoted){if(escaped)escaped=false;else if(ch==='\\')escaped=true;else if(ch==='"')quoted=false;continue;}
      if(ch==='"')quoted=true;else if(ch==='{')depth++;else if(ch==='}'&&!--depth){
        try{const parsed=JSON.parse(clean.slice(match.index,i+1));if(typeof parsed.reply==='string'&&parsed.reply.trim())return visible(parsed.reply);}catch{}break;
      }
    }
  }
  const envelope=clean.search(/\{\s*"reply"\s*:/),json=clean.startsWith('{')?clean:envelope>=0?clean.slice(envelope):null;
  if(json){
    const match=json.match(/"reply"\s*:\s*("(?:[^"\\]|\\.)*")/s);
    if(match){try{return visible(JSON.parse(match[1]));}catch{}}
    const start=json.match(/"reply"\s*:\s*(".*)$/s);
    if(start){for(let trim=0;trim<7;trim++){try{return visible(JSON.parse((trim?start[1].slice(0,-trim):start[1])+'"'));}catch{}}}
    return fallback;
  }
  if(record.structured===false||!clean||internalTutorText(clean))return fallback;
  return clean;
}
function tutorContent(raw,record={}){
  const node=E('div',{class:'tutor-answer-text'}),text=readableTutor(raw,record);
  // Limited, safe emphasis. Model output never becomes HTML or executable markup.
  for(const part of text.split(/(\*\*[^*\n]+\*\*)/g))node.append(part.startsWith('**')&&part.endsWith('**')?E('strong',{},part.slice(2,-2)):document.createTextNode(part));
  return node;
}
function renderChat() {
  if(!course())return;
  const latest=records('tutor_reply').at(-1)?.data;
  $('tutor-preview').textContent=latest?.followUp||readableTutor(latest?.reply,latest)||'Una duda también es un buen comienzo.';
  $('tutor-status').textContent=state.tutorConnected?'Conectado · '+(tutorProviders.find(p=>p.id===(state.settings.provider||'openrouter'))?.name||'Tutor'):'Sin conectar';
  $('chat-hint').textContent=state.tutorConnected?'Tu mensaje queda guardado.':'Conectalo en Ajustes.';
  const messages=records().filter(e=>['chat_message','tutor_reply'].includes(e.kind));
  if(!messages.length) $('tutor-chat').replaceChildren();
  else $('tutor-chat').replaceChildren(...messages.map(e=>{
    const student=e.kind==='chat_message',d=e.data;
    const m=E('div',{class:'message '+(student?'student':'assistant')},E('div',{class:'message-label'},student?'Vos':'Tutor'),student?d.message:tutorContent(d.reply,d));
    if(!student&&d.followUp)m.append(E('p',{},d.followUp));
    return m;
  }));
  $('tutor-chat').scrollTop=messages.length?$('tutor-chat').scrollHeight:0;
}
function showTutorDetails(){
  const data=course()?records('tutor_reply').at(-1)?.data:null;
  const dialog=E('dialog',{class:'tutor-details-dialog'},E('h2',{},'Contexto y evidencia'),E('button',{type:'button',class:'text-button',onclick:()=>dialog.close()},'Cerrar · Esc'));
  if(!data)dialog.append(E('p',{},'Todavía no hay una respuesta del tutor en esta lección.'));
  else{
    if(data.truncated)dialog.append(E('p',{},'La respuesta llegó incompleta; no se acreditó comprensión.'));
    if(data.tutorContext&&window.TutorContext)dialog.append(TutorContext.used(data.tutorContext));
    if(data.evidence?.length)dialog.append(E('ul',{},...data.evidence.map(x=>E('li',{},typeof x==='string'?x:(x.criterion||'Criterio')+': '+(x.quote||'')))));
    if(data.gaps?.length)dialog.append(E('p',{},'Pendiente: '+data.gaps.join(' · ')));
    if(data.reason)dialog.append(E('p',{},data.reason));
  }
  document.body.append(dialog);dialog.addEventListener('close',()=>dialog.remove());dialog.showModal();
}
async function askTutor(message,exerciseId=null) {
  if(!course()){notify('Prepará o importá un curso para conversar sobre sus lecciones. Podés consultar al tutor desde un apunte en Notas.');return;}
  if(busy){notify('El tutor está respondiendo. Tu respuesta está guardada.');return;}
  const targetCid=cid,targetLid=lid;
  window.WorkspaceKeys?.openTutor(false);
  await saveEvent('chat_message',{message,exerciseId});renderChat();
  if(!state.tutorConnected){notify('Respuesta guardada. Conectá el tutor en Ajustes o exportá para conversar fuera.');return;}
  busy=true;$('send-chat').disabled=true;$('send-chat').textContent='…';$('send-chat').setAttribute('aria-label','El tutor está respondiendo');
  try{await api('/api/tutor',{courseId:targetCid,lessonId:targetLid,message,exerciseId,contextRevision:window.TutorContext?.revision({kind:'study',courseId:targetCid,lessonId:targetLid})});await reload();}
  catch(err){notify(err.message);}
  finally{busy=false;$('send-chat').disabled=false;$('send-chat').textContent='↑';$('send-chat').setAttribute('aria-label','Conversar ↗');}
}
function renderNotebook() {
  const all=records(null,false), resolved=new Set(all.filter(e=>e.kind==='annotation_resolved').map(e=>e.data.annotationId));
  const visible=all.filter(e=>filter==='important'?['annotation','tutor_note'].includes(e.kind):filter==='all'?['annotation','tutor_note','answer','feedback','assessment','tutor_reply'].includes(e.kind):filter==='doubts'?(e.kind==='annotation'&&!resolved.has(e.id)&&['doubt','unclear','disagree'].includes(e.data.type))||(e.kind==='tutor_note'&&e.data.kind==='doubt'):e.kind===filter);
  const filterButton=(k,v)=>E('button',{class:'quiet'+(filter===k?' active':''),onclick:()=>{filter=k;renderNotebook();}},v);
  const nodes=[E('div',{class:'eyebrow'},'LO QUE VALE LA PENA RETOMAR'),E('h1',{},'Tu cuaderno'),E('p',{class:'lede'},'Tus anotaciones y los hallazgos importantes que el tutor propone conservar. Cada apunte remite a tu evidencia; una síntesis no acredita comprensión.'),E('div',{class:'filter-buttons'},filterButton('important','Lo importante'),filterButton('doubts','Dudas pendientes')),E('details',{class:'notebook-history'},E('summary',{},'Consultar registro completo'),E('p',{class:'muted'},'Las respuestas originales y las conversaciones se conservan para respaldos y para el agente que prepara la continuación.'),filterButton('all','Todo el registro'),filterButton('answer','Respuestas'),filterButton('feedback','Feedback'))];
  if(!visible.length)nodes.push(E('div',{class:'empty-state'},'Todavía no hay apuntes relevantes en esta vista. Anotá una duda; el tutor agregará solo lo que convenga retomar.'));
  for(const ev of visible.toReversed()) {
    const d=ev.data,l=course().lessons.find(x=>x.id===ev.lessonId);
    const item=E('article',{class:'notebook-item'},E('div',{class:'eyebrow'},`${kindLabel[ev.kind]} · ${dateLabel(ev.timestamp)}`),E('h3',{},l?.title||ev.lessonId));
    if(d.quote)item.append(E('blockquote',{},d.quote));
    item.append(E('p',{},d.comment||d.text||(ev.kind==='tutor_reply'?readableTutor(d.reply,d):d.reply)||d.reason||d.explanation||''));
    if(d.reasoning)item.append(E('p',{},'Tu justificación: '+d.reasoning));
    if(ev.kind==='tutor_note')item.append(E('p',{class:'muted'},({doubt:'Duda abierta',insight:'Relación conceptual',decision:'Decisión de repaso'}[d.kind]||'Síntesis')+' · Propuesto por el tutor. La cita es tuya; la síntesis no demuestra aprendizaje.'));
    if(d.courseVersion!==undefined && d.courseVersion!==course().version)item.append(E('p',{class:'muted'},'Esta anotación o respuesta pertenece a la versión '+d.courseVersion+'. Se conserva el fragmento original.'));
    if(ev.kind==='annotation') {
      item.append(E('span',{class:'muted'},d.shareWithTutor?'Compartida con el tutor':'Nota personal'),annotationActions(ev));
      if(!resolved.has(ev.id))item.append(E('button',{class:'text-button',onclick:async()=>{const old=lid;lid=ev.lessonId;try{await saveEvent('annotation_resolved',{annotationId:ev.id,note:'El estudiante la marca como resuelta.'});}finally{lid=old;}renderNotebook();}},' · Marcar como resuelta'));
      else item.append(E('span',{class:'muted'},' · Resuelta por vos'));
    }
    if(l)item.append(E('button',{class:'text-button',onclick:()=>chooseLesson(l.id)},'Volver a la lección →'));
    nodes.push(item);
  }
  nodes.push(E('button',{class:'primary',onclick:()=>$('export-dialog').showModal()},'Exportar historial completo'));
  $('main').replaceChildren(...nodes);
}
function renderPlan() { StudyPlan.render(); }

function renderSimulation(kind) {
  const box=E('section',{class:'simulation'},E('div',{class:'eyebrow'},'EXPERIMENTAR PARA ENTENDER'));
  if(kind==='integration') {
    box.append(E('h2',{},'Un pedido, tres versiones de la realidad'),E('p',{class:'muted'},'Modelo didáctico simplificado: el pedido reduce unidades disponibles. No representa todos los pasos contables de una venta real.'));
    const checkbox=E('input',{type:'checkbox'}), amount=E('input',{type:'range',min:0,max:20,value:5,'aria-label':'Unidades del pedido'}),output=E('div');
    const update=()=>{const n=Number(amount.value),shared=checkbox.checked;output.replaceChildren(E('div',{class:'flow-cells'},E('div',{class:'flow-cell'},'Ventas · disponible',E('strong',{},20-n)),E('div',{class:'flow-cell'},'Depósito · disponible',E('strong',{},shared?20-n:20)),E('div',{class:'flow-cell'},'Portal · disponible',E('strong',{},shared?20-n:20))),E('p',{},`Pedido: ${n} unidades. ${shared?'Los sistemas comparten el cambio.':'Depósito y portal no recibieron el cambio: podrían prometer stock ya reservado.'}`));};
    checkbox.addEventListener('change',update);amount.addEventListener('input',update);
    box.append(E('label',{class:'check'},checkbox,'Conectar los sistemas'),E('label',{},'Tamaño del pedido',amount),output,E('p',{class:'muted'},'Para pensar: ¿qué datos se deben compartir y en qué momento? ¿Alcanza con conectar sistemas si cada uno identifica al producto de forma diferente?'));update();
  } else {
    box.append(E('h2',{},'Un tablero puede decir cosas distintas'),E('p',{class:'muted'},'Datos ficticios: ventas de dos productos. Cambiá la medida y justificá qué decisión permite tomar.'));
    const select=E('select',{'aria-label':'Medida del tablero'},E('option',{value:'sales'},'Facturación'),E('option',{value:'margin'},'Margen de contribución')),out=E('div');
    const update=()=>{const values=select.value==='sales'?[10000,7000]:[1000,2800],max=Math.max(...values);out.replaceChildren(E('div',{class:'bar-chart'},...values.map((v,i)=>E('div',{class:'bar-column'},E('span',{},'$ '+v.toLocaleString('es-AR')),E('div',{class:'chart-bar',style:`height:${Math.round(v/max*85)}%`})))),E('div',{class:'flow-cells'},'Producto A','Producto B'),E('p',{},select.value==='sales'?'A factura más. ¿Eso implica que conviene promoverlo?':'B aporta más margen en este ejemplo. Faltan otros factores para decidir, como capacidad y demanda.'));};
    select.addEventListener('change',update);box.append(select,out,E('p',{class:'muted'},'Explicá por qué elegir una medida cambia la interpretación y qué relación tiene con el objetivo de negocio.'));update();
  }
  return box;
}
let tutorProviders=[
  {id:'openrouter',name:'OpenRouter',baseUrl:'https://openrouter.ai/api/v1',defaultModel:'openrouter/free'},
  {id:'freellmapi',name:'FreeLLMAPI',baseUrl:'http://localhost:3001/v1',defaultModel:'auto'},
  {id:'intern',name:'Intern Discovery',baseUrl:'https://discovery-api.intern-ai.org.cn/v1',defaultModel:''}
];
function providerDetails(){return tutorProviders.find(p=>p.id===$('provider-select').value)||tutorProviders[0];}
function providerFields(){const p=providerDetails();return {provider:p.id,providerBaseUrl:p.id==='freellmapi'?$('provider-base-url').value.trim():p.baseUrl};}
function setModelOptions(models=[],selected=providerDetails().defaultModel){
  const p=providerDetails(),options=[];
  if(p.id==='openrouter')options.push(E('option',{value:'openrouter/free'},'Selección automática gratuita'));
  if(p.id==='freellmapi')options.push(E('option',{value:'auto'},'Selección automática (cadena de FreeLLMAPI)'));
  if(p.id==='intern')options.push(E('option',{value:''},'Seleccioná o ingresá un ID de modelo'));
  for(const m of models)if(!options.some(o=>o.value===m.id))options.push(E('option',{value:m.id},m.name));
  if(selected&&!options.some(o=>o.value===selected))options.push(E('option',{value:selected},selected));
  $('model-select').replaceChildren(...options);$('model-select').value=selected;
}
function updateProvider(model=providerDetails().defaultModel){
  const p=providerDetails();$('provider-url-label').hidden=p.id!=='freellmapi';$('custom-model-label').hidden=p.id==='openrouter';$('custom-model').value='';
  $('model-label').textContent=p.id==='openrouter'?'Modelo gratuito':'Modelo';$('load-models').textContent=p.id==='openrouter'?'Buscar modelos gratuitos':'Buscar modelos';
  $('provider-info').textContent=p.id==='openrouter'?'Solo modelos con precio cero.':p.id==='freellmapi'?'Usá la URL de tu instancia y su clave unificada. La cadena y los proveedores habilitados se configuran en FreeLLMAPI.':'Creá una clave en Intern Discovery · Token Plan. El saldo y los límites dependen de tu cuenta.';
  $('quota-info').textContent='';setModelOptions([],model);
}
async function connectProviderKey(fields){
  const key=$('api-key').value.trim();if(!key)return;
  await api('/api/key',{...fields,key});
  if(JSON.stringify(fields)===JSON.stringify(providerFields()))$('api-key').value='';
  const fresh=await api('/api/state');state.tutorConnected=fresh.tutorConnected;renderChat();
}
api('/api/providers').then(d=>{tutorProviders=d.providers;}).catch(()=>{});
function showSettings() {
  const s=state.settings;$('exam-date').value=s.examDate;$('weekday-minutes').value=s.weekdayMinutes;$('weekend-minutes').value=s.weekendMinutes;$('api-key').value='';
  $('provider-select').value=s.provider||'openrouter';$('provider-base-url').value=s.providerBaseUrl||providerDetails().baseUrl;updateProvider(s.model);
  $('override-list').textContent=Object.entries(s.dailyOverrides||{}).map(([d,m])=>`${d}: ${m} min`).join(' · ')||'Sin ajustes por fecha.';$('settings-dialog').showModal();
}
async function flushTime() {
  const elapsed=Math.min(90,Math.round((Date.now()-activeStarted)/1000));activeStarted=Date.now();
  if(!state||!studying||!clockLesson||elapsed<1||document.hidden||view!=='study')return;
  const original=lid;lid=clockLesson;
  try{await saveEvent('study_time',{seconds:elapsed,measurement:'Ventana visible; aproximación de tiempo, no prueba de atención.'});}finally{lid=original;}
}
function annotationActions(item){return E('span',{class:'annotation-actions'},E('button',{class:'text-button',onclick:()=>editAnnotation(item)},'Editar'),E('button',{class:'text-button',onclick:()=>deleteAnnotation(item)},'Borrar'));}
function editAnnotation(item){editingAnnotation=item;selection=null;$('selected-quote').textContent=item.data.quote||'';$('annotation-comment').value=item.data.comment||'';$('annotation-type').value=item.data.type==='highlight'?'personal':item.data.type||'doubt';$('annotation-share').checked=item.data.shareWithTutor!==false;$('annotation-dialog').showModal();$('annotation-comment').focus();}
function deleteAnnotation(item){const dialog=E('dialog',{},E('h2',{},'Borrar anotación'),E('p',{},'Se elimina el comentario y sus revisiones de la base actual. Los respaldos descargados previamente no cambian.'),E('div',{class:'dialog-actions'},E('button',{class:'quiet',onclick:()=>dialog.close()},'Cancelar'),E('button',{class:'primary',onclick:async()=>{try{await api('/api/annotation',{action:'delete',id:item.id,expectedRevision:item.data.annotationRevision||0});dialog.close();await reload();notify('Anotación borrada.');}catch(e){notify(e.message);}}},'Borrar anotación')));dialog.addEventListener('close',()=>dialog.remove());document.body.append(dialog);dialog.showModal();}
function openStudyAnnotation(){
  if(view!=='study'||document.querySelector('dialog[open]')||document.body.classList.contains('tutor-open')||document.body.classList.contains('outline-open'))return;
  const s=window.getSelection();if(!s||s.isCollapsed||!s.rangeCount)return;
  const range=s.getRangeAt(0),start=range.startContainer.parentElement?.closest('.theory'),end=range.endContainer.parentElement?.closest('.theory');
  if(!start||start!==end)return;
  const quote=s.toString();if(!quote.trim())return;
  const prefix=range.cloneRange();prefix.selectNodeContents(start);prefix.setEnd(range.startContainer,range.startOffset);
  editingAnnotation=null;selection={blockId:start.dataset.blockId,quote,start:prefix.toString().length,end:prefix.toString().length+quote.length};
  $('selected-quote').textContent=quote;$('annotation-comment').value='';$('annotation-type').value='doubt';$('annotation-share').checked=true;$('annotation-dialog').showModal();$('annotation-comment').focus();
}
document.addEventListener('mouseup',event=>{if(!event.target.closest?.('mark[data-annotation-id],.pdf-highlight,.reading-highlight-actions,.notes-splitter'))captureReadingHighlight();});
$('annotation-form').addEventListener('submit',async ev=>{ev.preventDefault();try{const fields={comment:$('annotation-comment').value,type:$('annotation-type').value,shareWithTutor:$('annotation-share').checked};if(editingAnnotation){await api('/api/annotation',{...fields,action:'edit',id:editingAnnotation.id,expectedRevision:editingAnnotation.data.annotationRevision||0});}else{await saveEvent('annotation',{...selection,...fields});}$('annotation-dialog').close();editingAnnotation=null;window.getSelection()?.removeAllRanges();await reload();notify('Anotación guardada.');}catch(err){notify(err.message);}});
$('chat-form').addEventListener('submit',async ev=>{ev.preventDefault();const message=$('chat-input').value.trim();if(!message)return;$('chat-input').value='';try{await askTutor(message);}catch(err){$('chat-input').value=message;notify(err.message);}});
$('feedback-form').addEventListener('submit',async ev=>{ev.preventDefault();try{await saveEvent('feedback',{comment:$('feedback-text').value,kind:'lesson_feedback'});$('feedback-dialog').close();$('feedback-text').value='';notify('Feedback guardado para mejorar la continuación.');}catch(err){notify(err.message);}});
$('settings-form').addEventListener('submit',async ev=>{ev.preventDefault();try{
  const s={...state.settings,examDate:$('exam-date').value,weekdayMinutes:Number($('weekday-minutes').value),weekendMinutes:Number($('weekend-minutes').value),...providerFields(),model:$('custom-model').value.trim()||$('model-select').value,dailyOverrides:{...state.settings.dailyOverrides}};
  if($('override-date').value && $('override-minutes').value!=='')s.dailyOverrides[$('override-date').value]=Number($('override-minutes').value);
  await api('/api/settings',s);if($('api-key').value.trim())await api('/api/key',{...providerFields(),key:$('api-key').value.trim()});$('api-key').value='';$('settings-dialog').close();await reload();notify('Ajustes guardados.');
}catch(err){notify(err.message);}});
$('provider-select').addEventListener('change',()=>{$('provider-base-url').value=providerDetails().baseUrl;$('api-key').value='';updateProvider();});
$('provider-base-url').addEventListener('input',()=>{$('api-key').value='';$('quota-info').textContent='';});
$('model-select').addEventListener('change',()=>{$('custom-model').value='';});
$('load-models').addEventListener('click',async ev=>{
  ev.target.disabled=true;const fields=providerFields();
  try{await connectProviderKey(fields);const d=await api('/api/models?'+new URLSearchParams(fields));
    if(JSON.stringify(fields)!==JSON.stringify(providerFields()))return;
    const selected=$('model-select').value;setModelOptions(d.models,selected);notify('Catálogo de modelos actualizado.');
  }catch(err){notify(err.message);}finally{ev.target.disabled=false;}
});
$('check-quota').addEventListener('click',async()=>{
  const fields=providerFields();try{await connectProviderKey(fields);const d=await api('/api/quota?'+new URLSearchParams(fields));
    if(JSON.stringify(fields)!==JSON.stringify(providerFields()))return;
    $('quota-info').replaceChildren(document.createTextNode(d.freeRequests?`${d.freeRequests.remaining} consultas restantes de ${d.freeRequests.limit} en el día UTC.`:d.message||'OpenRouter no informó la cuota diaria de esta cuenta.'));
    if(d.url)$('quota-info').append(' ',E('a',{href:d.url,target:'_blank',rel:'noopener noreferrer'},'Abrir panel'));
  }catch(err){$('quota-info').textContent=err.message;}
});
$('disconnect-key').addEventListener('click',async()=>{try{await api('/api/key',{...providerFields(),key:''});$('api-key').value='';$('quota-info').textContent='Clave desconectada para este proveedor.';await reload();}catch(err){notify(err.message);}});
$('course-select').addEventListener('change',async()=>{await flushTime();cid=$('course-select').value;lid=course().lessons[0].id;clockLesson=lid;render();});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{$('mode-dialog').close();WorkspaceKeys.go(b.dataset.view).catch(e=>notify(e.message));}));
$('workspace-mode-button').addEventListener('click',()=>{$('mode-dialog').showModal();document.querySelector('#mode-dialog [data-view="'+view+'"]')?.focus();});
$('mode-settings').addEventListener('click',()=>{$('mode-dialog').close();showSettings();});
$('mode-dialog').addEventListener('keydown',ev=>{if(state.settings.keyboardProfile!=='modal')return;if(ev.ctrlKey||ev.altKey||ev.metaKey)return;const buttons=[...document.querySelectorAll('#mode-dialog [data-view],#mode-settings')];if(['j','k','ArrowDown','ArrowUp'].includes(ev.key)){ev.preventDefault();const index=buttons.indexOf(document.activeElement),delta=['j','ArrowDown'].includes(ev.key)?1:-1;buttons[(index+delta+buttons.length)%buttons.length]?.focus();}const dest={e:'study',n:'notes',c:'notebook',p:'plan'}[ev.key];if(dest){ev.preventDefault();document.querySelector('#mode-dialog [data-view='+dest+']').click();}if(ev.key==='a'){ev.preventDefault();$('mode-settings').click();}});
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>$ (b.dataset.close).close()));
$('settings-button').addEventListener('click',showSettings);$('export-button').addEventListener('click',()=>$('export-dialog').showModal());$('feedback-button').addEventListener('click',()=>$('feedback-dialog').showModal());
$('import-button').addEventListener('click',()=>$('course-file').click());
$('course-file').addEventListener('change',async ev=>{try{const file=ev.target.files[0];if(!file)return;if(file.size>8_000_000)throw new Error('El archivo supera 8 MB.');const data=JSON.parse(await file.text());if(data.courses&&data.events){await api('/api/restore',data);notify('Historial incorporado, sin duplicar eventos.');}else{const result=await api('/api/course',data);cid=result.id;lid=null;notify('Curso importado. Se conserva tu historial anterior.');}await reload();}catch(err){notify(err.message);}finally{ev.target.value='';}});
document.addEventListener('visibilitychange',()=>{if(document.hidden){const seconds=Math.min(90,Math.round((Date.now()-activeStarted)/1000));if(state&&studying&&clockLesson&&view==='study'&&seconds>0){const payload={id:crypto.randomUUID(),kind:'study_time',courseId:cid,lessonId:clockLesson,data:{seconds,measurement:'Ventana visible; estimación.'}};fetch('/api/event',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),keepalive:true}).catch(()=>{});}}activeStarted=Date.now();});
setInterval(()=>flushTime().catch(()=>{}),60000);
reload().then(()=>{clockLesson=lid;activeStarted=Date.now();}).catch(err=>{$('main').replaceChildren(E('h1',{},'No se pudo abrir el pliego'),E('p',{},err.message),E('button',{class:'quiet',onclick:()=>GlosaRoom.open()},'Abrir Margen'),E('button',{class:'text-button',onclick:()=>GlosaRoom.activate('primer-trazo')},'Volver a Primer trazo'));});

$('lesson-search').addEventListener('input',e=>{for(const b of document.querySelectorAll('.lesson-link'))b.hidden=!b.textContent.toLowerCase().includes(e.target.value.toLowerCase());});

async function toggleStudySession(){
  if(studying){await flushTime();studying=false;notify('Tiempo de sesión guardado.');}
  else{studying=true;activeStarted=Date.now();clockLesson=lid;notify('Sesión iniciada. Se cuenta el tiempo con Estudiar visible.');}
  updateSessionClock();
}
function updateSessionClock(){
  if(!state)return;
  const seconds=state.events.filter(e=>e.kind==='study_time'&&new Date(e.timestamp).toLocaleDateString('en-CA',{timeZone:state.timezone})===new Date().toLocaleDateString('en-CA',{timeZone:state.timezone})).reduce((n,e)=>n+(e.data.seconds||0),0)+(studying&&view==='study'&&!document.hidden?Math.min(90,Math.floor((Date.now()-activeStarted)/1000)):0);
  $('session-clock').textContent='Hoy · '+Math.floor(seconds/60)+' min';
  $('session-button').textContent=studying?'Pausar sesión':'Iniciar sesión';
  $('session-button').setAttribute('aria-pressed',String(studying));
}
$('session-button').addEventListener('click',()=>toggleStudySession().catch(e=>notify(e.message)));
setInterval(updateSessionClock,1000);

$('chat-input').addEventListener('input',()=>{const input=$('chat-input');input.style.height='auto';input.style.height=Math.min(160,input.scrollHeight)+'px';});

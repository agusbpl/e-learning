'use strict';
window.TutorContext=(()=>{
  function recordFor(target){return state?.library?.tutorContexts?.find(r=>r.target.kind===target.kind&&(target.kind==='study'?r.target.courseId===target.courseId&&r.target.lessonId===target.lessonId:r.target.noteId===target.noteId));}
  const revision=target=>recordFor(target)?.revision||0;
  const studyTarget=()=>({kind:'study',courseId:cid,lessonId:lid});
  function pages(text){
    const result=new Set();
    for(const part of text.split(',').map(s=>s.trim()).filter(Boolean)){
      const match=part.match(/^(\d+)(?:\s*-\s*(\d+))?$/);if(!match)throw Error('Usá páginas como 1-5, 8, 12.');
      const first=Number(match[1]),last=Number(match[2]||match[1]);if(first<1||last<first||last-first>1999)throw Error('Rango de páginas inválido.');
      for(let n=first;n<=last;n++)result.add(n);if(result.size>2000)throw Error('Elegí hasta 2.000 páginas.');
    }
    if(!result.size)throw Error('Indicá al menos una página.');return [...result].sort((a,b)=>a-b);
  }
  async function open(target=studyTarget(),message=''){
    const dialog=E('dialog',{class:'context-manager','aria-label':'Gestionar contexto del tutor'}),error=E('p',{class:'context-error',role:'alert'}),status=E('div',{class:'context-preview','aria-live':'polite'});
    dialog.append(E('div',{class:'eyebrow'},'LO QUE EL TUTOR RECIBE'),E('h2',{},'Contexto'),E('p',{class:'muted'},'Elegí el material para la próxima consulta. El mensaje que escribas y las reglas del tutor se envían siempre.'),E('p',{role:'status'},'Abriendo selección…'));
    // Native close restores focus before returning; a queued restoration would
    // steal a newer panel focus and clear an in-progress navigation prefix.
    dialog.addEventListener('close',()=>dialog.remove());document.body.append(dialog);dialog.showModal();
    try{
      const fresh=await api('/api/state');state.library=fresh.library;
      const initial=await api('/api/tutor-context',{target,message});if(!dialog.open)return;
      let selection=structuredClone(initial.selection),expectedRevision=initial.revision;const flags=E('div',{class:'context-flags'}),materials=E('div'),annotations=E('div'),notes=E('div'),texts=E('div');
      const search=E('input',{type:'search','aria-label':'Buscar material para el contexto',placeholder:'Buscar fuentes, anotaciones o apuntes…'});
      const queryInput=E('textarea',{rows:2,maxlength:20000,'aria-label':'Consulta para previsualizar búsqueda',placeholder:'La búsqueda de páginas usa las palabras de tu próxima consulta.'});queryInput.value=message;
      const matches=text=>text.toLowerCase().includes(search.value.toLowerCase());
      function mark(label,checked,change,description=''){
        const check=E('input',{type:'checkbox'});check.checked=checked;check.addEventListener('change',()=>{change(check.checked);status.replaceChildren(E('p',{class:'muted'},'Selección modificada. Previsualizá antes de guardar.'));});
        return E('label',{class:'context-choice'},check,E('span',{},label,description?E('small',{},description):null));
      }
      function drawFlags(){
        flags.replaceChildren();const names={includeLesson:'Lección completa',includeBaseNote:'Apunte o comentario actual',includeBaseSources:target.kind==='study'?'Páginas citadas por la lección':'Página PDF del apunte o comentario',includeHistory:'Historial reciente',includePlan:'Fecha y disponibilidad de estudio'};
        for(const [key,label] of Object.entries(names))if((key!=='includeLesson'||target.kind==='study')&&(key!=='includeBaseNote'||target.kind==='note'))flags.append(mark(label,selection[key],value=>selection[key]=value,key==='includeHistory'?(target.kind==='study'?'Hasta 70 eventos del curso y últimas evaluaciones. ':'Hasta 6 consultas de este comentario o página. ')+'Puede contener citas de fuentes y notas usadas antes. Desmarcalo para excluir esa conversación.':''));
      }
      function drawMaterials(){
        materials.replaceChildren();
        for(const doc of state.library.documents.filter(d=>matches(d.title))){
          let spec=selection.documents.find(s=>s.documentId===doc.id);
          const row=E('div',{class:'context-source'}),controls=E('div',{class:'context-source-options'});
          const modes=E('select',{'aria-label':'Contenido de '+doc.title},E('option',{value:'search'},'Buscar en todo el documento'),E('option',{value:'pages'},'Páginas elegidas'),E('option',{value:'all'},'Texto completo'));
          const range=E('input',{type:'text','aria-label':'Páginas de '+doc.title,placeholder:'1-5, 8, 12'});
          function sync(){controls.hidden=!spec;modes.value=spec?.mode||'search';range.hidden=modes.value!=='pages';if(spec?.pages)range.value=spec.pages.join(', ');}
          modes.addEventListener('change',()=>{spec.mode=modes.value;if(spec.mode==='pages'&&!spec.pages)spec.pages=[1];sync();status.replaceChildren();});
          range.addEventListener('input',()=>{spec.pageDraft=range.value;});
          row.append(mark(doc.title,!!spec,checked=>{if(checked){spec={documentId:doc.id,mode:'search'};selection.documents.push(spec);}else{selection.documents=selection.documents.filter(s=>s!==spec);spec=null;}sync();},(doc.pages||'?')+' páginas PDF'),controls);
          controls.append(modes,range,E('small',{class:'muted'},'Buscar envía hasta 6 páginas coincidentes; Texto completo envía todo el texto extraído.'));sync();materials.append(row);
        }
        if(!materials.childElementCount)materials.append(E('p',{class:'muted'},'No hay fuentes que coincidan.'));
      }
      function drawAnnotations(){
        annotations.replaceChildren();const courseVersion=state.courses.find(c=>c.id===target.courseId)?.version;
        const list=target.kind==='study'?state.events.filter(e=>e.kind==='annotation'&&e.courseId===target.courseId&&(e.data.courseVersion||courseVersion)===courseVersion):[];
        for(const a of list.filter(e=>matches((e.data.comment||'')+' '+(e.data.quote||''))))annotations.append(mark(a.data.comment||'Anotación sin comentario',selection.annotationIds.includes(a.id),checked=>{selection.annotationIds=checked?[...new Set([...selection.annotationIds,a.id])]:selection.annotationIds.filter(id=>id!==a.id);},(a.data.shareWithTutor===false?'Personal · se incluirá solo porque la marcás aquí. ':'')+(a.data.quote||'').slice(0,200)));
        if(!annotations.childElementCount)annotations.append(E('p',{class:'muted'},target.kind==='study'?'No hay anotaciones que coincidan.':'Las anotaciones de lectura están en Apuntes, debajo.'));
      }
      const sameItem=(a,b)=>a.noteId===b.noteId&&a.part===b.part&&(a.part==='general'||a.part==='anchor'&&(a.anchorId||JSON.stringify(a.legacyAnchor))===(b.anchorId||JSON.stringify(b.legacyAnchor))||a.part==='page'&&a.documentId===b.documentId&&a.page===b.page);
      function drawNotes(){
        notes.replaceChildren();
        for(const note of state.library.notes){
          const group=E('details'),entries=E('div');
          function entry(item,label,text){if(!matches(note.title+' '+label+' '+text))return;entries.append(mark(label,selection.noteItems.some(s=>sameItem(s,item)),checked=>{selection.noteItems=checked?[...selection.noteItems.filter(s=>!sameItem(s,item)),item]:selection.noteItems.filter(s=>!sameItem(s,item));},text.slice(0,170)));}
          entry({noteId:note.id,part:'general'},'Apunte general',note.content);
          for(const [documentId,pageNotes] of Object.entries(note.pageNotes||{}))for(const [page,text] of Object.entries(pageNotes))entry({noteId:note.id,part:'page',documentId,page:Number(page)},'Apunte de PDF '+page,text);
          for(const anchor of note.anchors)entry({noteId:note.id,part:'anchor',...(anchor.id?{anchorId:anchor.id}:{legacyAnchor:structuredClone(anchor)})},(anchor.scope==='general'?'Anotación independiente':'Anotación · PDF '+anchor.page),anchor.comment+' '+anchor.quote);
          if(entries.childElementCount){group.append(E('summary',{},note.title+(note.shared?'':' · personal')),entries);if(search.value)group.open=true;notes.append(group);}
        }
        if(!notes.childElementCount)notes.append(E('p',{class:'muted'},'No hay apuntes que coincidan.'));
      }
      function drawTexts(){
        texts.replaceChildren();selection.texts.forEach((source,index)=>{
          const title=E('input',{'aria-label':'Título de la fuente de texto',placeholder:'Título de la fuente',oninput:e=>source.title=e.target.value});title.value=source.title;
          const url=E('input',{type:'url','aria-label':'Enlace de la fuente de texto',placeholder:'https://… (referencia opcional)',oninput:e=>source.url=e.target.value});url.value=source.url||'';
          const text=E('textarea',{rows:5,maxlength:200000,'aria-label':'Contenido de la fuente de texto',placeholder:'Pegá el contenido que querés aportar.',oninput:e=>source.text=e.target.value});text.value=source.text;
          texts.append(E('div',{class:'context-text-source'},title,url,text,E('button',{type:'button',class:'text-button',onclick:()=>{selection.texts.splice(index,1);drawTexts();}},'Quitar fuente de este contexto')));
        });
      }
      function normalized(){const copy=structuredClone(selection);for(const doc of copy.documents){if(doc.mode==='pages'&&doc.pageDraft!==undefined)doc.pages=pages(doc.pageDraft);delete doc.pageDraft;}return copy;}
      function showPreview(result){
        const m=result.manifest;
        status.replaceChildren(E('p',{},m.characters.toLocaleString('es-AR')+' caracteres de contenido · '+m.items.length+' elementos · '+m.historyCount+' entradas de historial'),...m.warnings.map(w=>E('p',{class:'muted'},w)),m.tooLarge?E('p',{role:'alert'},'Supera el límite de la plataforma: elegí páginas o búsqueda antes de consultar.'):null,E('details',{},E('summary',{},'Ver material incluido'),...m.items.map(item=>E('p',{class:'muted'},(item.title||item.kind)+(item.kind==='document'?' · '+(item.mode==='all'?'completo':item.mode==='search'?'búsqueda':'páginas')+' · PDF '+(item.pages.join(', ')||'sin texto'):'')))),E('details',{},E('summary',{},'Ver texto de contexto'),E('pre',{},JSON.stringify(result.payload,null,2))));
      }
      async function preview(){error.textContent='';try{status.replaceChildren(E('p',{},'Preparando vista previa…'));showPreview(await api('/api/tutor-context',{target,message:queryInput.value,selection:normalized()}));}catch(e){error.textContent=e.message;status.replaceChildren();}}
      const upload=E('button',{type:'button',class:'text-button'},'＋ Adjuntar fuente PDF');
      upload.addEventListener('click',()=>{const input=E('input',{type:'file',accept:'.pdf,application/pdf',hidden:'hidden'});dialog.append(input);input.addEventListener('change',async()=>{upload.disabled=true;error.textContent='';try{const file=input.files[0];if(!file)return;if(file.size>20000000)throw Error('Adjuntá un PDF de hasta 20 MB.');const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});const doc=await api('/api/documents',{title:file.name,base64:encoded});if(!state.library.documents.some(d=>d.id===doc.id))state.library.documents.push(doc);if(!selection.documents.some(d=>d.documentId===doc.id))selection.documents.push({documentId:doc.id,mode:'all'});drawMaterials();status.replaceChildren(E('p',{class:'muted'},'Fuente adjuntada. Guardá la selección para incluirla.'));}catch(e){error.textContent=e.message;}finally{upload.disabled=false;input.remove();}});input.click();});
      const form=E('form',{onsubmit:async e=>{e.preventDefault();const button=form.querySelector('[type=submit]');button.disabled=true;error.textContent='';try{await api('/api/tutor-context',{action:'save',target,message:queryInput.value,selection:normalized(),expectedRevision});const fresh=await api('/api/state');state.library=fresh.library;notify('Contexto guardado para este '+(target.kind==='study'?'tema.':'apunte.'));dialog.close();}catch(err){error.textContent=err.message;}finally{button.disabled=false;}}});
      search.addEventListener('input',()=>{drawMaterials();drawAnnotations();drawNotes();});
      const section=(label,node,open=false)=>{const detail=E('details',{class:'context-section'},E('summary',{},label),node);detail.open=open;return detail;};
      form.append(search,flags,section('Fuentes',materials,true),E('div',{class:'context-add-actions'},upload,E('button',{type:'button',class:'text-button',onclick:()=>{selection.texts.push({title:'',text:'',url:''});drawTexts();}},'＋ Pegar fuente de texto')),texts,E('p',{class:'muted'},'Los enlaces de las fuentes de texto sirven como referencia: pegá su contenido, el tutor no navega esos enlaces.'),section('Anotaciones de estudio',annotations),section('Apuntes y anotaciones de lectura',notes),E('details',{},E('summary',{},'Vista previa de la próxima consulta'),queryInput,E('button',{type:'button',class:'text-button',onclick:preview},'Previsualizar contexto'),status),error,E('div',{class:'dialog-actions'},E('button',{type:'button',class:'text-button',onclick:()=>{selection=structuredClone(initial.defaults);drawFlags();drawMaterials();drawAnnotations();drawNotes();drawTexts();status.replaceChildren(E('p',{class:'muted'},'Selección inicial restaurada. Guardá para aplicarla.'));}},'Restablecer selección inicial'),E('button',{type:'button',class:'quiet',onclick:()=>dialog.close()},'Cancelar'),E('button',{type:'submit',class:'primary'},'Guardar contexto')));
      dialog.replaceChildren(E('div',{class:'eyebrow'},'LO QUE EL TUTOR RECIBE'),E('h2',{},'Contexto'),E('p',{class:'muted'},'La selección se guarda por '+(target.kind==='study'?'lección':'apunte')+' y se comparte entre tus dispositivos. El mensaje y las reglas del tutor se envían siempre.'),form);
      drawFlags();drawMaterials();drawAnnotations();drawNotes();drawTexts();showPreview(initial);search.focus();
    }catch(e){dialog.replaceChildren(E('h2',{},'Contexto'),E('p',{role:'alert'},e.message),E('button',{class:'quiet',onclick:()=>dialog.close()},'Cerrar'));}
  }
  document.getElementById('tutor-context-button').addEventListener('click',()=>open(studyTarget(),document.getElementById('chat-input').value));
  function used(trace){if(!trace)return null;return E('details',{class:'context-used'},E('summary',{},'Contexto utilizado'),E('p',{class:'muted'},'Selección '+trace.revision+' · '+trace.manifest.characters.toLocaleString('es-AR')+' caracteres · '+trace.manifest.historyCount+' entradas de historial'),...trace.manifest.items.map(item=>E('p',{class:'muted'},(item.title||item.kind)+(item.kind==='document'?' · '+(item.mode==='all'?'completo':item.mode==='search'?'búsqueda':'páginas')+' · PDF '+item.pages.join(', '):''))),...trace.manifest.warnings.map(w=>E('p',{class:'muted'},w)));}
  return {open,studyTarget,revision,used};
})();

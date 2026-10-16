'use strict';
/**
 * StudyTools — Herramientas de estudio inspiradas en Obsidian, integradas con
 * los apuntes reales de Glosa (sin un segundo almacén desconectado).
 *
 * Qué agrega:
 *   1. Wikilinks [[Título]] con referencias inversas y navegación.
 *   2. Plantilla de ficha de concepto y registro de errores de parcial.
 *   3. Propiedades de estudio (materia, unidad, fecha de parcial, necesito
 *      practicar) guardadas como metadata propia de cada apunte.
 *
 * La metadata de estudio vive dentro de la nota (`study`) y la valida
 * library.py. Nunca se crea un curso ni una lección arbitraria y nunca se
 * escribe como feedback de curso: son datos de estudio de quien aprende y no
 * acreditan dominio.
 *
 * El módulo no depende de archivos ajenos para funcionar: detecta la vista de
 * apuntes, engancha `ClassNotes.render` y guarda usando la API real de notas.
 * Usa la API limpia de `ClassNotes` (`select`, `current`, `currentId`,
 * `applyStudy`) cuando está disponible.
 */
window.StudyTools=(()=>{
  // === Constantes ===
  const WIKILINK_REGEX=/\[\[([^\[\]]+)\]\]/g;
  const ERROR_TYPES=['concepto','procedimiento','cálculo','interpretación','aplicación','otro'];
  const CONCEPT_CARD_TEMPLATE=`## Ficha: {concepto}

### Definición propia
[Explicá el concepto con tus palabras, como si se lo contaras a un compañero]

### Ejemplo
[Un caso concreto que ilustre el concepto]

### Contraejemplo
[Un caso que se parezca pero no cumpla la condición; explicá por qué]

### Fuente
[Clase, página del PDF o referencia bibliográfica]

### Pregunta de comprensión
[Una pregunta que te obligue a pensar el concepto, no solo repetirlo]
`;
  const STUDY_FIELDS=['materia','unidad','parcialDate','needsPractice','errors'];

  // === Estado interno ===
  let activeTab='references';
  let panel=null;
  let renderHooked=false;
  // Metadata de estudio que el usuario tocó en esta sesión, por si el objeto
  // `current` de notes.js todavía no la copió (apunte recién abierto). El
  // guardado real va por `ClassNotes.applyStudy`.
  const studyByNote=new Map();

  // === Acceso a globals ===
  // `state` y `api` viven en el ámbito global de los scripts clásicos. `state`
  // es un `let` (no está en window), `api` es una función declarada.
  const appState=()=>{try{return typeof state!=='undefined'?state:null;}catch{return null;}};
  const appApi=()=>{try{return typeof api!=='undefined'?api:window.api;}catch{return window.api;}};
  const CN=()=>window.ClassNotes||null;
  const notes=()=>appState()?.library?.notes||[];
  const activeNoteObject=()=>{const cn=CN();const cur=typeof cn?.current==='function'?cn.current():cn?.current;return cur&&cur.id?cur:null;};
  const pickNotify=()=>{try{return typeof notify!=='undefined'?notify:window.notify;}catch{return window.notify;}};
  const say=message=>{const n=pickNotify();if(typeof n==='function')n(message);};

  // === Helpers de DOM ===
  const $=id=>document.getElementById(id);
  const E=(tag,attrs={},...children)=>{
    const node=document.createElement(tag);
    for(const [key,value] of Object.entries(attrs)){
      if(value===undefined||value===null)continue;
      if(key==='class')node.className=value;
      else if(key==='text')node.textContent=value;
      else if(key.startsWith('on')&&typeof value==='function')node.addEventListener(key.slice(2),value);
      else if(typeof value==='boolean'){
        // `checked`, `disabled`, `hidden`, `open`, … son propiedades del DOM.
        if(key in node)node[key]=value;
        else if(value)node.setAttribute(key,'');
      }
      else if(key in node)node[key]=value;
      else node.setAttribute(key,value);
    }
    for(const child of children.flat())if(child!==null&&child!==undefined)node.append(child instanceof Node?child:document.createTextNode(String(child)));
    return node;
  };
  const cssEscape=id=>String(id).replace(/["\\]/g,'\\$&');
  const clone=value=>JSON.parse(JSON.stringify(value));
  const dateTimeLabel=iso=>{const d=new Date(iso);return isNaN(d)?'':d.toLocaleString('es-AR',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});};

  // === Texto de apuntes y búsqueda ===
  const noteText=n=>{
    let text=n.content||'';
    if(n.pageNotes)for(const pages of Object.values(n.pageNotes))for(const t of Object.values(pages))text+='\n'+t;
    return text;
  };
  const noteTitle=n=>n.title||'Apunte sin título';
  const byId=id=>notes().find(n=>n.id===id)||null;
  const normalizeTitle=value=>String(value||'').trim().toLowerCase().replace(/\s+/g,' ');
  const snippet=(text,needle)=>{
    const at=String(text||'').toLowerCase().indexOf(needle);
    if(at<0)return'';
    const start=Math.max(0,at-40),end=Math.min(text.length,at+needle.length+60);
    return (start>0?'…':'')+text.slice(start,end).replace(/\s+/g,' ').trim()+(end<text.length?'…':'');
  };

  function extractWikilinks(text){
    if(!text)return[];
    const links=[];let match;
    WIKILINK_REGEX.lastIndex=0;
    while((match=WIKILINK_REGEX.exec(text))!==null){
      const title=match[1].trim();
      if(title)links.push({title,index:match.index,length:match[0].length});
    }
    return links;
  }

  function findNoteByTitle(title){
    const normalized=normalizeTitle(title);
    if(!normalized)return null;
    return notes().find(n=>normalizeTitle(noteTitle(n))===normalized)||null;
  }

  function linksOf(note){
    return extractWikilinks(noteText(note)).map(link=>normalizeTitle(link.title));
  }

  function getBacklinks(noteId){
    const note=byId(noteId);
    if(!note)return[];
    const title=normalizeTitle(noteTitle(note));
    if(!title)return[];
    return notes()
      .filter(n=>n.id!==noteId&&linksOf(n).includes(title))
      .map(n=>({note:n,updatedAt:n.updatedAt||n.createdAt||''}))
      .sort((a,b)=>String(b.updatedAt).localeCompare(String(a.updatedAt)));
  }

  function outgoingLinks(note){
    return extractWikilinks(noteText(note)).map(link=>{
      const target=findNoteByTitle(link.title);
      return {title:link.title,target:target||null,explicit:true};
    });
  }

  // Menciones a un concepto en apuntes, clases y ejercicios (no solo wikilinks).
  function getMentions(title){
    const needle=normalizeTitle(title);
    const out=[];
    if(!needle)return out;
    for(const note of notes()){
      const text=noteText(note).toLowerCase();
      if(normalizeTitle(noteTitle(note))===needle||!text.includes(needle))continue;
      out.push({kind:'apunte',id:note.id,title:noteTitle(note),snippet:snippet(noteText(note),needle)});
    }
    const stateNow=appState();
    for(const course of stateNow?.courses||[]){
      for(const lesson of course.lessons||[]){
        for(const block of lesson.blocks||[]){
          if((block.text||'').toLowerCase().includes(needle)){
            out.push({kind:'clase',courseId:course.id,lessonId:lesson.id,title:`${course.title} · ${lesson.title}`,snippet:snippet(block.text,needle)});
            break;
          }
        }
        for(const exercise of lesson.exercises||[]){
          const text=((exercise.question||'')+' '+((exercise.rubric||[]).join(' '))).toLowerCase();
          if(text.includes(needle)){out.push({kind:'ejercicio',courseId:course.id,lessonId:lesson.id,title:`${course.title} · ${lesson.title}`,snippet:snippet(exercise.question||'',needle)});break;}
        }
      }
    }
    return out.slice(0,12);
  }

  // === Ficha de concepto ===
  const createConceptCard=conceptName=>CONCEPT_CARD_TEMPLATE.replace(/\{concepto\}/g,String(conceptName||'').trim().slice(0,200)||'Concepto');

  // === Propiedades de estudio (metadata de la nota) ===
  function studyOf(note){
    if(!note)return null;
    if(studyByNote.has(note.id))return clone(studyByNote.get(note.id));
    return note.study?clone(note.study):null;
  }

  function defaultStudy(){return {materia:'',unidad:'',parcialDate:null,needsPractice:false,errors:[]};}

  function mergeStudy(noteId,patch){
    const base=studyOf(byId(noteId))||defaultStudy();
    const next={...base,...patch};
    next.materia=String(next.materia||'').slice(0,120);
    next.unidad=String(next.unidad||'').slice(0,120);
    next.parcialDate=next.parcialDate||null;
    next.needsPractice=next.needsPractice===true;
    next.errors=Array.isArray(next.errors)?next.errors.slice(0,500):[];
    const clean={};
    for(const field of STUDY_FIELDS)clean[field]=next[field];
    studyByNote.set(noteId,clean);
    return clean;
  }

  function getNoteProperties(noteId){
    const note=byId(noteId);
    if(!note)return null;
    const study=studyOf(note)||defaultStudy();
    return {
      noteId,
      materia:study.materia||'',
      unidad:study.unidad||'',
      parcialDate:study.parcialDate||null,
      needsPractice:study.needsPractice===true,
      errors:Array.isArray(study.errors)?study.errors:[]
    };
  }

  // === Guardado real de la metadata de estudio ===
  // La nota activa se persiste por el adaptador `ClassNotes.applyStudy`, que usa
  // el mismo camino de guardado de Glosa (flush) incluso para un apunte nuevo sin
  // texto. Las notas que no están abiertas se guardan con la API real. No se
  // envuelve ninguna función global.
  function sanitizeNote(note){
    const keep=['id','title','folder','content','contentFormat','shared','documentId','page','writingScope','pageNotes','anchors','study','revision'];
    const out={};
    for(const key of keep)if(key in note)out[key]=note[key];
    return out;
  }

  function replaceNote(note){
    const stateNow=appState();
    if(!stateNow?.library?.notes)return;
    const index=stateNow.library.notes.findIndex(n=>n.id===note.id);
    if(index>=0)stateNow.library.notes[index]=note;
    else stateNow.library.notes.push(note);
    if(note.study)studyByNote.set(note.id,clone(note.study));
  }

  async function saveStudy(noteId,patch){
    const study=mergeStudy(noteId,patch);
    const cn=CN();
    if(getActiveNoteId()===noteId&&cn&&typeof cn.applyStudy==='function'){
      const saved=await cn.applyStudy(noteId,clone(study));
      if(saved)studyByNote.set(noteId,clone(saved));
      renderNoteListBadges();
      return saved||study;
    }
    const note=byId(noteId);
    if(!note)throw Error('Guardá el apunte antes de agregar propiedades de estudio.');
    const payload=sanitizeNote({...clone(note),study:clone(study)});
    let result;
    try{result=await appApi()('/api/notes',payload);}
    catch(error){
      // El archivo pudo cambiar fuera de Glosa: traer la versión vigente para
      // no volver a enviar contenido viejo, y conservar la propiedad local.
      try{const fresh=await appApi()('/api/state');const stateNow=appState();if(stateNow&&fresh?.library)stateNow.library=fresh.library;}catch{}
      studyByNote.set(noteId,clone(study));
      renderNoteListBadges();
      throw Error((error&&error.message)||('La propiedad quedó pendiente: '+noteId));
    }
    const saved=result&&result.note?result.note:result;
    if(saved&&saved.id)replaceNote(saved);
    else if(study)studyByNote.set(noteId,clone(study));
    renderNoteListBadges();
    return study;
  }

  async function setProperty(noteId,property,value){
    if(property==='needs_practice')return saveStudy(noteId,{needsPractice:value===true});
    if(property==='parcial_date')return saveStudy(noteId,{parcialDate:value||null});
    if(property==='materia'||property==='unidad')return saveStudy(noteId,{[property]:value||''});
    throw Error('Propiedad de estudio desconocida.');
  }

  async function logPartialError(data){
    const noteId=getActiveNoteId();
    if(!noteId)throw Error('Abrí un apunte guardado antes de registrar un error.');
    const current=getNoteProperties(noteId)||defaultStudy();
    const entry={
      id:(window.crypto?.randomUUID?.() || String(Date.now())),
      concept:String(data.concept||'').trim().slice(0,200),
      errorType:ERROR_TYPES.includes(data.errorType)?data.errorType:'concepto',
      description:String(data.description||'').slice(0,20000),
      correction:String(data.correction||'').slice(0,20000),
      createdAt:new Date().toISOString()
    };
    if(!entry.concept)throw Error('Escribí el concepto o ejercicio del error.');
    await saveStudy(noteId,{errors:[entry,...(current.errors||[])].slice(0,500)});
    return entry;
  }

  // === Filtros ===
  function filterNotes(filters={}){
    const f=filters||{};
    return notes().filter(note=>{
      const props=getNoteProperties(note.id)||defaultStudy();
      if(f.materia&&props.materia!==f.materia)return false;
      if(f.unidad&&props.unidad!==f.unidad)return false;
      if(f.needsPractice&&!props.needsPractice)return false;
      if(f.parcialDate&&props.parcialDate!==f.parcialDate)return false;
      return true;
    });
  }

  const collect=(field)=>{const set=new Set();for(const note of notes()){const props=getNoteProperties(note.id);const value=props?.[field];if(value)set.add(value);}return [...set].sort((a,b)=>a.localeCompare(b,'es'));};
  const getAllMaterias=()=>collect('materia');
  const getAllUnidades=()=>collect('unidad');

  // === Navegación real (preserva borrador: la navegación de Glosa hace flush) ===
  function getActiveNoteId(){
    const cn=CN();
    if(cn){
      const cid=typeof cn.currentId==='function'?cn.currentId():cn.currentId;
      if(typeof cid==='string'&&cid)return cid;
      const cur=typeof cn.current==='function'?cn.current():cn.current;
      if(cur&&cur.id)return cur.id;
    }
    const link=document.querySelector('.class-note-row .class-note-link.active,.class-note-row .class-note-link[aria-current="page"]');
    const row=link?.closest('.class-note-row');
    return row?.dataset?.noteId||null;
  }

  async function openNote(noteId){
    const cn=CN();
    if(cn&&typeof cn.select==='function'){await cn.select(noteId);return true;}
    const click=()=>{
      const row=document.querySelector(`.class-note-row[data-note-id="${cssEscape(noteId)}"]`);
      const link=row?.querySelector('.class-note-link');
      if(!link)return false;
      link.click();
      return true;
    };
    if(click())return true;
    const search=$('class-note-search');
    if(search){search.value='';search.dispatchEvent(new Event('input',{bubbles:true}));}
    const folderSelect=document.querySelector('.notes-sidebar select[aria-label="Filtrar carpeta"]');
    if(folderSelect){folderSelect.value='';folderSelect.dispatchEvent(new Event('change',{bubbles:true}));}
    if(click())return true;
    cn?.render?.();
    if(click())return true;
    say('No se encontró el apunte en la lista.');
    return false;
  }

  async function openLesson(courseId,lessonId){
    try{await window.WorkspaceKeys?.go?.('study');}catch{}
    const stateNow=appState();
    const course=stateNow?.courses?.find(c=>c.id===courseId);
    const lesson=course?.lessons?.find(l=>l.id===lessonId);
    if(!lesson)return false;
    const button=[...document.querySelectorAll('.lesson-link')].find(b=>b.textContent.includes(lesson.title));
    if(button){button.click();return true;}
    say('No se pudo abrir la clase.');
    return false;
  }

  // === Escritura en el editor real (sin tocar nodos del editor en vivo) ===
  function appendToWriting(text){
    const noteId=getActiveNoteId();
    const note=noteId?byId(noteId):null;
    const extra=text;
    const pageCell=note?.documentId?document.querySelector(`.note-page-cell[data-page="${note.page||1}"] textarea`):null;
    if(pageCell){
      pageCell.value=pageCell.value.trim()?pageCell.value.replace(/\s*$/,'')+'\n\n'+extra:extra;
      pageCell.dispatchEvent(new Event('input',{bubbles:true}));
      return true;
    }
    const content=$('class-note-content');
    if(!content)return false;
    const value=content.value;
    content.value=value.trim()?value.replace(/\s*$/,'')+'\n\n'+extra:extra;
    content.dispatchEvent(new Event('input',{bubbles:true}));
    return true;
  }

  async function insertConceptCard(conceptName){
    if(!getActiveNoteId()){say('Abrí un apunte guardado antes de insertar una ficha.');return false;}
    if(!String(conceptName||'').trim())return false;
    if(!appendToWriting(createConceptCard(conceptName))){say('No hay un apunte abierto para insertar la ficha.');return false;}
    const cn=CN();
    if(typeof cn?.flush==='function')await cn.flush();
    if(typeof cn?.render==='function')cn.render();
    await renderNoteListBadges();
    renderPanel();
    say('Ficha de concepto insertada.');
    return true;
  }

  // === Panel ===
  const TABS=[['references','Referencias'],['properties','Propiedades'],['concept','Ficha'],['errors','Errores'],['filters','Filtros']];

  function ensurePanel(){
    const main=$('main');
    if(!main||!main.querySelector('.class-notes-layout')){if(panel){panel.remove();panel=null;}return null;}
    if(panel&&panel.isConnected&&panel.parentElement===main)return panel;
    if(panel)panel.remove();
    panel=E('details',{id:'study-tools-panel',class:'study-tools-panel'},
      E('summary',{class:'study-tools-summary'},
        E('span',{class:'study-tools-summary-title'},'Herramientas de estudio'),
        E('span',{class:'study-tools-summary-hint'},'referencias · fichas · propiedades')
      ),
      E('div',{class:'study-tools-body'},
        E('div',{class:'study-tools-tabs'}),
        E('div',{class:'study-tools-content'})
      )
    );
    main.append(panel);
    return panel;
  }

  function renderPanel(){
    const section=ensurePanel();
    if(!section)return;
    const tabs=section.querySelector('.study-tools-tabs');
    const content=section.querySelector('.study-tools-content');
    if(!tabs||!content)return;
    tabs.replaceChildren(...TABS.map(([key,label])=>E('button',{
      class:'study-tools-tab'+(activeTab===key?' active':''),
      type:'button',
      'aria-pressed':activeTab===key?'true':'false',
      onclick:()=>{activeTab=key;renderPanel();}
    },label)));
    content.replaceChildren();
    const noteId=getActiveNoteId();
    // Un apunte nuevo todavía no está en `state.library.notes`, pero ya tiene
    // identidad y admite propiedades/fichas: usamos el objeto real de ClassNotes.
    const note=(noteId&&byId(noteId))||(noteId?activeNoteObject():null);
    switch(activeTab){
      case 'references':renderReferencesTab(content,note);break;
      case 'properties':renderPropertiesTab(content,note);break;
      case 'concept':renderConceptTab(content,note);break;
      case 'errors':renderErrorsTab(content,note);break;
      case 'filters':renderFiltersTab(content);break;
    }
  }

  function activeNoteTitle(note){
    if(note)return noteTitle(note);
    const button=$('note-name-button');
    return button&&!button.hidden?button.textContent:'';
  }

  function renderReferencesTab(container,note){
    if(!note){container.append(E('p',{class:'muted'},'Abrí o creá un apunte para ver sus referencias.'));return;}
    const backlinks=getBacklinks(note.id);
    const back=E('section',{class:'study-subsection'},E('h3',{},'Notas que enlazan a esta'));
    if(!backlinks.length)back.append(E('p',{class:'muted'},'Ninguna todavía. Escribí [[Título de nota]] en otra nota para enlazarla.'));
    else back.append(E('ul',{class:'study-list'},...backlinks.map(link=>E('li',{class:'study-list-item'},
      E('button',{class:'text-button study-link',type:'button',onclick:()=>openNote(link.note.id)},noteTitle(link.note)),
      E('span',{class:'study-meta'},dateTimeLabel(link.updatedAt))
    ))));
    container.append(back);

    const outgoing=outgoingLinks(note);
    if(outgoing.length){
      const out=E('section',{class:'study-subsection'},E('h3',{},'Enlaces en esta nota'));
      out.append(E('ul',{class:'study-list'},...outgoing.map(link=>E('li',{class:'study-list-item'},
        E('button',{
          class:'text-button study-link'+(link.target?'':' study-link-missing'),
          type:'button',
          onclick:()=>{if(link.target)openNote(link.target.id);else say(`La nota «${link.title}» no existe todavía.`);}
        },link.title),
        E('span',{class:'study-meta'},link.target?'existe':'sin apunte')
      ))));
      container.append(out);
    }

    const mentions=getMentions(noteTitle(note)).filter(m=>!(m.kind==='apunte'&&linksOf(byId(m.id)).includes(normalizeTitle(noteTitle(note)))));
    if(mentions.length){
      const section=E('section',{class:'study-subsection'},E('h3',{},'Menciones en tu material'));
      section.append(E('ul',{class:'study-list'},...mentions.map(mention=>{
        const label={apunte:'apunte',clase:'clase',ejercicio:'ejercicio'}[mention.kind]||mention.kind;
        return E('li',{class:'study-list-item study-mention'},
          E('button',{
            class:'text-button study-link',
            type:'button',
            onclick:()=>{if(mention.kind==='apunte')openNote(mention.id);else openLesson(mention.courseId,mention.lessonId);}
          },`${mention.title}`),
          E('span',{class:'study-badge'},label),
          mention.snippet?E('span',{class:'study-snippet'},mention.snippet):null
        );
      })));
      container.append(section);
    }
  }

  function propertyRow(label,control,hint){
    return E('div',{class:'study-property-row'},
      E('label',{},label),
      control,
      hint?E('p',{class:'study-hint'},hint):null
    );
  }

  function renderPropertiesTab(container,note){
    if(!note){container.append(E('p',{class:'muted'},'Abrí o creá un apunte para completar sus propiedades.'));return;}
    const props=getNoteProperties(note.id)||defaultStudy();
    const section=E('div',{class:'study-properties'});

    const materia=E('input',{type:'text',value:props.materia,placeholder:'Ej: Análisis matemático','aria-label':'Materia','data-study-field':'materia',
      onchange:event=>saveAndRefresh(note.id,{materia:event.target.value})});
    const unidad=E('input',{type:'text',value:props.unidad,placeholder:'Ej: Unidad 3 · Derivadas','aria-label':'Unidad','data-study-field':'unidad',
      onchange:event=>saveAndRefresh(note.id,{unidad:event.target.value})});
    const parcial=E('input',{type:'date',value:props.parcialDate||'','aria-label':'Fecha del parcial','data-study-field':'parcialDate',
      onchange:event=>saveAndRefresh(note.id,{parcialDate:event.target.value||null})});
    const practice=E('input',{type:'checkbox',checked:props.needsPractice,'aria-label':'Necesito practicar','data-study-field':'needsPractice',
      onchange:event=>saveAndRefresh(note.id,{needsPractice:event.target.checked})});

    section.append(
      propertyRow('Materia',materia),
      propertyRow('Unidad',unidad),
      propertyRow('Fecha parcial',parcial),
      propertyRow('Repaso',E('label',{class:'study-property-checkbox'},practice,E('span',{},'Necesito practicar')),'Marcar es tu recordatorio de repaso; no acredita dominio.')
    );
    container.append(section);
    container.append(E('p',{class:'study-note'},'Estas propiedades se guardan como metadata de este apunte, con o sin curso activo.'));
  }

  async function saveAndRefresh(noteId,patch){
    try{await saveStudy(noteId,patch);}catch(error){say(error.message);}
    await renderNoteListBadges();
    renderPanel();
  }

  function renderConceptTab(container,note){
    if(!note){container.append(E('p',{class:'muted'},'Abrí un apunte para insertar una ficha.'));return;}
    const actions=E('form',{class:'study-inline-form',onsubmit:event=>{
      event.preventDefault();
      const input=event.target.querySelector('input');
      insertConceptCard(input.value);
      input.value='';
    }},
      E('input',{type:'text',placeholder:'Nombre del concepto','aria-label':'Nombre del concepto',required:'required'}),
      E('button',{class:'quiet',type:'submit'},'Insertar ficha')
    );
    container.append(actions);
    container.append(E('p',{class:'study-note'},'La ficha se agrega al final del apunte, sin reemplazar tu borrador. Secciones: definición propia, ejemplo, contraejemplo, fuente y pregunta de comprensión.'));
    const preview=E('div',{class:'study-card-preview'});
    for(const part of ['Definición propia','Ejemplo','Contraejemplo','Fuente','Pregunta de comprensión']){
      preview.append(E('div',{class:'card-section'},
        E('div',{class:'card-section-label'},part),
        E('div',{class:'card-section-content'},'[Tu contenido aquí]')
      ));
    }
    container.append(preview);
  }

  function errorEntry(entry){
    const type=entry.errorType||'concepto';
    return E('article',{class:'study-error-entry'},
      E('div',{class:'study-error-head'},
        E('span',{class:'study-error-concept'},entry.concept||'Sin concepto'),
        E('span',{class:'study-badge'},type),
        E('span',{class:'study-meta'},dateTimeLabel(entry.createdAt))
      ),
      entry.description?E('p',{},entry.description):null,
      entry.correction?E('p',{class:'study-error-correction'},E('strong',{},'Corrección: '),entry.correction):null
    );
  }

  function renderErrorsTab(container,note){
    if(!note){container.append(E('p',{class:'muted'},'Abrí un apunte para registrar errores de parcial.'));return;}
    const props=getNoteProperties(note.id)||defaultStudy();
    const concept=E('input',{type:'text',value:activeNoteTitle(note),'aria-label':'Concepto o ejercicio'});
    const type=E('select',{'aria-label':'Tipo de error'},...ERROR_TYPES.map(t=>E('option',{value:t},t)));
    const description=E('textarea',{rows:2,placeholder:'¿Qué error cometiste?','aria-label':'Descripción del error'});
    const correction=E('textarea',{rows:2,placeholder:'¿Cuál es la corrección?','aria-label':'Corrección'});
    const form=E('form',{class:'study-error-form',onsubmit:async event=>{
      event.preventDefault();
      try{
        await logPartialError({concept:concept.value,errorType:type.value,description:description.value,correction:correction.value});
        description.value='';correction.value='';
        say('Error registrado.');
        await renderNoteListBadges();
      }catch(error){say(error.message);}
      renderPanel();
    }},
      propertyRow('Concepto',concept),
      propertyRow('Tipo',type),
      propertyRow('Qué pasó',description),
      propertyRow('Corrección',correction),
      E('div',{class:'study-form-actions'},E('button',{class:'quiet',type:'submit'},'Registrar error'))
    );
    container.append(form);
    container.append(E('p',{class:'study-note'},'El registro es tu material de repaso, no una nota ni evidencia de dominio.'));
    const errors=props.errors||[];
    container.append(E('h3',{},'Errores registrados'));
    if(!errors.length)container.append(E('p',{class:'muted'},'Todavía no registraste errores en este apunte.'));
    else container.append(E('div',{class:'study-error-list'},...errors.map(errorEntry)));
  }

  function renderFiltersTab(container){
    const filters=E('form',{class:'study-filters',onsubmit:event=>{event.preventDefault();applyFilters();}});
    const materia=E('select',{'aria-label':'Filtrar por materia'},E('option',{value:''},'Todas las materias'),...getAllMaterias().map(m=>E('option',{value:m},m)));
    const unidad=E('select',{'aria-label':'Filtrar por unidad'},E('option',{value:''},'Todas las unidades'),...getAllUnidades().map(u=>E('option',{value:u},u)));
    const parcial=E('input',{type:'date','aria-label':'Filtrar por fecha de parcial'});
    const practice=E('input',{type:'checkbox','aria-label':'Solo lo que necesito practicar'});
    filters.append(
      propertyRow('Materia',materia),
      propertyRow('Unidad',unidad),
      propertyRow('Fecha parcial',parcial),
      propertyRow('Repaso',E('label',{class:'study-property-checkbox'},practice,E('span',{},'Solo necesito practicar'))),
      E('div',{class:'study-form-actions'},
        E('button',{class:'quiet',type:'submit'},'Aplicar filtros'),
        E('button',{class:'text-button',type:'button',onclick:()=>renderPanel()},'Limpiar')
      )
    );
    const applyFilters=()=>{
      const results=filterNotes({materia:materia.value,unidad:unidad.value,needsPractice:practice.checked,parcialDate:parcial.value||null});
      const existing=container.querySelector('.study-filter-results');
      if(existing)existing.remove();
      const section=E('div',{class:'study-filter-results'},E('h3',{},`Notas que coinciden (${results.length})`));
      if(!results.length)section.append(E('p',{class:'muted'},'Ninguna nota coincide con estos filtros.'));
      else for(const note of results){
        const props=getNoteProperties(note.id)||defaultStudy();
        const badges=[];
        if(props.needsPractice)badges.push(E('span',{class:'study-badge practice'},'Practicar'));
        if(props.parcialDate)badges.push(E('span',{class:'study-badge'},props.parcialDate));
        section.append(E('div',{class:'study-filter-result'},
          E('button',{class:'text-button study-link',type:'button',onclick:()=>openNote(note.id)},noteTitle(note)),
          E('span',{class:'study-meta'},[props.materia,props.unidad].filter(Boolean).join(' · ')||'Sin materia ni unidad'),
          ...badges
        ));
      }
      container.append(section);
    };
    container.append(filters);
  }

  // === Indicadores en la lista de apuntes ===
  async function renderNoteListBadges(){
    const rows=document.querySelectorAll('.class-note-row');
    for(const row of rows){
      const noteId=row.dataset?.noteId;
      const existing=row.querySelector('.note-study-badges');
      if(existing)existing.remove();
      if(!noteId)continue;
      const props=getNoteProperties(noteId);
      if(!props)continue;
      const badges=[];
      if(props.needsPractice)badges.push(E('span',{class:'note-study-badge practice'},'Practicar'));
      if(props.parcialDate)badges.push(E('span',{class:'note-study-badge'},'Parcial'));
      if(badges.length)row.append(E('div',{class:'note-study-badges'},...badges));
    }
  }

  // === Enganche y ciclo de vida ===
  function hookRender(){
    const cn=CN();
    if(renderHooked||!cn||typeof cn.render!=='function')return;
    const original=cn.render;
    cn.render=function(){
      const result=original.apply(this,arguments);
      try{onRender();}catch(error){console.error('StudyTools',error);}
      return result;
    };
    renderHooked=true;
  }

  function onRender(){
    if(!document.querySelector('.class-notes-layout')){if(panel){panel.remove();panel=null;}return;}
    ensurePanel();
    renderPanel();
    renderNoteListBadges();
  }

  function init(){
    hookRender();
    onRender();
    if(typeof MutationObserver!=='undefined'&&!window.__studyToolsObserver){
      const observer=new MutationObserver(()=>{
        if(!document.querySelector('.class-notes-layout')){if(panel){panel.remove();panel=null;}return;}
        if(!panel||!panel.isConnected)onRender();
      });
      observer.observe(document.body,{childList:true,subtree:true});
      window.__studyToolsObserver=observer;
    }
  }

  // === API pública ===
  if(typeof document!=='undefined'&&!window.__studyToolsAutoStarted){
    window.__studyToolsAutoStarted=true;
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
    else init();
  }
  return {
    init,
    refresh:onRender,
    extractWikilinks,
    normalizeTitle,
    findNoteByTitle,
    getBacklinks,
    outgoingLinks,
    getMentions,
    getActiveNoteId,
    openNote,
    openLesson,
    createConceptCard,
    insertConceptCard,
    getNoteProperties,
    setProperty,
    saveStudy,
    logPartialError,
    filterNotes,
    getAllMaterias,
    getAllUnidades,
    studyByNote,
    CONCEPT_CARD_TEMPLATE,
    ERROR_TYPES
  };
})();

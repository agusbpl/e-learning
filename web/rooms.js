'use strict';
// Requests carry their room explicitly: two tabs can study different rooms safely.
const GlosaRoom = (() => {
  let id=localStorage.getItem('glosa-active-room')||'primer-trazo';
  const prefix=id==='local'?'':'glosa:'+id+':';
  const storage={getItem:key=>localStorage.getItem(prefix+key),setItem:(key,value)=>localStorage.setItem(prefix+key,value),removeItem:key=>localStorage.removeItem(prefix+key)};
  const originalFetch=window.fetch.bind(window);
  let redirecting=false;
  const url=path=>{
    const target=new URL(path,location.origin);
    if(target.origin===location.origin&&/^\/(api|sources|documents)\//.test(target.pathname))target.searchParams.set('room',id);
    return target.origin===location.origin?target.pathname+target.search+target.hash:target.href;
  };
  // A retired installation keeps no 'local' room: the server marks the response
  // and the client just moves to the room it points at (the tutorial), so stale
  // 'local' selections never render a phantom local card.
  const followRoom=response=>{const next=response.headers.get('X-Glosa-Room-Redirect');if(next&&next!==id&&!redirecting){redirecting=true;localStorage.setItem('glosa-active-room',next);location.reload();}return response;};
  window.fetch=(input,options={})=>{
    const target=new URL(typeof input==='string'?input:input.url,location.origin);
    if(target.origin===location.origin&&/^\/(api|sources|documents)\//.test(target.pathname)){
      const headers=new Headers(options.headers||(input instanceof Request?input.headers:undefined));
      if(!headers.has('X-Glosa-Room'))headers.set('X-Glosa-Room',id);
      options={...options,headers};
    }
    return originalFetch(input,options).then(followRoom);
  };
  async function request(path,body){
    const response=await originalFetch(path,{headers:{'Content-Type':'application/json','X-Glosa-Room':'local'},...(body?{method:'POST',body:JSON.stringify(body)}:{})});
    const result=await response.json();if(!response.ok)throw new Error(result.error);return result;
  }
  async function activate(next){
    // Flush note autosaves and session time in the OLD room before reloading.
    if(typeof ClassNotes!=='undefined')await ClassNotes.flush();
    if(typeof flushTime==='function')await flushTime();
    localStorage.setItem('glosa-active-room',next);location.reload();
  }
  // The dialog markup lives in index.html; the vault presentation is injected here.
  const BOVEDAS_CSS=`
#rooms-dialog .boveda-lead{font:14px/1.7 var(--serif);margin:0 0 4px}
#rooms-dialog .boveda-section{margin:22px 0 0;padding-top:16px;border-top:1px solid var(--line)}
#rooms-dialog .boveda-section h3{margin:0 0 6px;font:600 12px system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--ink)}
#rooms-dialog .boveda-current{border:1px solid var(--line);border-left:3px solid var(--green);border-radius:6px;padding:14px 16px;margin:16px 0 0;background:var(--pale)}
#rooms-dialog .boveda-card-name{font:600 16px var(--serif)}
#rooms-dialog .boveda-path{display:block;font:11px ui-monospace,monospace;color:var(--muted);overflow-wrap:anywhere;margin-top:4px}
#rooms-dialog .boveda-path-row{display:flex;align-items:flex-end;justify-content:space-between;gap:12px}
#rooms-dialog .boveda-copy{font-size:11px;white-space:nowrap;color:var(--green)}
#rooms-dialog .boveda-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
#rooms-dialog .boveda-chip{font:11px system-ui,sans-serif;color:var(--green);background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:2px 9px}
#rooms-dialog .boveda-row{display:flex;align-items:flex-start;gap:10px;border-bottom:1px solid var(--line)}
#rooms-dialog .boveda-row .room-choice{flex:1;border-bottom:0;padding:10px 0}
#rooms-dialog .boveda-rename{font-size:11px;color:var(--muted);padding:10px 0;white-space:nowrap}
#rooms-dialog .boveda-group{margin:14px 0 2px;font:600 10px system-ui,sans-serif;letter-spacing:1.2px;text-transform:uppercase;color:var(--muted)}
#rooms-dialog .boveda-note{margin:10px 0 0}
`;
  const human=bytes=>bytes>=1073741824?(bytes/1073741824).toFixed(1)+' GB':bytes>=1048576?(bytes/1048576).toFixed(1)+' MB':bytes>=1024?Math.round(bytes/1024)+' KB':bytes+' B';
  const when=epoch=>{try{return new Date(epoch*1000).toLocaleString('es-AR',{dateStyle:'medium',timeStyle:'short'});}catch{return new Date(epoch*1000).toLocaleString();}};
  const chips=item=>{
    const box=document.createElement('span');box.className='boveda-chips';
    const counts=item.contents||{};
    const labels=[[counts.courses,'curso','cursos'],[counts.documents,'fuente','fuentes'],[counts.notes,'apunte','apuntes'],[counts.conversation,'mensaje con el tutor','mensajes con el tutor'],[counts.events,'registro','registros']];
    for(const [value,one,many] of labels){
      if(typeof value!=='number'||value<=0)continue;
      const chip=document.createElement('span');chip.className='boveda-chip';chip.textContent=value+' '+(value===1?one:many);box.append(chip);
    }
    if(item.files){const chip=document.createElement('span');chip.className='boveda-chip';chip.textContent=human(item.files.bytes)+' en la carpeta';box.append(chip);}
    if(!box.childElementCount){const chip=document.createElement('span');chip.className='boveda-chip';chip.textContent=item.contents===null?'Contenido no disponible':'Sin contenido todavía';box.append(chip);}
    return box;
  };
  const decorate=()=>{
    if(document.getElementById('bovedas-css'))return;
    const dialog=document.getElementById('rooms-dialog');
    const by=name=>document.getElementById(name);
    const list=by('room-list'),create=by('pliego-create-form'),backups=by('margen-backups'),status=by('room-status'),download=by('room-download');
    const details=[...dialog.querySelectorAll('details')];
    const margenDetails=details.find(node=>node.contains(by('margen-form')));
    const importDetails=details.find(node=>node.contains(by('room-upload')));
    const actions=dialog.querySelector('.dialog-actions');
    const eyebrow=dialog.querySelector('.eyebrow'),heading=dialog.querySelector('h2'),intro=[...dialog.children].find(node=>node.tagName==='P');
    if(!list||!create||!backups||!status||!download||!margenDetails||!importDetails||!actions||!eyebrow||!heading||!intro)return;
    const style=document.createElement('style');style.id='bovedas-css';style.textContent=BOVEDAS_CSS;document.head.append(style);
    eyebrow.textContent='TU MARGEN';
    heading.textContent='Margen';
    intro.className='boveda-lead muted';
    intro.textContent='Tu Margen es una carpeta visible de esta computadora con tus materias adentro. Cada pliego es una subcarpeta con sus cursos, PDFs, apuntes, historial y conversación con el tutor. Pedile a tu agente: «Usá el MCP de autoría para crear un pliego con /ruta/a/mis/materiales». El pliego completo aparece acá, listo para estudiar. Crear, abrir o cambiar de pliego no borra nada: cada uno guarda su propio historial con los mismos IDs.';
    margenDetails.querySelector('summary').textContent='Dónde está tu Margen · Carpeta';
    margenDetails.querySelector('p.muted').textContent='Tu Margen contiene un pliego por subcarpeta, con nombres que ves en el explorador de archivos. Cambiar la carpeta no mueve archivos: solo le dice a Glosa dónde buscarlos.';
    const margenInfo=document.createElement('p');margenInfo.id='boveda-margen-info';margenInfo.className='muted';
    by('margen-form').after(margenInfo);
    importDetails.querySelector('summary').textContent='Importar una copia como pliego nuevo';
    importDetails.querySelector('p.muted').textContent='Crea un pliego NUEVO con una copia de los datos del respaldo (ZIP o carpeta). El pliego original queda intacto y todo conserva sus IDs.';
    download.textContent='↓ Exportar este pliego · ZIP con PDFs';
    const section=(title,help,nodes)=>{
      const box=document.createElement('section');box.className='boveda-section';
      const label=document.createElement('h3');label.textContent=title;box.append(label);
      if(help){const note=document.createElement('p');note.className='muted';note.textContent=help;box.append(note);}
      for(const node of nodes)box.append(node);
      return box;
    };
    const current=document.createElement('div');current.id='boveda-current';current.className='boveda-current';
    const listSection=section('Tus pliegos','Cada fila es un pliego: una subcarpeta de tu Margen con su contenido. Elegí uno para abrirlo; el que está abierto aparece marcado. Dos pliegos pueden tener cursos o apuntes con el mismo nombre sin mezclarse: cada uno vive en su subcarpeta.',[list]);
    const createSection=section('Crear un pliego nuevo','Crea una subcarpeta nueva dentro del Margen con una base vacía. Se abre al terminar y los pliegos existentes no cambian.',[create]);
    const backupSection=section('Copias detectadas en el Margen','Subcarpetas que parecen respaldos de Glosa. Importarlas crea un pliego nuevo con una copia; nunca sincronizan ni sobrescriben.',[backups]);
    backupSection.id='boveda-backups';
    dialog.replaceChildren(eyebrow,heading,intro,current,AuthorPrompt.mount(),listSection,createSection,margenDetails,backupSection,importDetails,status,download,actions);
  };
  async function renameVault(item,status){
    const chosen=prompt('Nuevo nombre del pliego «'+item.title+'».\nTambién se renombra su carpeta en el Margen; el ID y el historial no cambian.',item.title);
    if(chosen===null)return;
    const title=chosen.trim();
    if(!title||title===item.title)return;
    // Save pending notes first: the folder is moved right after, and an autosave
    // racing the move must not land in the old path.
    try{if(typeof ClassNotes!=='undefined')await ClassNotes.flush();if(typeof flushTime==='function')await flushTime();}catch{}
    status.textContent='Renombrando el pliego y su carpeta…';
    try{await request('/api/rooms/rename',{id:item.id,title});await open();}
    catch(error){status.textContent=error.message==='No encontrado.'?'Renombrar todavía no está publicado en este servidor: actualizá Glosa. Mientras tanto, cerrá el pliego y renombrá su carpeta a mano.':error.message;}
  }
  const renderCurrent=(result,details)=>{
    const card=document.getElementById('boveda-current');card.replaceChildren();
    // The request that lists rooms runs as 'local'; the open vault is the client-side id.
    const room=result.rooms.find(entry=>entry.id===id)||{id,title:'Pliego abierto'};
    const item=details.get(room.id)||(room.id==='local'&&result.local?result.local:undefined);
    const label=document.createElement('div');label.className='boveda-card-name';label.textContent=room.id==='local'?'Biblioteca local':room.title;
    card.append(label);
    if(item){
      const row=document.createElement('div');row.className='boveda-path-row';
      const path=document.createElement('span');path.className='boveda-path';path.textContent=item.path;
      const copy=document.createElement('button');copy.type='button';copy.className='text-button boveda-copy';copy.textContent='Copiar ruta';
      copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(item.path);copy.textContent='Ruta copiada';setTimeout(()=>{copy.textContent='Copiar ruta';},2000);}catch{copy.textContent='No se pudo copiar';}});
      row.append(path,copy);card.append(row,chips(item));
      const note=document.createElement('p');note.className='muted boveda-note';
      note.textContent=(item.modified?'Última modificación: '+when(item.modified)+'. ':'')+'Todo lo tuyo vive en esa carpeta: cursos, PDFs, apuntes y conversación. Cambiar de pliego no copia ni borra nada.';
      card.append(note);
    }else{
      const note=document.createElement('p');note.className='muted boveda-note';
      note.textContent=room.id==='local'?'La biblioteca local vive en la carpeta de datos de la propia aplicación y es tu espacio de trabajo de siempre: ahí están tus cursos, tus apuntes y tu historial. Podés trasladarla a tu Margen como un pliego visible sin perder IDs ni borradores.':room.id==='primer-trazo'?'Primer trazo es el tutorial incluido. Sus datos se guardan aparte, en una subcarpeta de los datos de la aplicación, y no se agregan a tus cursos ni a tu historial.':'Espacio sin carpeta de pliego propia.';
      card.append(note);
    }
  };
  const rowFor=(room,item,status)=>{
    const row=document.createElement('div');row.className='boveda-row';
    const button=document.createElement('button');button.type='button';button.className='room-choice text-button';
    const name=document.createElement('span');name.className='boveda-row-name';name.textContent=(room.id==='local'?'Biblioteca local':room.title)+(room.id===id?' · abierto':'');
    button.append(name);
    if(item){
      const path=document.createElement('span');path.className='boveda-path';path.textContent=item.path;
      button.append(path,chips(item));
    }else{
      const note=document.createElement('span');note.className='boveda-path';note.textContent=room.id==='local'?'Biblioteca local · carpeta de datos de la aplicación':'Tutorial incluido · no toca tus cursos reales';
      button.append(note);
    }
    button.addEventListener('click',()=>activate(room.id).catch(e=>status.textContent=e.message));
    row.append(button);
    if(item){
      const rename=document.createElement('button');rename.type='button';rename.className='text-button boveda-rename';rename.textContent='Renombrar';
      rename.title='Renombra el pliego y su carpeta en el Margen';
      rename.addEventListener('click',()=>renameVault(item,status));
      row.append(rename);
    }
    return row;
  };
  const renderList=(result,details,list,status)=>{
    list.replaceChildren();
    const vaults=result.rooms.filter(room=>details.has(room.id));
    const others=result.rooms.filter(room=>!details.has(room.id));
    if(!vaults.length){const empty=document.createElement('p');empty.className='muted';empty.textContent='Todavía no hay pliegos: creá el primero en el bloque siguiente.';list.append(empty);}
    for(const room of vaults)list.append(rowFor(room,details.get(room.id),status));
    if(others.length){
      const group=document.createElement('div');group.className='boveda-group';group.textContent=result.rooms.some(room=>room.id==='local')?'Biblioteca local y tutorial':'Tutorial';list.append(group);
      for(const room of others)list.append(rowFor(room,null,status));
    }
  };
  const renderMargen=result=>{
    const info=document.getElementById('boveda-margen-info');
    const origins={environment:'fijada con la variable GLOSA_MARGEN_DIR',settings:'guardada desde esta pantalla',default:'carpeta por defecto ~/Margen'};
    const count=result.pliegos.length;
    info.textContent='Tu Margen está en «'+result.margen.path+'» ('+(origins[result.margen.source]||result.margen.source)+'). Hay '+count+' '+(count===1?'pliego encontrado':'pliegos encontrados')+'.';
  };
  async function open(){
    decorate();
    const dialog=document.getElementById('rooms-dialog'),list=document.getElementById('room-list'),status=document.getElementById('room-status');
    status.textContent='';if(!dialog.open)dialog.showModal();list.replaceChildren();
    try{const result=await request('/api/rooms');
      // Obsolete local selection in a retired installation: follow the room the
      // server resolved instead of rendering a local card that no longer exists.
      if(id==='local'&&result.active&&result.active!=='local'){await activate(result.active);return;}
      const details=new Map(result.pliegos.map(item=>[item.id,item]));
      if(result.local)details.set(result.local.id,result.local);
      renderCurrent(result,details);
      renderList(result,details,list,status);
      renderMargen(result);
      document.getElementById('margen-folder').value=result.margen.path;
      document.getElementById('margen-folder').disabled=result.margen.source==='environment';
      document.querySelector('#margen-form button').disabled=result.margen.source==='environment';
      const backups=document.getElementById('margen-backups');backups.replaceChildren();
      for(const backup of result.backups){const button=document.createElement('button');button.className='text-button';button.textContent='Importar copia · '+backup.title;button.addEventListener('click',async()=>{button.disabled=true;try{const item=await request('/api/rooms/import',{folder:backup.folder});await activate(item.id);}catch(error){status.textContent=error.message;button.disabled=false;}});backups.append(button);}
      document.getElementById('boveda-backups').hidden=result.backups.length===0;
      status.textContent=result.warnings.join(' · ');
    }catch(error){status.textContent=error.message;}
  }
  document.addEventListener('DOMContentLoaded',()=>{
    decorate();
    document.getElementById('rooms-button').addEventListener('click',open);
    document.getElementById('margen-form').addEventListener('submit',async event=>{
      event.preventDefault();const button=event.submitter;button.disabled=true;
      try{await request('/api/margen',{folder:document.getElementById('margen-folder').value});await open();}
      catch(error){document.getElementById('room-status').textContent=error.message;}finally{button.disabled=false;}
    });
    document.getElementById('pliego-create-form').addEventListener('submit',async event=>{
      event.preventDefault();const button=event.submitter;button.disabled=true;
      try{const item=await request('/api/rooms/create',{title:document.getElementById('pliego-title').value});await activate(item.id);}
      catch(error){document.getElementById('room-status').textContent=error.message;}finally{button.disabled=false;}
    });
    document.querySelectorAll('a[href^="/api/export"]').forEach(a=>a.href=url(a.getAttribute('href')));
    document.getElementById('room-download').href=url('/api/rooms/export');
    document.getElementById('room-download').addEventListener('click',async event=>{
      event.preventDefault();const status=document.getElementById('room-status');
      try{
        status.textContent='Guardando apuntes y preparando respaldo…';
        if(typeof ClassNotes!=='undefined')await ClassNotes.flush();
        if(typeof flushTime==='function')await flushTime();
        const response=await fetch(url('/api/rooms/export'));
        if(!response.ok)throw new Error((await response.json()).error);
        const address=URL.createObjectURL(await response.blob()),link=document.createElement('a');
        link.href=address;link.download='pliego-glosa.zip';document.body.append(link);link.click();link.remove();
        setTimeout(()=>URL.revokeObjectURL(address),10000);status.textContent='Pliego exportado con sus PDFs y registro guardado.';
      }catch(error){status.textContent=error.message;}
    });
    document.getElementById('room-folder-form').addEventListener('submit',async event=>{
      event.preventDefault();const status=document.getElementById('room-status'),button=event.submitter;button.disabled=true;
      try{status.textContent='Importando pliego…';const result=await request('/api/rooms/import',{folder:document.getElementById('room-folder').value});await activate(result.id);}
      catch(error){status.textContent=error.message;}finally{button.disabled=false;}
    });
    document.getElementById('room-upload').addEventListener('change',async event=>{
      const file=event.target.files[0],status=document.getElementById('room-status');if(!file)return;
      if(file.size>60_000_000){status.textContent='El ZIP admite hasta 60 MB.';return;}
      event.target.disabled=true;status.textContent='Comprobando e importando pliego…';
      try{const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});const result=await request('/api/rooms/import',{base64:encoded});await activate(result.id);}
      catch(error){status.textContent=error.message;}finally{event.target.disabled=false;event.target.value='';}
    });
  });
  return {id,storage,url,open,activate};
})();

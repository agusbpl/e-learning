'use strict';
// Requests carry their room explicitly: two tabs can study different rooms safely.
const GlosaRoom = (() => {
  const id=localStorage.getItem('glosa-active-room')||'primer-trazo';
  const prefix=id==='local'?'':'glosa:'+id+':';
  const storage={getItem:key=>localStorage.getItem(prefix+key),setItem:(key,value)=>localStorage.setItem(prefix+key,value),removeItem:key=>localStorage.removeItem(prefix+key)};
  const originalFetch=window.fetch.bind(window);
  const url=path=>{
    const target=new URL(path,location.origin);
    if(target.origin===location.origin&&/^\/(api|sources|documents)\//.test(target.pathname))target.searchParams.set('room',id);
    return target.origin===location.origin?target.pathname+target.search+target.hash:target.href;
  };
  window.fetch=(input,options={})=>{
    const target=new URL(typeof input==='string'?input:input.url,location.origin);
    if(target.origin===location.origin&&/^\/(api|sources|documents)\//.test(target.pathname)){
      const headers=new Headers(options.headers||(input instanceof Request?input.headers:undefined));
      if(!headers.has('X-Glosa-Room'))headers.set('X-Glosa-Room',id);
      options={...options,headers};
    }
    return originalFetch(input,options);
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
  async function open(){
    const dialog=document.getElementById('rooms-dialog'),list=document.getElementById('room-list'),status=document.getElementById('room-status');
    status.textContent='';if(!dialog.open)dialog.showModal();list.replaceChildren();
    try{const result=await request('/api/rooms');
      for(const room of result.rooms){const button=document.createElement('button');button.className='room-choice text-button';button.textContent=room.title+(room.id===id?' · abierta':'');button.addEventListener('click',()=>activate(room.id).catch(e=>status.textContent=e.message));list.append(button);}
      document.getElementById('margen-folder').value=result.margen.path;
      document.getElementById('margen-folder').disabled=result.margen.source==='environment';
      document.querySelector('#margen-form button').disabled=result.margen.source==='environment';
      const backups=document.getElementById('margen-backups');backups.replaceChildren();
      for(const backup of result.backups){const button=document.createElement('button');button.className='text-button';button.textContent='Importar copia · '+backup.title;button.addEventListener('click',async()=>{button.disabled=true;try{const item=await request('/api/rooms/import',{folder:backup.folder});await activate(item.id);}catch(error){status.textContent=error.message;button.disabled=false;}});backups.append(button);}
      status.textContent=result.warnings.join(' · ');
    }catch(error){status.textContent=error.message;}
  }
  document.addEventListener('DOMContentLoaded',()=>{
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

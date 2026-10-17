'use strict';
// This assistant only composes text. It does not launch an agent or create a vault.
const AuthorPrompt = (() => {
  const node=(tag,attrs={},text)=>{
    const el=document.createElement(tag);
    for(const [key,value] of Object.entries(attrs))el.setAttribute(key,value);
    if(text!==undefined)el.textContent=text;
    return el;
  };
  function build(values,setup={}){
    if(!values.folder.trim())return '';
    const lines=[`Usá el MCP de Glosa para crear un pliego con los materiales del directorio ${JSON.stringify(values.folder.trim())}.`,
      'Tomá ese directorio como fuente y guardá el pliego resultante como un directorio dentro del Margen configurado'+(setup.margen?': '+JSON.stringify(setup.margen):' en Glosa')+'.'];
    lines.push('Si el MCP de Glosa no está disponible, configurá y conectá el servidor de autoría'+(setup.authorCommand?' mediante stdio con el comando '+JSON.stringify(setup.authorCommand):' de esta instalación')+' en tu cliente y continuá con el encargo.');
    if(values.title.trim())lines.push('Materia o nombre del pliego: '+values.title.trim()+'.');
    if(values.mode==='exam'){
      lines.push('Quiero preparar un examen.');
      if(values.kind)lines.push('Tipo: '+values.kind+'.');
      if(values.date)lines.push('Fecha: '+values.date+(values.time?' a las '+values.time:'')+'.');
      else if(values.time)lines.push('Hora: '+values.time+'; fecha aún no indicada.');
      if(values.scope.trim())lines.push('Temario e indicaciones docentes: '+values.scope.trim());
      if(values.availability.trim())lines.push('Disponibilidad: '+values.availability.trim());
    }
    if(values.preferences.trim())lines.push('Preferencias y contexto adicional: '+values.preferences.trim());
    return lines.join('\n\n');
  }
  function mount(){
    const box=node('details',{id:'author-prompt-assistant',class:'boveda-section'});
    box.append(node('summary',{},'Preparar una materia con mi agente'));
    box.append(node('p',{class:'muted'},'Elegí los materiales y copiá el encargo para pegarlo en Codex, OpenCode, Antigravity o tu agente. Los datos del examen son opcionales.'));
    const form=node('form',{id:'author-prompt-form'});
    const fields={};
    const field=(key,label,tag='input',attrs={})=>{
      const wrap=node('label',{},label),input=node(tag,{id:'author-'+key,...attrs});
      fields[key]=input;wrap.append(input);return wrap;
    };
    form.append(field('folder','Carpeta de materiales','input',{type:'text',placeholder:'/ruta/a/mis/materiales',required:'',autocomplete:'off'}));
    const choose=node('button',{type:'button',class:'quiet',id:'author-choose-folder'},'Elegir carpeta');
    form.append(choose);
    const picker=node('section',{id:'author-folder-picker',hidden:'','aria-label':'Elegir carpeta de materiales'});
    picker.append(node('p',{class:'muted'},'Carpetas de la computadora donde corre Glosa. No se suben ni se leen los archivos.'));
    const location=node('p',{class:'boveda-path',id:'author-folder-location'}),folders=node('div',{id:'author-folder-list'});
    const up=node('button',{type:'button',class:'text-button'},'↑ Carpeta superior');
    const use=node('button',{type:'button',class:'quiet',id:'author-use-folder'},'Usar esta carpeta');
    const cancel=node('button',{type:'button',class:'text-button'},'Cerrar selector');
    picker.append(location,up,folders,use,cancel);form.append(picker);
    form.append(field('title','Materia o nombre (opcional)','input',{type:'text',maxlength:'200',placeholder:'Nombre opcional'}));
    const modeWrap=node('label',{},'¿Qué querés preparar?'),mode=node('select',{id:'author-mode'});
    mode.append(node('option',{value:'directory'},'Que el agente revise los materiales y proponga la ruta'),node('option',{value:'exam'},'Preparar un examen'));fields.mode=mode;modeWrap.append(mode);form.append(modeWrap);
    const exam=node('div',{id:'author-exam-fields',hidden:''});
    const kindWrap=field('kind','Tipo de examen (opcional)','select');
    fields.kind.append(node('option',{value:''},'Sin especificar'),...['Teoría','Práctica','Teórico-práctico'].map(value=>node('option',{value},value)));
    exam.append(kindWrap,field('date','Fecha (opcional)','input',{type:'date'}),field('time','Hora (opcional)','input',{type:'time'}),
      field('scope','Temario o indicaciones del docente (opcional)','textarea',{rows:'2',placeholder:'Unidades o temas que querés incluir'}),
      field('availability','Tiempo disponible (opcional)','textarea',{rows:'2',placeholder:'Días y horarios en los que podés estudiar'}));
    form.append(exam,field('preferences','Algo más que deba saber el agente (opcional)','textarea',{rows:'2',placeholder:'Indicaciones opcionales para tu agente'}));
    const previewWrap=node('label',{},'Encargo listo para pegar'),preview=node('textarea',{id:'author-prompt-preview',rows:'10',spellcheck:'false'});
    previewWrap.append(preview);form.append(previewWrap);
    const copy=node('button',{type:'submit',class:'primary',id:'author-copy-prompt',disabled:''},'Copiar');
    const status=node('p',{id:'author-prompt-status',role:'status',class:'muted'});
    form.append(copy,status);box.append(form);
    const style=node('style');style.textContent=`
#author-prompt-form{display:grid;gap:12px;margin-top:16px}
#author-prompt-form label{display:grid;gap:6px;font-size:12px}
#author-prompt-form input,#author-prompt-form select,#author-prompt-form textarea{box-sizing:border-box;width:100%;padding:9px;border:1px solid var(--line);border-radius:5px;background:var(--bg);color:var(--ink);font:13px/1.5 system-ui}
#author-prompt-form button{justify-self:start}
#author-exam-fields{display:grid;gap:12px}
#author-exam-fields[hidden],#author-folder-picker[hidden]{display:none}
#author-folder-picker{padding:14px;border:1px solid var(--line);border-radius:5px}
#author-folder-list{display:grid;max-height:220px;overflow:auto;margin:8px 0}
#author-folder-list button{text-align:left;padding:7px;overflow-wrap:anywhere}
#author-prompt-preview{resize:vertical;min-height:170px}
`;box.append(style);
    let setup={},loaded=false,current='',browseGeneration=0;
    const values=()=>Object.fromEntries(Object.entries(fields).map(([key,input])=>[key,input.value]));
    const update=()=>{
      exam.hidden=mode.value!=='exam';
      preview.value=build(values(),setup);copy.disabled=!preview.value;
      status.textContent='';
    };
    async function browse(path){
      const generation=++browseGeneration;
      status.textContent='Abriendo carpeta…';use.disabled=true;
      try{
        const response=await fetch('/api/author-folders'+(path?'?path='+encodeURIComponent(path):''));
        const result=await response.json();if(!response.ok)throw Error(result.error);
        if(generation!==browseGeneration)return;
        setup=result;loaded=true;current=result.path;location.textContent=current;up.disabled=current===result.parent;
        up.onclick=()=>browse(result.parent);
        folders.replaceChildren();
        for(const dir of result.directories){const button=node('button',{type:'button',class:'text-button'},dir.name);button.onclick=()=>browse(dir.path);folders.append(button);}
        if(!result.directories.length)folders.append(node('p',{class:'muted'},'No hay subcarpetas visibles. Podés usar esta carpeta.'));
        update();status.textContent=result.truncated?'Se muestran las primeras 300 carpetas. Podés escribir la ruta directamente.':'';
        use.disabled=false;
      }catch(error){if(generation===browseGeneration)status.textContent=error.message;}
    }
    box.addEventListener('toggle',()=>{if(box.open&&!loaded)browse('');});
    choose.onclick=()=>{picker.hidden=false;browse(fields.folder.value.trim());};
    use.onclick=()=>{fields.folder.value=current;picker.hidden=true;update();};
    cancel.onclick=()=>{picker.hidden=true;choose.focus();};
    const fieldChanged=event=>{if(Object.values(fields).includes(event.target))update();};
    form.addEventListener('input',fieldChanged);form.addEventListener('change',fieldChanged);
    // Keep edits made to the generated prompt; do not rebuild on preview input.
    preview.addEventListener('input',event=>{event.stopPropagation();copy.disabled=!preview.value.trim();status.textContent='';});
    preview.addEventListener('change',event=>event.stopPropagation());
    form.addEventListener('submit',async event=>{
      event.preventDefault();if(!preview.value.trim())return;
      try{
        if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(preview.value);
        else{preview.focus();preview.select();if(!document.execCommand('copy'))throw Error('No se pudo copiar automáticamente. Seleccioná el texto y copialo.');}
        status.textContent='Copiado. Pegalo en tu agente para empezar.';
      }catch{preview.focus();preview.select();status.textContent='Seleccioná y copiá el texto con Ctrl+C o ⌘C; el navegador no permitió copiar automáticamente.';}
    });
    update();return box;
  }
  return {mount,build};
})();

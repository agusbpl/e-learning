// Native fields remain the source for forms, validation and existing draft handlers.
// Vim edits their text through the same editor used by class notes.
export function installVimFields(){
  const fields=new Map();
  const enabled=()=>window.WorkspaceKeys?.profile?.()!=='vimium';
  const nativeValue=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value');
  function attach(source){
    if(fields.has(source))return fields.get(source).api;
    const host=document.createElement('div');host.className='vim-field';
    if(source.matches('.note-cell-content'))host.classList.add('note-cell-vim');
    if(source.id==='class-note-content')host.classList.add('note-raw-vim');
    host.style.setProperty('--field-lines',Math.max(1,source.rows||3));
    source.after(host);
    const range=source.setSelectionRange.bind(source),originalFocus=source.focus,originalBlur=source.blur,originalSelect=source.select;
    const label=source.getAttribute('aria-label')||source.placeholder||'Texto';
    const api=NoteLiveMarkdown.create(host,nativeValue.get.call(source),text=>{
      nativeValue.set.call(source,text);source.dispatchEvent(new Event('input',{bubbles:true}));
    },{
      plain:true,source,label:'Editor: '+label,
      onSelection:selection=>{range(selection.from,selection.to,selection.anchor>selection.head?'backward':'forward');source.dispatchEvent(new Event('select',{bubbles:true}));},
      onWrite:()=>{source.dispatchEvent(new Event('input',{bubbles:true}));if(source.closest('.note-editor'))return window.ClassNotes?.flush();}
    });
    const sync=()=>api.setText(nativeValue.get.call(source));
    const focus=()=>{const start=source.selectionStart,end=source.selectionEnd,backward=source.selectionDirection==='backward';sync();api.focus();api.enterInsert();api.setSelection(backward?end:start,backward?start:end);source.dispatchEvent(new FocusEvent('focus'));};
    Object.defineProperty(source,'value',{configurable:true,get(){return nativeValue.get.call(this);},set(value){nativeValue.set.call(this,value);sync();}});
    source.focus=focus;source.blur=()=>api.element.blur();
    source.select=()=>{api.focus();api.setSelection(0,api.text().length);};
    source.setSelectionRange=(start,end,direction)=>{range(start,end,direction);api.setSelection(direction==='backward'?end:start,direction==='backward'?start:end);};
    source.addEventListener('input',sync);
    source.classList.add('vim-source');source.setAttribute('aria-hidden','true');
    const invalid=event=>{event.preventDefault();focus();api.element.setAttribute('aria-invalid','true');window.notify?.(source.validationMessage);};
    source.addEventListener('invalid',invalid);
    api.element.addEventListener('blur',event=>source.dispatchEvent(new FocusEvent('blur',{relatedTarget:event.relatedTarget})));
    api.element.addEventListener('keyup',event=>source.dispatchEvent(new KeyboardEvent('keyup',{key:event.key,bubbles:false})));
    // The PDF notebook's #N + Enter behavior still belongs to its original field.
    api.element.addEventListener('keydown',event=>{
      if(event.key!=='Enter'||!source.matches('.note-cell-content')||api.mode()!=='INSERTAR')return;
      const forwarded=new KeyboardEvent('keydown',{key:event.key,ctrlKey:event.ctrlKey,shiftKey:event.shiftKey,altKey:event.altKey,metaKey:event.metaKey,cancelable:true});
      source.dispatchEvent(forwarded);if(forwarded.defaultPrevented){event.preventDefault();event.stopImmediatePropagation();}
    },true);
    fields.set(source,{api,host,sync,invalid,originalFocus,originalBlur,originalSelect,range});
    return api;
  }
  document.addEventListener('focusin',event=>{
    const source=event.target;
    if(!source.matches?.('textarea')||source.disabled||source.readOnly||!enabled())return;
    const start=source.selectionStart,end=source.selectionEnd,backward=source.selectionDirection==='backward';
    const api=attach(source);api.setText(source.value);api.focus();api.enterInsert();api.setSelection(backward?end:start,backward?start:end);
  });
  const observer=new MutationObserver(()=>{
    for(const [source,field] of fields){
      if(!source.isConnected){
        field.api.destroy();field.host.remove();fields.delete(source);
        delete source.value;source.focus=field.originalFocus;source.blur=field.originalBlur;source.select=field.originalSelect;delete source.setSelectionRange;
        source.classList.remove('vim-source');source.removeAttribute('aria-hidden');source.removeEventListener('input',field.sync);source.removeEventListener('invalid',field.invalid);
      }else if(field.host.hidden!==source.hidden)field.host.hidden=source.hidden;
    }
  });
  observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden']});
}

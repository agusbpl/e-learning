// A single Markdown document, with formatting drawn over its original source.
// CodeMirror handles input, selections, composition and undo without HTML-to-MD conversion.
// https://codemirror.net/examples/decoration/
import {EditorState, StateField, StateEffect, Compartment, Transaction} from '@codemirror/state';
import {EditorView, Decoration, WidgetType, keymap, drawSelection} from '@codemirror/view';
import {history, historyKeymap, defaultKeymap, indentWithTab, redo, isolateHistory} from '@codemirror/commands';
import {syntaxTree} from '@codemirror/language';
import {markdown, markdownLanguage, markdownKeymap} from '@codemirror/lang-markdown';
import {GFM} from '@lezer/markdown';
import {vim, Vim, getCM} from '@replit/codemirror-vim';
import {installVimFields} from './fields.js';

const editors=new Map();
const vimEnabled=()=>window.WorkspaceKeys?.profile?.()!=='vimium';
const editorFor=element=>editors.get(element?.closest?.('.cm-editor'));
const modeOf=view=>{const state=getCM(view)?.state.vim;return !state||state.insertMode?'INSERTAR':state.visualMode?'VISUAL':'NORMAL';};
const reportMode=api=>{if(api.element===document.activeElement)document.dispatchEvent(new CustomEvent('glosa-vim-mode',{detail:{element:api.element,mode:api.mode()}}));};
Vim.defineEx('write','w',cm=>{const api=editors.get(cm.cm6.dom);Promise.resolve().then(()=>api?.write()).catch(error=>window.notify?.(error.message));});
Vim.defineEx('quit','q',cm=>window.WorkspaceKeys?.leaveEditor?.(cm.cm6.contentDOM));
Vim.defineEx('wq','wq',cm=>{const api=editors.get(cm.cm6.dom);Promise.resolve().then(()=>api?.write()).then(()=>window.WorkspaceKeys?.leaveEditor?.(api.element)).catch(error=>window.notify?.(error.message));});
window.VimEditors={
  get:editorFor,
  setProfile:enabled=>{for(const api of editors.values())api.setVim(enabled);},
  enterInsert:element=>editorFor(element)?.enterInsert(),
  sourceFor:element=>editorFor(element)?.source||element
};

const focusEffect=StateEffect.define();
const focused=StateField.define({create:()=>false,update:(value,tr)=>tr.effects.find(e=>e.is(focusEffect))?.value??value});
const url=value=>{try{const result=new URL(value,location.href);return /^(https?:|mailto:)$/.test(result.protocol)?result.href:null;}catch{return null;}};

class Bullet extends WidgetType {
  toDOM(){const node=document.createElement('span');node.textContent='•';return node;}
}

class Preview extends WidgetType {
  constructor(source,from,inline=false){super();this.source=source;this.from=from;this.inline=inline;}
  eq(other){return this.source===other.source&&this.from===other.from;}
  toDOM(view){
    const node=document.createElement(this.inline?'span':'div');node.className='cm-md-widget note-markdown';
    const rendered=NoteMarkdown.render(this.source);node.append(...(this.inline&&rendered.firstChild?.tagName==='P'?[...rendered.firstChild.childNodes]:[rendered]));
    node.addEventListener('mousedown',event=>{
      if(event.target.closest('a')&&(event.ctrlKey||event.metaKey))return;
      event.preventDefault();view.dispatch({selection:{anchor:this.from},scrollIntoView:false});view.focus();
    });
    return node;
  }
  ignoreEvent(){return false;}
}

function decorations(state){
  const ranges=[],doc=state.doc;
  const active=node=>state.field(focused)&&state.selection.ranges.some(r=>r.from<=node.to&&r.to>=node.from);
  const mark=(from,to,className,attributes=null)=>{if(to>from)ranges.push(Decoration.mark({class:className,...(attributes?{tagName:'a',attributes}: {})}).range(from,to));};
  const hide=(from,to)=>{if(to>from)ranges.push(Decoration.replace({}).range(from,to));};
  const lines=(from,to,className)=>{for(let line=doc.lineAt(from);line.from<=to;){ranges.push(Decoration.line({class:className}).range(line.from));if(line.to>=doc.length)break;line=doc.line(line.number+1);}};
  syntaxTree(state).iterate({enter:ref=>{
    const node=ref.node,name=node.name,source=doc.sliceString(node.from,node.to);
    if(/^(Table|Image|HorizontalRule|FencedCode)$/.test(name)&&!active(node)){
      ranges.push(Decoration.replace({widget:new Preview(source,node.from,name==='Image'),block:name!=='Image'}).range(node.from,node.to));return false;
    }
    if(/^ATXHeading[1-6]$/.test(name))lines(node.from,node.to,'cm-md-h'+name.slice(-1));
    else if(/^SetextHeading[12]$/.test(name))lines(node.from,node.to,'cm-md-h'+name.slice(-1));
    else if(name==='Emphasis')mark(node.from,node.to,'cm-md-em');
    else if(name==='StrongEmphasis')mark(node.from,node.to,'cm-md-strong');
    else if(name==='Strikethrough')mark(node.from,node.to,'cm-md-del');
    else if(name==='InlineCode')mark(node.from,node.to,'cm-md-inline-code');
    else if(name==='FencedCode'||name==='CodeBlock')lines(node.from,node.to,'cm-md-code');
    else if(name==='Blockquote')lines(node.from,node.to,'cm-md-quote');
    else if(name==='ListItem')lines(node.from,node.to,'cm-md-list');
    else if(name==='ListMark'&&/^[-+*]$/.test(source)&&!active(node.parent))ranges.push(Decoration.replace({widget:new Bullet()}).range(node.from,node.to));
    else if(name==='Table')lines(node.from,node.to,'cm-md-table-source');
    else if(name==='Link'){
      const delimiters=node.getChildren('LinkMark'),destination=node.getChild('URL');
      const href=destination&&url(doc.sliceString(destination.from,destination.to));
      if(href&&delimiters.length>=2)mark(delimiters[0].to,delimiters[1].from,'cm-md-link',{href,rel:'noopener noreferrer'});
      if(!active(node)&&delimiters.length>=2){hide(node.from,delimiters[0].to);hide(delimiters[1].from,node.to);}return true;
    }
    else if(name==='URL'&&node.parent?.name!=='Link'&&node.parent?.name!=='Image'){
      const href=url(source.startsWith('www.')?'https://'+source:source);if(href)mark(node.from,node.to,'cm-md-link',{href,rel:'noopener noreferrer'});
    }
    else if(name==='Paragraph'){
      for(const match of source.matchAll(/\bgithub\.com\/[^\s<>]+/g)){
        const from=node.from+match.index;let parent=syntaxTree(state).resolveInner(from,1),nested=false;
        while(parent&&parent!==node){if(['Link','Image','InlineCode'].includes(parent.name))nested=true;parent=parent.parent;}
        const href=url('https://'+match[0]);if(!nested&&href)mark(from,from+match[0].length,'cm-md-link',{href,rel:'noopener noreferrer'});
      }
    }
    if(['HeaderMark','EmphasisMark','StrikethroughMark','QuoteMark','CodeMark','CodeInfo'].includes(name)){
      if(!active(node.parent)){
        let end=node.to;if(['HeaderMark','QuoteMark'].includes(name)&&doc.sliceString(end,end+1)===' ')end++;
        hide(node.from,end);
      }else mark(node.from,node.to,'cm-md-syntax');
    }
  }});
  return Decoration.set(ranges,true);
}
const styling=StateField.define({
  create:decorations,
  update:(value,tr)=>tr.docChanged||tr.selection||tr.effects.some(e=>e.is(focusEffect))||syntaxTree(tr.startState)!==syntaxTree(tr.state)?decorations(tr.state):value,
  provide:field=>EditorView.decorations.from(field)
});

window.NoteLiveMarkdown={create(parent,text,onChange,options={}){
  let resetting=false;
  const keys=new Compartment();let enabled=vimEnabled();
  const inputKeys=active=>active?[vim(),history({newGroupDelay:1e9})]:[history()];
  let view;view=new EditorView({parent,state:EditorState.create({doc:text,extensions:[
    keys.of(inputKeys(enabled)),focused,...(options.plain?[]:[markdown({base:markdownLanguage,extensions:GFM}),styling]),EditorView.lineWrapping,
    drawSelection(),EditorState.allowMultipleSelections.of(true),
    // Vim undo groups an entire insertion/change, including pauses and cursor updates.
    EditorState.transactionExtender.of(tr=>{
      if(!enabled||!view)return null;
      if(!tr.docChanged&&tr.selection)return {annotations:Transaction.addToHistory.of(false)};
      if(tr.docChanged&&tr.isUserEvent('input.type.compose.start')&&!getCM(view)?.state.vim?.insertMode)return {annotations:isolateHistory.of('before')};
      return null;
    }),
    keymap.of([{key:'Mod-Shift-z',run:redo,preventDefault:true},...markdownKeymap,...defaultKeymap,...historyKeymap,indentWithTab]),
    EditorView.contentAttributes.of({'aria-label':options.label||'Contenido de la nota','aria-multiline':'true',spellcheck:'true'}),
    EditorView.updateListener.of(update=>{if(update.docChanged&&!resetting)onChange(update.state.doc.toString());if(update.selectionSet)options.onSelection?.(update.state.selection.main);}),
    EditorView.domEventHandlers({
      focus:(_,editor)=>{editor.dispatch({effects:focusEffect.of(true)});reportMode(api);},
      blur:(_,editor)=>{editor.dispatch({effects:focusEffect.of(false)});},
      click:(event,editor)=>{
        const link=event.target.closest('a');if(!link)return false;
        event.preventDefault();if(event.ctrlKey||event.metaKey){const href=url(link.getAttribute('href'));if(href)window.open(href,'_blank','noopener,noreferrer');return true;}return false;
      }
    })
  ]})});
  const connectMode=()=>{const cm=getCM(view);if(!cm)return;
    // Keep the search prompt, without the dependency's implementation hint.
    if(!cm.glosaSearchPrompt){
      const open=cm.openDialog;
      cm.openDialog=function(template,...args){
        if(template instanceof Node){const walker=document.createTreeWalker(template,NodeFilter.SHOW_TEXT);let node;
          while((node=walker.nextNode()))node.textContent=node.textContent.replace(/\((?:JavaScript|Vim) regexp: set (?:nopcre|pcre)\)/g,'');
        }
        return open.call(this,template,...args);
      };cm.glosaSearchPrompt=true;
    }
    cm.on('vim-mode-change',()=>{
    // Visual may exit during a selection update. Finish that update before
    // dispatching the history boundary, so Vim's plugin cannot reenter the view.
    if(api.mode()==='NORMAL')queueMicrotask(()=>{if(editors.get(view.dom)===api&&api.mode()==='NORMAL')view.dispatch({annotations:isolateHistory.of('after')});});
    reportMode(api);
  });};
  const api={
    element:view.contentDOM,
    source:options.source,
    mode:()=>enabled?modeOf(view):'INSERTAR',
    visualKind:()=>{const state=getCM(view)?.state.vim;return state?.visualMode?(state.visualBlock?'block':state.visualLine?'line':'character'):null;},
    vimEnabled:()=>enabled,
    enterInsert(){const cm=getCM(view);if(cm&&!cm.state.vim?.insertMode)Vim.handleKey(cm,'i');reportMode(api);},
    enterVisual(kind='character'){const cm=getCM(view);if(!enabled||!cm)return;view.focus();if(cm.state.vim?.insertMode||cm.state.vim?.visualMode)Vim.handleKey(cm,'<Esc>');Vim.handleKey(cm,kind==='line'?'V':kind==='block'?'<C-v>':'v');reportMode(api);},
    setVim(next){if(next===enabled)return;enabled=next;view.dispatch({effects:keys.reconfigure(inputKeys(next))});if(next)connectMode();reportMode(api);},
    write:options.onWrite||(()=>window.ClassNotes?.flush()),
    focus:()=>view.focus(),
    text:()=>view.state.doc.toString(),
    selectedText:()=>view.state.selection.ranges.map(range=>view.state.sliceDoc(range.from,range.to)).join('\n'),
    setSelection:(anchor,head=anchor)=>view.dispatch({selection:{anchor,head}}),
    setText(value){if(value===view.state.doc.toString())return;resetting=true;try{view.dispatch({changes:{from:0,to:view.state.doc.length,insert:value},selection:{anchor:Math.min(view.state.selection.main.head,value.length)}});}finally{resetting=false;}},
    destroy:()=>{editors.delete(view.dom);view.destroy();}
  };
  editors.set(view.dom,api);connectMode();return api;
}};
installVimFields();

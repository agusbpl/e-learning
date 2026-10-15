// Integrated Vim runs in a temporary workspace; no real notes or model calls.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
(async()=>{
  const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-vim-')),listener=net.createServer();
  await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
  const original='# Tema\n\nalpha beta gamma\nsegunda línea\ntercera línea';
  const service=spawn('python3',['-c',`import json,server
server.init_db()
with server.connect() as conn: conn.execute('INSERT INTO documents VALUES(?,?)',('vim-document',json.dumps({'id':'vim-document','title':'Documento temporal para celdas','pages':3,'sha256':'0'*64,'storage':'upload','filename':'vim-fixture.pdf'})))
server.openrouter=lambda *args,**kwargs: {'choices':[{'message':{'content':'Ayuda simulada.'}}]}
server.library().save_note({'title':'Tema','folder':'','content':${JSON.stringify(original)},'contentFormat':'markdown','shared':False,'documentId':None,'page':None,'anchors':[]})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:['ignore','ignore','pipe']});
  let browser,stderr='';service.stderr.on('data',d=>stderr+=d);const base=`http://127.0.0.1:${port}`,snapshot=async()=>await(await fetch(base+'/api/state')).json();
  try{
    for(let i=0;i<100;i++){try{await snapshot();break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
    browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
    const page=await browser.newPage({viewport:{width:1100,height:850}}),errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error(e.stack);});
    page.on('console',message=>{if(message.type()==='error'&&!message.text().startsWith('Failed to load resource'))console.error(message.text());});
    await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Tema'}).click();
    const editor=page.locator('#note-markdown-preview .cm-content'),raw=page.locator('#class-note-content'),id=(await snapshot()).library.notes[0].id;
    await page.keyboard.press('i');assert.equal(await page.locator('#global-mode').textContent(),'INSERTAR');
    await page.keyboard.press('Escape');assert.equal(await page.locator('#global-mode').textContent(),'NORMAL');assert(await editor.evaluate(el=>document.activeElement===el));
    await page.keyboard.type('ggjj0wciwDELTA');await page.keyboard.press('Escape');
    assert.equal(await raw.inputValue(),original.replace('beta','DELTA'));assert(await editor.evaluate(el=>document.activeElement===el));
    await page.keyboard.press('u');assert.equal(await raw.inputValue(),original);await page.keyboard.press('Control+r');assert.equal(await raw.inputValue(),original.replace('beta','DELTA'));
    // Counts, line operators, registers and visual selections use the Vim engine.
    await page.keyboard.type('0dd');assert(!(await raw.inputValue()).includes('alpha'));await page.keyboard.press('u');assert((await raw.inputValue()).includes('alpha DELTA gamma'));
    await page.keyboard.type('gg2j0Vj');assert.equal(await editor.evaluate(el=>VimEditors.get(el).visualKind()),'line');assert.equal(await editor.evaluate(el=>VimEditors.get(el).selectedText()),'alpha DELTA gamma\nsegunda línea');
    await page.waitForFunction(()=>document.querySelectorAll('#note-markdown-preview .cm-selectionBackground').length>=2);
    await page.keyboard.press('d');assert(!(await raw.inputValue()).includes('segunda'));await page.keyboard.press('u');assert.equal(await raw.inputValue(),original.replace('beta','DELTA'));
    await page.keyboard.type('gg2j0');await page.keyboard.press('Control+v');await page.keyboard.type('lj');assert.equal(await editor.evaluate(el=>VimEditors.get(el).visualKind()),'block');assert.equal(await editor.evaluate(el=>VimEditors.get(el).selectedText()),'al\nse');
    await page.waitForFunction(()=>document.querySelectorAll('#note-markdown-preview .cm-selectionBackground').length>=2);
    await page.keyboard.press('d');assert((await raw.inputValue()).includes('pha DELTA gamma\ngunda línea'));await page.keyboard.press('u');assert.equal(await raw.inputValue(),original.replace('beta','DELTA'));
    await page.keyboard.type('gg2j0vll');assert.equal(await page.locator('#global-mode').textContent(),'VISUAL');assert.equal(await editor.evaluate(el=>VimEditors.get(el).selectedText()),'alp');
    await page.waitForFunction(()=>[...document.querySelectorAll('#note-markdown-preview .cm-selectionBackground')].some(el=>el.getBoundingClientRect().width>10));
    await page.keyboard.press('c');await page.keyboard.type('ALP');await page.keyboard.press('Escape');assert((await raw.inputValue()).includes('ALPha'));await page.keyboard.press('u');assert.equal(await raw.inputValue(),original.replace('beta','DELTA'));
    await page.keyboard.type('gg2j0vll');await page.keyboard.press('y');assert.equal(await page.locator('#global-mode').textContent(),'NORMAL');
    await page.keyboard.type('gg2j2w');await page.keyboard.press('i');await page.keyboard.type('X');await page.keyboard.press('Escape');assert((await raw.inputValue()).includes('Xgamma'));
    await page.keyboard.press('u');assert(!(await raw.inputValue()).includes('Xgamma'));await page.keyboard.press('.');assert((await raw.inputValue()).includes('Xgamma'));
    await page.keyboard.type('G$p');assert((await raw.inputValue()).endsWith('líneaalp'));await page.keyboard.press('u');assert((await raw.inputValue()).endsWith('línea'));
    // / searches inside the document; :w saves instead of opening the app palette.
    await page.keyboard.type('/DELTA');await page.keyboard.press('Enter');assert.equal(await page.locator('.command-palette[open]').count(),0);
    await page.keyboard.type(':w');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');
    let note=(await snapshot()).library.notes[0];assert.equal(note.id,id);assert.equal(note.content,await raw.inputValue());assert.equal(note.shared,false);
    await page.keyboard.type(':wq');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.activeElement.matches('.note-editor'));await page.keyboard.press('i');await page.keyboard.press('Escape');
    // Which-key does not steal editor focus; cancel/unknown keys do not edit text.
    const beforeLeader=await raw.inputValue();await page.keyboard.press('Space');const sheet=page.locator('.leader-cheatsheet');await sheet.waitFor({state:'visible'});
    assert(await editor.evaluate(el=>document.activeElement===el));assert(await sheet.getByRole('button',{name:'w Guardar apunte'}).isVisible());
    await page.screenshot({path:'/tmp/glosa-leader-desktop.png'});
    await page.keyboard.press('Escape');assert.equal(await sheet.count(),0);assert(await editor.evaluate(el=>document.activeElement===el));
    await page.keyboard.press('Space');await page.keyboard.press('?');assert.equal(await sheet.count(),0);assert.equal(await raw.inputValue(),beforeLeader);
    await page.keyboard.press('Space');await page.keyboard.press('Shift+KeyV');assert.equal(await editor.evaluate(el=>VimEditors.get(el).visualKind()),'line');assert.equal(await sheet.count(),0);await page.keyboard.press('Escape');assert.equal(await editor.evaluate(el=>VimEditors.get(el).mode()),'NORMAL');
    await page.setViewportSize({width:390,height:844});await page.keyboard.press('Space');await sheet.waitFor({state:'visible'});
    assert(await sheet.evaluate(el=>{const r=el.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight&&el.scrollWidth<=el.clientWidth;}));
    await page.screenshot({path:'/tmp/glosa-leader-mobile.png'});await sheet.getByRole('button',{name:'v Visual · caracteres',exact:true}).click();assert.equal(await editor.evaluate(el=>VimEditors.get(el).visualKind()),'character');await page.keyboard.press('Escape');await page.setViewportSize({width:1100,height:850});
    // The leader works directly from editor NORMAL, including in text-only Focus.
    await page.keyboard.press('Space');await page.keyboard.press('z');await page.waitForFunction(()=>document.body.classList.contains('global-focus'));assert(!(await page.locator('#note-options').isVisible()));
    await page.keyboard.press('Space');assert.equal(await sheet.count(),0);await page.keyboard.press(':');await page.waitForSelector('.command-palette[open]');await page.keyboard.press('Escape');
    await page.keyboard.press('Space');await page.keyboard.press('z');await page.waitForFunction(()=>!document.body.classList.contains('global-focus'));
    await page.keyboard.press('Space');await page.keyboard.press('t');await page.waitForSelector('.note-tutor-dialog[open]');
    const question=page.locator('.note-tutor-dialog textarea');await question.evaluate(el=>{el.value='uno dos tres';el.focus();});
    const field=page.locator('.note-tutor-dialog .cm-content');assert(await field.isVisible());assert.equal(await page.locator('#global-mode').textContent(),'INSERTAR');
    await page.keyboard.press('Escape');assert.equal(await page.locator('#global-mode').textContent(),'NORMAL');assert(await field.evaluate(el=>document.activeElement===el));
    await page.keyboard.press('Space');await page.locator('.note-tutor-dialog .leader-cheatsheet').waitFor({state:'visible'});await page.keyboard.press('Escape');assert(await field.evaluate(el=>document.activeElement===el));assert(await page.locator('.note-tutor-dialog[open]').isVisible());
    await page.keyboard.type('gg0wciwDOS');await page.keyboard.press('Escape');assert.equal(await question.inputValue(),'uno DOS tres');
    await page.keyboard.press('Control+Enter');await page.waitForSelector('.note-tutor-output .tutor-answer-text');assert.equal((await snapshot()).library.noteTutor.at(-1).message,'uno DOS tres');
    await page.keyboard.press('Escape');await page.waitForSelector('.note-tutor-dialog',{state:'detached'});
    // Native study answer handlers still receive Vim edits and keep their drafts.
    await page.keyboard.press('Space');await page.keyboard.press('e');await page.waitForSelector('.activity');
    const answer=page.locator('#main textarea').first();await answer.evaluate(el=>{const details=el.closest('details');if(details)details.open=true;el.value='uno dos tres';el.focus();});
    assert(await page.locator('#main .vim-field .cm-content').first().isVisible());await page.keyboard.press('Escape');await page.keyboard.type('gg0wciwDOS');await page.keyboard.press('Escape');assert.equal(await answer.inputValue(),'uno DOS tres');
    // Turning Vim off leaves literal typing and the current draft intact.
    await page.evaluate(()=>{state.settings.keyboardProfile='vimium';WorkspaceKeys.sync();});await page.keyboard.press('Control+End');await page.keyboard.type(' hjkl');assert.equal(await answer.inputValue(),'uno DOS tres hjkl');
    await page.evaluate(()=>{state.settings.keyboardProfile='modal';WorkspaceKeys.sync();});await page.keyboard.press('Escape');await page.keyboard.press('Escape');
    // Reading selections stay inside the theory panel, copy with y and clear on Esc.
    await page.context().grantPermissions(['clipboard-read','clipboard-write']);
    await page.locator('.theory').first().evaluate(el=>{el.tabIndex=-1;el.focus();});await page.keyboard.type('vll');assert.equal(await page.locator('#global-mode').textContent(),'VISUAL');
    const selected=await page.evaluate(()=>getSelection().toString());assert(selected.length>=3);await page.keyboard.press('y');assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),selected);assert.equal(await page.locator('#global-mode').textContent(),'NORMAL');assert.equal(await page.evaluate(()=>getSelection().toString()),'');
    await page.keyboard.press('V');await page.keyboard.press('j');assert.equal(await page.locator('#global-mode').textContent(),'VISUAL');assert(await page.evaluate(()=>document.querySelector('.theory').contains(getSelection().focusNode)));await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>getSelection().toString()),'');
    await page.keyboard.press('Space');await page.keyboard.press('n');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Tema'}).click();await page.waitForSelector('#note-markdown-preview .cm-content');
    await page.keyboard.press('i');await page.keyboard.press('Escape');await page.keyboard.type('gg');await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');
    note=(await snapshot()).library.notes[0];assert.equal(note.id,id);assert.equal(note.content,await raw.inputValue());
    // Page cells keep their source selection, page jumps and save handlers too.
    const pageNote=await(await fetch(base+'/api/notes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'Celdas Vim',folder:'',content:'',shared:false,documentId:'vim-document',page:1,writingScope:'page',pageNotes:{'vim-document':{'1':'Uno dos','2':''}},anchors:[]})})).json();
    await page.evaluate(note=>{GlosaRoom.storage.setItem('class-note-id',note.id);GlosaRoom.storage.setItem('class-note-mode:'+note.id,'page');},pageNote);
    await page.reload();await page.waitForSelector('.activity');await page.keyboard.press('Space');await page.keyboard.press('n');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Celdas Vim'}).click();await page.waitForSelector('.note-page-cell');
    const first=page.locator('.note-page-cell[data-page="1"] textarea');await first.focus();await page.keyboard.press('Escape');await page.keyboard.type('gg0wciwDOS');await page.keyboard.press('Escape');assert.equal(await first.inputValue(),'Uno DOS');
    await page.keyboard.type('Go#2');await page.keyboard.press('Enter');await page.keyboard.type('Página dos');await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');
    const savedPage=(await snapshot()).library.notes.find(n=>n.id===pageNote.id);assert.equal(savedPage.page,2);assert.equal(savedPage.pageNotes['vim-document']['1'],'Uno DOS');assert.equal(savedPage.pageNotes['vim-document']['2'],'Página dos');
    assert.deepEqual(errors,[]);console.log('OK: Vim character/line/block highlights, visual delete/change/yank/undo, which-key desktop/mobile/dialogs, silent Focus, reading selection/copy, motions/Ex, tutor/answers, save and preserved IDs.');
  }catch(error){if(browser)console.error(await browser.contexts()[0]?.pages()[0]?.evaluate(()=>({focus:document.activeElement?.outerHTML.slice(0,180),mode:document.getElementById('global-mode')?.textContent,notice:document.getElementById('notice')?.textContent,main:document.getElementById('main')?.innerHTML.slice(0,350),source:document.getElementById('class-note-content')?.value})));throw error;}finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

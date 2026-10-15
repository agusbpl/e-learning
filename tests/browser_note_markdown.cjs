// Markdown reading/editing uses a temporary database, never the student's notes.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
(async()=>{
  const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-markdown-')),listener=net.createServer();
  await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
  const service=spawn('python3',['-c',`import json,server
server.init_db()
server.openrouter=lambda *args,**kwargs: {'choices':[{'message':{'content':'Ayuda simulada en base temporal.'}}]}
server.library().save_note({'title':'ejemplo de formato','folder':'','content':'Texto sintético para comprobar formato\\n\\nse usa *cursiva*\\n\\ngithub.com/example/public-fixture','shared':False,'documentId':None,'page':None,'anchors':[]})
note=server.library().snapshot()['notes'][0]
record={'id':'temporary-history','noteId':note['id'],'message':'Consulta anterior','reply':'Respuesta conservada','createdAt':note['createdAt'],'context':{'scope':'general'}}
with server.connect() as conn: conn.execute('INSERT INTO note_tutor VALUES(?,?)',(record['id'],json.dumps(record)))
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:['ignore','ignore','pipe']});
  let browser,stderr='';service.stderr.on('data',d=>stderr+=d);const base=`http://127.0.0.1:${port}`;
  const snapshot=async()=>await(await fetch(base+'/api/state')).json();
  try{
    for(let i=0;i<100;i++){try{await snapshot();break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
    browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
    const page=await browser.newPage({viewport:{width:1100,height:850}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'ejemplo de formato'}).click();
    const preview=page.locator('#note-markdown-preview'),input=page.locator('#class-note-content'),editor=preview.locator('.cm-content'),original=(await snapshot()).library.notes[0];
    const rawMode=async()=>{await page.keyboard.press('Escape');await page.keyboard.press('Space');await page.keyboard.press(':');await page.keyboard.type('Editar Markdown completo');await page.keyboard.press('Enter');await input.waitFor({state:'visible'});};
    const saved=async()=>{await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');return (await snapshot()).library.notes[0];};
    assert(await preview.isVisible());assert(!(await input.isVisible()));assert.equal(await preview.locator('.cm-md-em').innerText(),'cursiva');
    assert.equal(await preview.locator('a').getAttribute('href'),'https://github.com/example/public-fixture');
    assert.equal(await preview.locator('.cm-md-h1').innerText(),'ejemplo de formato');assert.equal(await input.inputValue(),'# ejemplo de formato\n\n'+original.content);assert.equal(await page.locator('#class-note-title').count(),0);
    for(const selector of ['.note-meta','.note-writing-controls','.note-footer','.note-ask-button','#note-tutor-history'])assert(!(await page.locator(selector).isVisible()));
    assert((await page.locator('#note-tutor-history').textContent()).includes('Consulta anterior'));
    await page.getByLabel('Opciones del apunte',{exact:true}).click();assert(await page.locator('.note-meta').isVisible());assert(await page.locator('#note-tutor-history').isVisible());await page.keyboard.press('Escape');
    const markdown='# Ejemplo de formato\n\nSe usa *cursiva* y **geometría**.\n\n- puntos\n- polígonos\n\n> Una cita\n\n```python\nprint("<p>")\n```\n\n| Tipo | Ejemplo |\n| --- | --- |\n| Punto | Ciudad |\n\n[Datos](https://example.com)';
    await rawMode();await input.fill(markdown);await page.keyboard.press('Escape');await page.keyboard.press('Escape');assert(await editor.isVisible());assert(!(await input.isVisible()));
    assert.equal(await preview.locator('.cm-md-strong').innerText(),'geometría');assert.equal(await preview.locator('tbody td').count(),2);
    let note=await saved();assert.equal(note.id,original.id);assert.equal(note.content,markdown);assert.equal(note.title,'Ejemplo de formato');assert.equal(note.contentFormat,'markdown');assert.equal(note.shared,false);
    // Write directly inside formatted text. Other formatting and the same editable DOM stay in place.
    await editor.click();await editor.evaluate(el=>VimEditors.enterInsert(el));await page.keyboard.press('Control+End');const element=await editor.elementHandle();
    await page.keyboard.press('Enter');await page.keyboard.press('Enter');await page.keyboard.type('Otra línea con *cursiva* y **negrita**.');
    assert(await element.evaluate(el=>el.isConnected));assert(await preview.isVisible());assert(!(await input.isVisible()));
    assert.equal(await preview.locator('.cm-md-em').last().evaluate(el=>getComputedStyle(el).fontStyle),'italic');assert.equal(await preview.locator('.cm-md-strong').last().evaluate(el=>getComputedStyle(el).fontWeight),'700');assert.equal(await preview.locator('tbody td').count(),2);
    const expected=markdown+'\n\nOtra línea con *cursiva* y **negrita**.';assert.equal(await input.inputValue(),expected);
    await page.keyboard.press('Escape');await page.keyboard.press('A');await page.keyboard.insertText(' á ñ 漢字');assert((await input.inputValue()).endsWith(' á ñ 漢字'));
    await page.keyboard.press('Escape');await page.keyboard.press('u');assert.equal(await input.inputValue(),expected);await page.keyboard.press('Control+r');assert((await input.inputValue()).endsWith(' á ñ 漢字'),JSON.stringify({source:await input.inputValue(),focus:await page.evaluate(()=>document.activeElement.outerHTML.slice(0,100))}));
    note=await saved();const final=await input.inputValue();assert.equal(note.content,final);
    const exported=await(await fetch(base+'/api/notes/'+note.id+'/markdown')).text();assert(exported.includes(final));assert.equal(exported.match(/# Ejemplo de formato/g).length,1);
    await page.keyboard.press('Escape');assert(await editor.isVisible());assert(!(await input.isVisible()));
    // Selection for tutor queries comes from the editable source, never from hidden controls.
    await editor.click();await editor.evaluate(el=>VimEditors.enterInsert(el));await page.keyboard.press('Control+Home');await page.keyboard.press('ArrowDown');await page.keyboard.press('ArrowDown');await page.keyboard.press('Home');await page.keyboard.press('Shift+End');
    await page.keyboard.press('Control+Shift+Enter');await page.waitForSelector('.note-tutor-dialog[open]');assert((await page.getByLabel('Pregunta sobre el apunte',{exact:true}).inputValue()).includes('Se usa'));await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.waitForSelector('.note-tutor-dialog',{state:'detached'});await page.keyboard.press('Escape');
    // Focus stays text-only even while writing; commands remain available by keyboard.
    await page.keyboard.press('Space');await page.keyboard.press('z');await page.waitForFunction(()=>document.body.classList.contains('global-focus'));
    for(const selector of ['.topbar','#workspace-mode-button','#global-mode','#note-options','.note-meta','.note-footer','#note-tutor-history'])assert(!(await page.locator(selector).isVisible()));
    await page.keyboard.press('i');assert(await editor.isVisible());assert(!(await input.isVisible()));await page.screenshot({path:'/tmp/glosa-note-live-focus.png'});
    await page.keyboard.press('Escape');await page.keyboard.press('Space');await page.keyboard.press(':');await page.keyboard.type('Consultas del apunte');await page.keyboard.press('Enter');await page.waitForSelector('.note-records-dialog[open]');assert((await page.locator('.note-records-dialog').textContent()).includes('Consulta anterior'));await page.keyboard.press('Escape');
    await page.keyboard.press('Space');await page.keyboard.press('z');await page.waitForFunction(()=>!document.body.classList.contains('global-focus'));
    await page.reload();await page.waitForSelector('.activity');await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Ejemplo de formato'}).click();assert.equal(await input.inputValue(),final);assert(await editor.isVisible());
    // Pasting plain Markdown renders it in the same editor, and no HTML can execute.
    await editor.click();await editor.evaluate(el=>VimEditors.enterInsert(el));await page.keyboard.press('Control+a');await page.keyboard.insertText('# Pegado\n\nTexto **fuerte** y *suave*.\n\n<script>window.bad=true</script>');
    assert.equal(await preview.locator('.cm-md-h1').count(),1);assert.equal(await preview.locator('.cm-md-strong').innerText(),'fuerte');assert.equal(await preview.locator('script').count(),0);assert.equal(await page.evaluate(()=>window.bad),undefined);assert((await input.inputValue()).includes('<script>'));
    await page.keyboard.press('Escape');await page.evaluate(()=>{state.settings.keyboardProfile='vimium';WorkspaceKeys.sync();});
    await editor.click();await editor.evaluate(el=>VimEditors.enterInsert(el));await page.keyboard.press('Control+End');await page.keyboard.insertText(' edición');note=await saved();assert(note.content.endsWith(' edición'));assert(await editor.isVisible());
    // New notes have a real Markdown heading and start in the formatted editor.
    await page.evaluate(()=>ClassNotes.create());assert.equal(await input.inputValue(),'# \n\n');assert(await editor.isVisible());assert(!(await input.isVisible()));
    await page.keyboard.type('Nuevo título');await page.keyboard.press('Control+End');await page.keyboard.type('Un cuerpo.');await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');
    note=(await snapshot()).library.notes.at(-1);assert.equal(note.title,'Nuevo título');assert.equal(note.content,'# Nuevo título\n\nUn cuerpo.');
    // A failed save never destroys the live editor or its draft.
    await page.route('**/api/notes',route=>route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({error:'Fallo temporal de prueba'})}));
    await editor.click();await editor.evaluate(el=>VimEditors.enterInsert(el));await page.keyboard.press('Control+End');await page.keyboard.type(' Borrador conservado.');await page.waitForSelector('#note-save-error',{state:'visible'});assert(await editor.isVisible());assert((await input.inputValue()).includes('Borrador conservado.'));
    await page.unroute('**/api/notes');await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');assert(!(await page.locator('#note-save-error').isVisible()));
    await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:'/tmp/glosa-note-live-mobile.png'});await page.getByLabel('Opciones del apunte',{exact:true}).click();assert(await page.locator('.note-options-panel').isVisible());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert.deepEqual(errors,[]);console.log('OK: live Markdown formatting while writing, exact source preservation, caret/undo/redo, Unicode, paste safety, focus, tutor selection, raw mode, autosave/Ctrl+s/reload/export and mobile.');
  }catch(error){if(browser)console.error(await browser.contexts()[0]?.pages()[0]?.evaluate(()=>({focus:document.activeElement?.outerHTML.slice(0,200),mode:document.getElementById('global-mode')?.textContent,source:document.getElementById('class-note-content')?.value.slice(-150),dialogs:document.querySelectorAll('dialog[open]').length,focusMode:state.settings.focusMode,body:document.body.className})));throw error;}finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

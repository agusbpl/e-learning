// Uses a local simulated provider. No credentials or calls to external models.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict');
const {spawn}=require('child_process');
(async()=>{
  const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'estudio-note-tutor-'));
  const listener=net.createServer();await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
  const script=`import json,time,server
server.init_db()
def fake(path,body=None,authenticated=True):
    context=json.loads(body['messages'][1]['content'])
    message=context['studentMessage']
    if 'SIMULAR FALLO' in message: raise ValueError('Cuota agotada simulada')
    time.sleep(.5)
    return {'choices':[{'message':{'content':'Aclaración **legible**: '+message+' — contexto PDF '+str(context['context']['page'])}}]}
server.openrouter=fake
c=server.snapshot()['courses'][0]
server.event('tutor_reply',c['id'],c['lessons'][0]['id'],{'reply':'{"reply":"Explicaci\\\\u00f3n anterior.\\\\nSin JSON visible.","reason":"cortado'})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`;
  const service=spawn('python3',['-c',script],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:['ignore','pipe','pipe']});
  const base=`http://127.0.0.1:${port}`;let browser,stderr='';service.stderr.on('data',d=>stderr+=d);
  const getState=async()=>await(await fetch(base+'/api/state')).json();
  try{
    for(let i=0;i<100;i++){try{if((await fetch(base+'/api/state')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
    browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
    const page=await browser.newPage({viewport:{width:1400,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');
    await page.keyboard.type('gt');await page.waitForSelector('#tutor-panel',{state:'visible'});
    assert((await page.locator('#tutor-chat').textContent()).includes('Explicación anterior.'));
    assert(!(await page.locator('#tutor-chat').textContent()).includes('"reply"'));
    await page.keyboard.press('Escape');await page.locator('#main').focus();await page.keyboard.type('gn');await page.waitForSelector('#note-markdown-preview .cm-content');
    await page.keyboard.press('i');await page.keyboard.type('¿Qué significa esta idea?');
    assert.equal((await getState()).library.noteTutor.length,0);
    await page.keyboard.press('Control+Shift+Enter');await page.waitForSelector('.note-tutor-output strong');
    assert((await page.locator('.note-tutor-output').textContent()).includes('Aclaración legible: # ¿Qué significa esta idea?'));
    let state=await getState();assert.equal(state.library.noteTutor.length,1);assert.equal(state.library.notes[0].shared,false);assert.equal(state.library.notes[0].content,'# ¿Qué significa esta idea?\n\n');
    await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.locator('#main').focus();await page.keyboard.type('gt');await page.waitForSelector('.note-tutor-dialog[open]');
    assert.equal((await getState()).library.noteTutor.length,1);assert.equal(await page.locator('[data-view=notes]').getAttribute('class'),'nav active');
    await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.locator('#main').focus();await page.keyboard.press('a');await page.waitForSelector('.source-note-dialog[open]');
    await page.keyboard.type('Duda con anotación');await page.keyboard.press('Control+Shift+Enter');await page.waitForSelector('.source-note-dialog .note-tutor-output strong');
    assert.equal(await page.locator('.source-note-dialog[open]').count(),1);state=await getState();assert.equal(state.library.notes[0].anchors.length,1);
    await page.locator('.source-note-dialog .cm-content').fill('SIMULAR FALLO');await page.keyboard.press('Control+Shift+Enter');await page.waitForSelector('.source-note-dialog [role=alert]');
    state=await getState();assert.equal(state.library.notes[0].anchors.length,1);assert.equal(state.library.notes[0].anchors[0].comment,'SIMULAR FALLO');assert.equal(state.library.noteTutor.at(-1).status,'failed');
    await page.locator('.source-note-dialog .cm-content').fill('Nueva duda sin duplicar anotación');await page.keyboard.press('Control+Shift+Enter');await page.waitForFunction(()=>document.querySelector('.source-note-dialog .tutor-answer-text')?.textContent.includes('Nueva duda'));
    state=await getState();assert.equal(state.library.notes[0].anchors.length,1);assert.equal(state.library.noteTutor.length,4);const textNote=structuredClone(state.library.notes[0]);const textHistory=structuredClone(state.library.noteTutor);
    await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.locator('#main').focus();
    // Opening a PDF creates its own note; its history must not absorb the text note's queries.
    await page.keyboard.type('gf');await page.waitForSelector('.pdf-picker[open]');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.getElementById('pdf-loading')?.hidden===true,{},{timeout:30000});
    await page.getByLabel('Notas de la página 1',{exact:true}).focus();await page.locator('.note-page-cell[data-page="1"] .cm-content').fill('Duda que pertenece a página 1');await page.keyboard.press('Control+Shift+Enter');await page.waitForSelector('.note-tutor-output [role=status]');
    await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.locator('#main').focus();await page.keyboard.press(']');await page.waitForFunction(()=>document.getElementById('pdf-page')?.value==='2');
    await page.getByLabel('Notas de la página 2',{exact:true}).focus();await page.locator('.note-page-cell[data-page="2"] .cm-content').fill('Otra página, otro apunte');await page.keyboard.press('Control+s');
    await page.waitForFunction(()=>document.querySelector('#note-tutor-history')?.textContent.includes('Consultas del apunte · 1'));
    state=await getState();assert.equal(state.library.noteTutor.at(-1).context.page,1);assert.equal(state.library.noteTutor.at(-1).context.studentText,'Duda que pertenece a página 1');
    assert.equal(await page.getByLabel('Notas de la página 2',{exact:true}).inputValue(),'Otra página, otro apunte');const pdfNote=state.library.notes.find(n=>n.id===state.library.noteTutor.at(-1).noteId);assert(pdfNote);assert.notEqual(pdfNote.id,textNote.id);assert.equal(pdfNote.page,2);assert.equal(state.library.noteTutor.filter(r=>r.noteId===pdfNote.id).length,1);assert.deepEqual(state.library.notes.find(n=>n.id===textNote.id),textNote);assert.deepEqual(state.library.noteTutor.filter(r=>r.noteId===textNote.id),textHistory);
    assert(!state.events.some(e=>e.kind==='assessment'));
    const md=await(await fetch(base+'/api/export.md')).text();assert(md.includes('Nueva duda sin duplicar anotación'));assert(md.includes('Cuota agotada simulada'));
    await page.reload();await page.waitForSelector('.activity');await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'¿Qué significa esta idea?'}).click();await page.waitForSelector('#note-tutor-history',{state:'attached'});assert((await page.locator('#note-tutor-history').textContent()).includes('Consultas del apunte · 4'));
    await page.keyboard.press('Escape');await page.keyboard.type('gt');await page.waitForSelector('.note-tutor-dialog[open]');await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(root,'output','qa','notas-tutor-mobile.png')});
    assert.deepEqual(errors,[]);console.log('OK: readable legacy JSON, optional immediate note tutor, keyboard save-and-ask, failed/repeated annotation questions, page context, edits during response, persistence and exports. No external model calls.');
  }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

// Synthetic provider output in a temporary database. No external model calls.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-tutor-output-')),socket=net.createServer();
 await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
 const service=spawn('python3',['-c',`import json,server
server.init_db()
course=server.snapshot()['courses'][0];lesson=course['lessons'][0]
server.event('tutor_reply',course['id'],lesson['id'],{'reply':'El estudiante envió una respuesta. PRIVATE_LEGACY. Ahora debo producir el JSON.','rawResponse':'PRIVATE_RAW','structured':False,'truncated':True,'courseVersion':course['version']})
server.event('tutor_reply',course['id'],lesson['id'],{'reply':'PRIVATE_PREFIX\\n'+json.dumps({'reply':'Respuesta final visible.','status':'pending'}),'structured':False,'courseVersion':course['version']})
note=server.library().save_note({'title':'Notas de prueba','folder':'','content':'# Notas de prueba','contentFormat':'markdown','shared':False,'documentId':None,'page':None,'anchors':[]})
record={'id':'reply-note','noteId':note['id'],'createdAt':server.now(),'message':'Una duda','reply':'<think>PRIVATE_NOTE</think>Explicación final del apunte.','status':'answered','helpProvided':True,'context':{'scope':'general','noteRevision':note['revision']}}
with server.connect() as conn: conn.execute('INSERT INTO note_tutor VALUES(?,?)',(record['id'],json.dumps(record)))
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:['ignore','ignore','pipe']});
 let browser,stderr='';service.stderr.on('data',d=>stderr+=d);const base=`http://127.0.0.1:${port}`,snapshot=async()=>await(await fetch(base+'/api/state')).json();
 try{
  for(let i=0;i<100;i++){try{await snapshot();break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
  const original=await snapshot();
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');
  assert.equal(await page.locator('#tutor-preview').textContent(),'Respuesta final visible.');await page.keyboard.press('Space');await page.keyboard.press('t');await page.waitForSelector('#tutor-chat .assistant');
  const chat=await page.locator('#tutor-chat').innerText();assert(chat.includes('Respuesta final visible.'));assert(chat.includes('respuesta final completa'));assert(!chat.includes('PRIVATE_'));assert(!chat.includes('Ahora debo'));
  const cases=[['<think>PRIVATE</think>Respuesta final.','Respuesta final.'],['PRIVATE</think>Respuesta final.','Respuesta final.'],['<analysis>PRIVATE','respuesta final completa'],['El estudiante envió una respuesta combinada. PRIVATE','respuesta final completa'],['Antes del JSON\n{"reply":"Una explicación útil.","status":','Una explicación útil.'],['{"status":"pending","reply":"Una explicación útil.","evidence":','Una explicación útil.'],['Texto normal del tutor.','Texto normal del tutor.']];
  for(const [raw,expected] of cases){const shown=await page.evaluate(raw=>readableTutor(raw),raw);assert(shown.includes(expected),shown);assert(!shown.includes('PRIVATE'));}
  await page.screenshot({path:'/tmp/glosa-tutor-final-only.png'});
  await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press('Space');await page.keyboard.press('c');await page.waitForSelector('.notebook-history summary');await page.locator('.notebook-history summary').click();await page.getByRole('button',{name:'Todo el registro',exact:true}).click();const notebook=await page.locator('#main').innerText();assert(notebook.includes('Respuesta final visible.'));assert(!notebook.includes('PRIVATE_'));
  await page.keyboard.press('Space');await page.keyboard.press('n');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Notas de prueba'}).click();await page.getByLabel('Opciones del apunte',{exact:true}).click();await page.locator('#note-tutor-history>details>summary').click();await page.locator('#note-tutor-history .note-tutor-entry>summary').click();const note=await page.locator('#note-tutor-history').innerText();assert(note.includes('Explicación final del apunte.'));assert(!note.includes('PRIVATE_NOTE'));
  const after=await snapshot();assert.deepEqual(after.events.filter(e=>e.kind==='tutor_reply'),original.events.filter(e=>e.kind==='tutor_reply'));assert.deepEqual(after.library.noteTutor,original.library.noteTutor);assert(!after.events.some(e=>e.kind==='assessment'));assert.deepEqual(errors,[]);
  console.log('OK: only final replies in chat, preview, notebook and note history; tagged/unclosed thinking and prefixed/truncated JSON; original records untouched; no mastery awarded or model calls.');
 }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exit(1);});

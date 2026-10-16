// Isolated database and temp HOME; no provider calls or real history modifications.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-rooms-')),home=path.join(data,'home'),socket=net.createServer();
 fs.mkdirSync(home,{recursive:true});
 await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
 // HOME points inside the temp tree and GLOSA_MARGEN_DIR is empty, so the default
 // visible Margen is temporary and `set_margen` still works.
 const service=spawn('python3',['server.py'],{cwd:root,env:{...process.env,HOME:home,GLOSA_MARGEN_DIR:'',LEARNING_DATA_DIR:data,LEARNING_PORT:String(port),OPENROUTER_API_KEY:''},stdio:'ignore'}),base=`http://127.0.0.1:${port}`;
 let browser;
 try{
  for(let n=0;n<100;n++){try{const res=await fetch(base+'/api/state');if(res.ok)break;}catch{}await new Promise(r=>setTimeout(r,100));if(n===99)throw Error('Startup failed');}
  const state=await (await fetch(base+'/api/state')).json(),doc=state.library.documents[0];
  const note=await (await fetch(base+'/api/notes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'Nota para salas',folder:'',content:'ORIGINAL',shared:false,documentId:doc.id,page:1,writingScope:'page',pageNotes:{[doc.id]:{'1':'Contenido original'}},anchors:[]})})).json();
  const zip=Buffer.from(await (await fetch(base+'/api/rooms/export')).arrayBuffer());
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});const page=await browser.newPage({viewport:{width:1200,height:800}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{if(!localStorage.getItem('glosa-active-room'))localStorage.setItem('glosa-active-room','local');});await page.goto(base);await page.waitForSelector('.activity');
  await page.getByRole('button',{name:'Abrir Margen',exact:true}).click();await page.waitForSelector('#rooms-dialog[open]');
  // Margen is the visible vault: injected stylesheet, explanation and honest special spaces.
  assert.equal(await page.locator('#bovedas-css').count(),1);
  assert.match(await page.locator('#rooms-dialog').textContent(),/Tu Margen es una carpeta visible de esta computadora/);
  assert.match(await page.locator('#rooms-dialog').textContent(),/Dónde está tu Margen/);
  assert.match(await page.locator('#boveda-current').textContent(),/La biblioteca local vive en la carpeta de datos de la propia aplicación/);
  assert.match(await page.locator('.boveda-row').filter({hasText:'Biblioteca local'}).textContent(),/Biblioteca local/);
  assert.match(await page.locator('#boveda-margen-info').textContent(),/Tu Margen está en/);
  assert.match(await page.locator('.boveda-row').filter({hasText:'Primer trazo'}).textContent(),/Tutorial incluido/);
  await page.locator('#room-upload').setInputFiles({name:'pliego.zip',mimeType:'application/zip',buffer:zip});
  await page.waitForFunction(()=>GlosaRoom.id.startsWith('room-'));await page.waitForSelector('.activity');
  const selected=await page.evaluate(()=>GlosaRoom.id);assert(selected.startsWith('room-'));
  await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Nota para salas'}).click();await page.waitForSelector('#pdf-page-canvas canvas');
  assert.equal(await page.locator('#note-name-button').textContent(),'Nota para salas');
  await page.locator('.note-page-cell[data-page="1"] textarea').focus();const input=page.locator('.note-page-cell[data-page="1"] .cm-content');await input.fill('CAMBIO EN SALA IMPORTADA');await input.press('Escape');
  await page.evaluate(()=>ClassNotes.flush());
  const original=await (await fetch(base+'/api/state')).json(),imported=await (await fetch(base+'/api/state',{headers:{'X-Glosa-Room':selected}})).json();
  assert.equal(original.library.notes.find(n=>n.id===note.id).pageNotes[doc.id]['1'],'Contenido original');
  assert.equal(imported.library.notes.find(n=>n.id===note.id).pageNotes[doc.id]['1'],'CAMBIO EN SALA IMPORTADA');
  await page.getByRole('button',{name:'Abrir Margen',exact:true}).click();
  // Opened pliego card: human folder path, contents summary and a rename that moves the folder but keeps the ID.
  await page.waitForFunction(()=>document.getElementById('boveda-current').textContent.includes('1 apunte'));
  const listing=await (await fetch(base+'/api/rooms',{headers:{'X-Glosa-Room':selected}})).json();
  const item=listing.pliegos.find(entry=>entry.id===selected);assert(item);
  assert.equal(path.basename(item.path),item.title,'the visible folder uses the human name');
  const card=await page.locator('#boveda-current').textContent();
  assert(card.includes(item.path));assert(card.includes('1 apunte'));
  const row=page.locator('.boveda-row').filter({hasText:item.path});
  const rowText=await row.textContent();
  assert(rowText.includes('1 curso'));assert(rowText.includes('1 fuente'));assert(rowText.includes('1 apunte'));
  page.once('dialog',prompt=>prompt.accept('Pliego renombrado'));
  await row.locator('.boveda-rename').click();
  await page.waitForSelector('.boveda-row:has-text("Pliego renombrado")');
  assert.equal(await page.evaluate(()=>GlosaRoom.id),selected,'renaming a pliego keeps its stable ID');
  const afterRename=await (await fetch(base+'/api/rooms',{headers:{'X-Glosa-Room':selected}})).json();
  const renamed=afterRename.pliegos.find(entry=>entry.id===selected);
  assert.equal(path.basename(renamed.path),'Pliego renombrado','the folder is physically renamed');
  assert.notEqual(renamed.path,item.path);
  const download=await page.locator('#room-download').getAttribute('href');assert(download.includes(selected));
  const downloaded=page.waitForEvent('download');await page.locator('#room-download').click();assert.equal((await downloaded).suggestedFilename(),'pliego-glosa.zip');
  await page.locator('.room-choice').filter({hasText:'Biblioteca local'}).click();await page.waitForFunction(()=>GlosaRoom.id==='local');await page.waitForSelector('.activity');
  assert.equal(await page.evaluate(()=>GlosaRoom.id),'local');
  await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Nota para salas'}).click();await page.waitForSelector('#pdf-page-canvas canvas');assert.equal(await page.locator('.note-page-cell[data-page="1"] textarea').inputValue(),'Contenido original');
  assert.deepEqual(errors,[]);console.log('OK: ZIP imported, isolated notes with identical IDs, PDF opened, export scoped, switch back preserved original; Margen card shows the human folder path and contents, and rename moves the folder keeping the ID.');
 }finally{if(browser)await browser.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});

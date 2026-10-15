// Temporary database, no provider or model calls.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),http=require('http'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
const get=url=>new Promise((resolve,reject)=>http.get(url,{headers:{Connection:'close'}},r=>{let s='';r.setEncoding('utf8');r.on('data',c=>s+=c);r.on('end',()=>{try{resolve(JSON.parse(s));}catch(e){reject(e);}});}).on('error',reject));
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'estudio-headers-')),listener=net.createServer();
 await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
 const service=spawn('python3',['-c',`import server
server.init_db()
doc=next(d for d in server.library().snapshot()['documents'] if d['pages']>=2)
server.library().save_note({'title':'Encabezados','folder':'','content':'','shared':False,'documentId':doc['id'],'page':1,'writingScope':'page','pageNotes':{doc['id']:{'1':'Uno','2':'Dos'}},'anchors':[]})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:'ignore'});
 const base=`http://127.0.0.1:${port}`;let browser;
 try{
  for(let i=0;i<100;i++){try{await get(base+'/api/state');break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error('Server unavailable');}
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  const save=async()=>{await page.keyboard.press('Control+s');await page.waitForFunction(()=>document.getElementById('note-save-status')?.textContent==='Guardado en esta computadora');};
  await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Encabezados'}).click();await page.waitForFunction(()=>document.getElementById('pdf-loading')?.hidden===true);
  await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press(':');await page.keyboard.type('Editar Markdown completo');await page.keyboard.press('Enter');
  const input=page.locator('#class-note-content');assert.equal(await input.inputValue(),'#1\n\nUno\n\n#2\n\nDos');
  await input.fill('Uno\n\n#2\n\nDos');await save();assert.equal(await input.inputValue(),'#1\n\nUno\n\n#2\n\nDos');
  await input.focus();await page.keyboard.press('Control+Home');await page.waitForFunction(()=>document.getElementById('pdf-page')?.value==='1');await page.keyboard.press('Escape');await page.keyboard.press('Escape');await page.keyboard.press(']');await page.waitForFunction(()=>document.getElementById('pdf-page')?.value==='2');
  await input.fill('Texto sin encabezado, página dos');await save();assert.equal(await input.inputValue(),'#1\n\n#2\n\nTexto sin encabezado, página dos');
  let state=await get(base+'/api/state'),note=state.library.notes[0];assert.equal(note.pageNotes[note.documentId]['2'],'Texto sin encabezado, página dos');assert.equal(note.pageNotes[note.documentId]['1'],'');
  await input.fill('# pag1\n\nLegado\n\n# pag2\n\nSegunda');await save();assert.equal(await input.inputValue(),'#1\n\nLegado\n\n#2\n\nSegunda');
  state=await get(base+'/api/state');note=state.library.notes[0];const md=fs.readFileSync(path.join(data,'notes',note.id+'.md'),'utf8');assert(md.includes('#1\n\nLegado'));assert(md.includes('#2\n\nSegunda'));assert(!md.includes('# pag'));
  await page.reload();await page.waitForSelector('.activity');await page.keyboard.type('gn');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Encabezados'}).click();await page.waitForSelector('#class-note-content',{state:'attached'});assert((await input.inputValue()).includes('#1\n\nLegado'));assert.deepEqual(errors,[]);
  console.log('OK: #1 restored without blocking, numbered headings, current page preserved without headings, legacy format, Markdown mirror and reload. No model calls.');
 }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

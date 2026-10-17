// Prompt composition only: temporary HOME/database; no agent or model is launched.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-prompt-')),home=path.join(data,'home');
 const materials=path.join(home,'Materiales "TPG" & <curso>');fs.mkdirSync(materials,{recursive:true});
 fs.writeFileSync(path.join(materials,'apunte.md'),'Fuente: no debe ser leída ni enviada por el formulario.');
 fs.mkdirSync(path.join(materials,'Unidad 1'));
 const socket=net.createServer();await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
 const service=spawn('python3',['server.py'],{cwd:root,env:{...process.env,HOME:home,GLOSA_MARGEN_DIR:'',LEARNING_DATA_DIR:data,LEARNING_PORT:String(port),OPENROUTER_API_KEY:''},stdio:'ignore'}),base=`http://127.0.0.1:${port}`;
 let browser;
 try{
  for(let i=0;i<100;i++){try{if((await fetch(base+'/api/state')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error('Startup failed');}
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
  const page=await browser.newPage({viewport:{width:1100,height:850}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.copiedPrompt=text;}}}));
  await page.goto(base);await page.locator('#rooms-button').click();
  await page.locator('#author-prompt-assistant summary').click();
  await page.waitForFunction(expected=>document.getElementById('author-folder-location').textContent===expected,home);
  assert(await page.locator('#author-copy-prompt').isDisabled());
  assert(await page.locator('#author-exam-fields').isHidden());
  const before=await page.evaluate(async()=>({state:await (await fetch('/api/state')).json(),rooms:await (await fetch('/api/rooms')).json()}));
  await page.getByRole('button',{name:'Elegir carpeta',exact:true}).click();
  await page.locator('#author-folder-list').getByRole('button',{name:path.basename(materials),exact:true}).click();
  await page.waitForFunction(expected=>document.getElementById('author-folder-location').textContent===expected,materials);
  await page.getByRole('button',{name:'Usar esta carpeta',exact:true}).click();
  assert.equal(await page.locator('#author-folder').inputValue(),materials);
  let prompt=await page.locator('#author-prompt-preview').inputValue();
  assert.equal(prompt,`Usá el MCP de Glosa para crear un pliego con los materiales del directorio ${JSON.stringify(materials)}.\n\nTomá ese directorio como fuente y guardá el pliego resultante como un directorio dentro del Margen configurado: ${JSON.stringify(path.join(home,'Margen'))}.\n\nSi el MCP de Glosa no está disponible, configurá y conectá el servidor de autoría mediante stdio con el comando ${JSON.stringify(path.join(root,'start-author.sh'))} en tu cliente y continuá con el encargo.`);
  for(const unwanted of ['create_study_pliego','source_folder_brief','simulacro','rúbrica','siglas'])assert(!prompt.includes(unwanted));
  assert(!prompt.includes('Fuente: no debe ser leída'));
  await page.locator('#author-copy-prompt').click();assert.equal(await page.evaluate(()=>window.copiedPrompt),prompt);
  await page.locator('#author-mode').selectOption('exam');
  await page.locator('#author-title').fill('Tecnologías para la Gestión');
  await page.locator('#author-kind').selectOption('Teoría');await page.locator('#author-date').fill('2026-10-20');await page.locator('#author-time').fill('19:00');
  await page.locator('#author-scope').fill('Hasta la última clase. Práctica solo complementaria.');
  await page.locator('#author-availability').fill('Sábado y lunes libres; domingo 20 minutos.');
  await page.locator('#author-preferences').fill('Simulacros diarios y uno holístico el martes.');
  prompt=await page.locator('#author-prompt-preview').inputValue();
  for(const value of ['Tipo: Teoría','2026-10-20 a las 19:00','Hasta la última clase','domingo 20 minutos','holístico el martes'])assert(prompt.includes(value));
  await page.locator('#author-copy-prompt').click();assert.equal(await page.evaluate(()=>window.copiedPrompt),prompt);
  await page.locator('#author-prompt-preview').fill(prompt+'\n\nMi aclaración final.');await page.locator('#author-copy-prompt').click();
  assert((await page.evaluate(()=>window.copiedPrompt)).endsWith('Mi aclaración final.'));
  await page.locator('#author-mode').selectOption('directory');prompt=await page.locator('#author-prompt-preview').inputValue();
  assert(!prompt.includes('2026-10-20'));assert(!prompt.includes('Tipo: Teoría'));assert(!prompt.includes('domingo 20 minutos'));
  const after=await page.evaluate(async()=>({state:await (await fetch('/api/state')).json(),rooms:await (await fetch('/api/rooms')).json()}));
  assert.deepEqual(after.state.events,before.state.events);assert.deepEqual(after.state.courses,before.state.courses);
  assert.deepEqual(after.state.calendarEvents,before.state.calendarEvents);assert.deepEqual(after.rooms.rooms,before.rooms.rooms);
  assert.deepEqual(errors,[]);console.log('OK: folder selection, directory-only and exam prompts, editable preview and Copy; no materials read or pliegos/history created.');
 }finally{if(browser)await browser.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});

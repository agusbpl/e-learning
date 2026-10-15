// Isolated database. No calls to any model provider.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),http=require('http'),assert=require('assert/strict'),{spawn}=require('child_process');
const request=(url,body)=>new Promise((resolve,reject)=>{const data=body?JSON.stringify(body):null;const req=http.request(url,{method:data?'POST':'GET',headers:data?{'Content-Type':'application/json'}:{}},res=>{let text='';res.on('data',c=>text+=c);res.on('end',()=>{try{const value=JSON.parse(text);if(res.statusCode>=400)throw Error(JSON.stringify(value));resolve(value);}catch(e){reject(e);}});});req.on('error',reject);req.end(data);});
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'estudio-groups-')),socket=net.createServer();
 await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
 const service=spawn('python3',['-c',`import server
server.init_db()
server.event('tutor_note','qa-groups','one',{'kind':'doubt','text':'Retomar la relación conceptual.','quote':'Primera respuesta original.','isLearningEvidence':False,'courseVersion':'0'})
server.event('tutor_reply','qa-groups','one',{'reply':'INTERCAMBIO QUE NO DEBE VOLCARSE EN EL CUADERNO','courseVersion':'0'})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port),OPENROUTER_API_KEY:''},stdio:'ignore'}),base=`http://127.0.0.1:${port}`;
 let browser;
 try{
  for(let n=0;n<100;n++){try{await request(base+'/api/state');break;}catch{if(n===99)throw Error('Startup failed');await new Promise(r=>setTimeout(r,100));}}
  const course={schemaVersion:1,id:'qa-groups',title:'Agrupación de preguntas',version:'1',sources:[],lessons:[{id:'one',title:'Una lección',unit:'QA',intro:'Prueba de flujos',minutes:5,priority:1,blocks:[{id:'b1',title:'Primera teoría',text:'Una distinción conceptual.'},{id:'b2',title:'Segunda teoría',text:'Un tema diferente.'}],exercises:[{id:'e1',type:'open',question:'Primera pregunta',rubric:['Explicar']},{id:'e2',type:'explain',question:'Segunda pregunta',rubric:['Aplicar']}]}]};
  await request(base+'/api/course',course);
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('study-course','qa-groups'));
  await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');assert.equal(await page.locator('.group-conversation').count(),1);assert.equal(await page.locator('.activity details,.activity-actions').count(),0);assert.equal(await page.getByRole('button',{name:'Guardar respuesta',exact:true}).count(),0);assert(!((await page.locator('#main').innerText()).includes('Borrador guardado al escribir')));
  assert.equal(await page.locator('.topbar [data-view]').count(),0);await page.keyboard.type('gm');await page.waitForSelector('#mode-dialog[open]');await page.keyboard.press('j');assert.equal(await page.evaluate(()=>document.activeElement.dataset.view),'notes');await page.keyboard.press('Escape');
  await page.locator('.activity textarea').nth(0).fill('Primera respuesta original.');
  await page.reload();await page.waitForSelector('.activity');assert.equal(await page.locator('.activity textarea').nth(0).inputValue(),'Primera respuesta original.');assert.equal((await request(base+'/api/state')).events.filter(e=>e.kind==='answer').length,0);
  await page.locator('.group-conversation').click();assert.equal((await request(base+'/api/state')).events.filter(e=>e.kind==='answer').length,0);
  await page.locator('.activity textarea').nth(1).fill('Segunda respuesta original.');await page.keyboard.press('Control+Enter');
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Conectá el tutor'));
  let state=await request(base+'/api/state'),records=state.events.filter(e=>e.courseId==='qa-groups');
  assert.equal(records.filter(e=>e.kind==='answer').length,2);assert.equal(records.filter(e=>e.kind==='chat_message').length,1);
  const message=records.find(e=>e.kind==='chat_message').data.message;assert(message.includes('Primera respuesta original.'));assert(message.includes('Segunda respuesta original.'));
  await page.reload();await page.waitForSelector('.activity');await page.keyboard.type('gc');await page.waitForSelector('.notebook-item');
  assert.equal(await page.locator('.notebook-item').count(),1);assert(!((await page.locator('#main').innerText()).includes('INTERCAMBIO QUE')));
  await page.locator('.notebook-history summary').click();await page.getByRole('button',{name:'Todo el registro',exact:true}).click();assert((await page.locator('#main').innerText()).includes('INTERCAMBIO QUE'));
  course.version='2';course.lessons[0].sequence=[{type:'block',id:'b1'},{type:'exercise',id:'e1'},{type:'block',id:'b2'},{type:'exercise',id:'e2'}];
  await request(base+'/api/course',course);await page.reload();await page.waitForSelector('.activity');assert.equal(await page.locator('.group-conversation').count(),2);
  const order=await page.locator('#main>.theory-section,#main>.exercise-group').evaluateAll(nodes=>nodes.map(n=>n.className));assert.deepEqual(order,['theory-section','exercise-group','theory-section','exercise-group']);
  assert.equal(await page.getByRole('button',{name:'Consultar al tutor',exact:true}).count(),2);
  assert.equal(await page.getByRole('button',{name:'Marcar como revisada',exact:true}).count(),0);
  assert.equal(await page.getByRole('button',{name:'Preparar continuación',exact:true}).isVisible(),false);
  await page.locator('.continuation-handoff summary').click();
  await page.getByRole('button',{name:'Preparar continuación',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.continuation-handoff summary')?.textContent==='Continuación solicitada');
  state=await request(base+'/api/state');assert.equal(state.events.filter(e=>e.kind==='continuation_requested').length,1);
  await page.getByRole('button',{name:'Ver pendientes →',exact:true}).click();await page.waitForSelector('.calendar-heading');
  state=await request(base+'/api/state');
  assert.equal(state.events.filter(e=>e.kind==='self_review'&&e.courseId==='qa-groups'&&e.lessonId==='one').length,1);
  assert.notEqual(state.recommendations['qa-groups'].statuses.one,'independent');
  await page.getByRole('button',{name:'＋ Evento',exact:true}).click();await page.getByLabel('Título del evento').fill('Clase de QA');await page.getByLabel('Tipo de evento').selectOption('theory');await page.getByLabel('Fecha del evento').fill(state.localDate);await page.getByLabel('Hora opcional').fill('18:00');await page.getByLabel('Repetir semanalmente hasta').fill('2026-11-30');await page.getByRole('button',{name:'Guardar evento',exact:true}).click();await page.waitForSelector('.calendar-event:has-text("Clase de QA")');
  await page.getByRole('button',{name:'Semana',exact:true}).click();assert.equal(await page.locator('.calendar-week .calendar-day').count(),7);assert((await page.locator('.calendar-week').innerText()).includes('Clase de QA'));
  await page.getByRole('button',{name:'Mes',exact:true}).click();assert((await page.locator('.calendar-month .calendar-event').count())>=4);
  await page.locator('.calendar-event:has-text("Clase de QA")').first().click();await page.getByLabel('Título del evento').fill('Clase corregida');await page.getByRole('button',{name:'Guardar evento',exact:true}).click();await page.waitForSelector('.calendar-event:has-text("Clase corregida")');
  await page.reload();await page.waitForSelector('.activity');await page.keyboard.type('gp');await page.getByRole('button',{name:'Mes',exact:true}).click();assert((await page.locator('.calendar-month').innerText()).includes('Clase corregida'));
  const qa=path.join(root,'output/qa');fs.mkdirSync(qa,{recursive:true});await page.screenshot({path:path.join(qa,'plan-modos-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(qa,'plan-modos-mobile.png'),fullPage:true});
  assert((await request(base+'/api/export.json')).calendarEvents.some(e=>e.title==='Clase corregida'));
  assert.deepEqual(errors,[]);console.log('OK: one conversation per consecutive group, validation before saving, original answers preserved, important notebook by default, complete history available, separate theory creates separate conversations. No model calls.');
 }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

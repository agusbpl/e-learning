// A local simulated provider and a temporary database; never contacts a model.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict');
const {spawn}=require('child_process');
const {fixturePDF}=require('./helpers/pdf_fixture.cjs');
const http=require('http');
const localJSON=url=>new Promise((resolve,reject)=>{http.get(url,{headers:{Connection:'close'}},res=>{let text='';res.setEncoding('utf8');res.on('data',chunk=>text+=chunk);res.on('error',reject);res.on('end',()=>{try{if(res.statusCode!==200)throw Error(text);resolve(JSON.parse(text));}catch(e){reject(e);}});}).on('error',reject);});
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'estudio-context-'));
 const listener=net.createServer();await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
 const script=`import json,server
server.init_db();server.KEY='test-key'
c=server.snapshot()['courses'][0];l=c['lessons'][0]
server.event('annotation',c['id'],l['id'],{'quote':'Cita','comment':'PRIVADA ELEGIDA','shareWithTutor':False,'courseVersion':c['version']})
server.event('annotation',c['id'],l['id'],{'quote':'Cita pública','comment':'COMPARTIDA EXCLUIDA','shareWithTutor':True,'courseVersion':c['version']})
server.library().save_note({'title':'Apunte de contexto','folder':'Prueba','content':'GENERAL EXCLUIDO','shared':False,'documentId':None,'page':None,'anchors':[{'id':'ctx-anchor','scope':'general','documentId':None,'page':None,'sha256':None,'quote':'','comment':'COMENTARIO ELEGIDO'}]})
def fake(path,body=None,authenticated=True):
    payload=json.loads(body['messages'][1]['content'])
    return {'choices':[{'message':{'content':json.dumps({'reply':'Ayuda con el contexto elegido.','status':'pending','evidence':[],'gaps':[],'receivedContext':payload})}}]}
server.openrouter=fake
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`;
 const service=spawn('python3',['-c',script],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:['ignore','pipe','pipe']});let stderr='',browser;service.stderr.on('data',d=>stderr+=d);
 const base=`http://127.0.0.1:${port}`,getState=()=>localJSON(base+'/api/state');
 try{
  for(let i=0;i<100;i++){try{if(await getState())break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
  const initial=await getState(),doc=initial.library.documents[0];
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});const page=await browser.newPage({viewport:{width:1400,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('.activity');await page.keyboard.type('gx');await page.waitForSelector('.context-manager input[type=search]');
  await page.getByRole('checkbox',{name:/Historial reciente/}).uncheck();await page.getByRole('checkbox',{name:'Páginas citadas por la lección',exact:true}).uncheck();
  await page.locator('.context-section>summary').filter({hasText:'Anotaciones de estudio'}).click();
  const privateBox=page.getByRole('checkbox',{name:/PRIVADA ELEGIDA/}),publicBox=page.getByRole('checkbox',{name:/COMPARTIDA EXCLUIDA/});assert.equal(await privateBox.isChecked(),false);assert(await publicBox.isChecked());await privateBox.check();await publicBox.uncheck();
  await page.locator('.context-section>summary').filter({hasText:'Apuntes y anotaciones de lectura'}).click();await page.locator('.context-section details>summary').filter({hasText:'Apunte de contexto'}).click();await page.getByRole('checkbox',{name:/COMENTARIO ELEGIDO/}).check();
  const source=page.locator('.context-source').filter({hasText:doc.title});await source.locator('input[type=checkbox]').check();await source.locator('select').selectOption('pages');await source.locator('input[type=text]').fill('2');
  await page.getByRole('button',{name:'＋ Pegar fuente de texto',exact:true}).click();await page.getByLabel('Título de la fuente de texto',{exact:true}).fill('Fuente manual');await page.getByLabel('Contenido de la fuente de texto',{exact:true}).fill('TEXTO DE REFERENCIA ELEGIDO');
  await page.locator('summary').filter({hasText:'Vista previa de la próxima consulta'}).click();await page.getByRole('button',{name:'Previsualizar contexto',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.context-preview')?.textContent.includes('Fuente manual'));
  await page.getByRole('button',{name:'Guardar contexto',exact:true}).click();await page.waitForSelector('.context-manager',{state:'detached'});
  let state=await getState();assert.equal(state.library.tutorContexts.length,1);assert.equal(state.library.tutorContexts[0].selection.includeHistory,false);assert.equal(state.library.notes[0].shared,false);
  await page.keyboard.type('gt');await page.waitForSelector('#tutor-panel',{state:'visible'});await page.locator('#tutor-panel .cm-content').fill('Una consulta con mi contexto');await page.getByRole('button',{name:'Conversar ↗',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#tutor-chat .message.assistant'));await page.evaluate(()=>WorkspaceKeys.closePanels());await page.locator('#main').focus();await page.keyboard.press(':');await page.getByRole('button',{name:'Contexto y evidencia de la última respuesta',exact:true}).click();await page.waitForSelector('.context-used');
  state=await getState();const received=state.events.filter(e=>e.kind==='tutor_reply').at(-1).data.receivedContext,serialized=JSON.stringify(received);
  assert(serialized.includes('PRIVADA ELEGIDA'));assert(serialized.includes('COMENTARIO ELEGIDO'));assert(serialized.includes('TEXTO DE REFERENCIA ELEGIDO'));assert(!serialized.includes('COMPARTIDA EXCLUIDA'));assert(!serialized.includes('GENERAL EXCLUIDO'));assert.deepEqual(received.sourcePages.map(p=>p.page),[2]);
  await page.keyboard.press('Escape');await page.locator('#main').focus();await page.keyboard.type('gx');await page.waitForSelector('.context-manager input[type=search]');await page.locator('.context-section>summary').filter({hasText:'Anotaciones de estudio'}).click();await privateBox.uncheck();
  await page.locator('.context-source').filter({hasText:doc.title}).locator('input[type=checkbox]').uncheck();
  const pdf=path.join(data,'fuente-adjunta.pdf');fs.writeFileSync(pdf,fixturePDF());
  const chooser=page.waitForEvent('filechooser');await page.getByRole('button',{name:'＋ Adjuntar fuente PDF',exact:true}).click();await(await chooser).setFiles(pdf);await page.waitForFunction(()=>document.querySelector('.context-preview')?.textContent.includes('Fuente adjuntada'));
  await page.screenshot({path:path.join(data,'contexto-desktop.png')});
  await page.getByRole('button',{name:'Guardar contexto',exact:true}).click();await page.waitForSelector('.context-manager',{state:'detached'});state=await getState();assert.equal(state.library.tutorContexts[0].revision,2);assert.equal(state.library.tutorContexts[0].selection.annotationIds.length,0);assert(state.library.documents.some(d=>d.title==='fuente-adjunta.pdf'));
  await page.reload();await page.waitForSelector('.activity');await page.locator('#global-command-button').focus();await page.keyboard.type('gx');await page.waitForSelector('.context-manager input[type=search]');assert.equal(await page.getByRole('checkbox',{name:/Historial reciente/}).isChecked(),false);
  await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(data,'contexto-mobile.png')});
  // Closing must not steal a newer focus and discard the next navigation prefix.
  await page.evaluate(()=>{document.querySelector('.context-manager').close();document.getElementById('main').focus({preventScroll:true});});await page.waitForSelector('.context-manager',{state:'detached'});assert(await page.evaluate(()=>document.activeElement.id==='main'),'Context close must preserve a newer focus');await page.setViewportSize({width:1400,height:1000});
  await page.keyboard.type('gn');await page.waitForSelector('#class-note-content',{state:'attached'});await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'Apunte de contexto'}).click();await page.keyboard.type('gx');await page.waitForSelector('.context-manager input[type=search]');await page.getByRole('checkbox',{name:'Apunte o comentario actual',exact:true}).uncheck();await page.getByRole('button',{name:'Guardar contexto',exact:true}).click();await page.waitForSelector('.context-manager',{state:'detached'});
  state=await getState();assert.equal(state.library.tutorContexts.length,2);assert.equal(state.library.tutorContexts.find(c=>c.target.kind==='note').selection.includeBaseNote,false);
  assert.deepEqual(errors,[]);console.log('OK: context manager by keyboard, explicit private annotation/note selection, source pages and pasted text, exact captured provider context, PDF upload, persistent unchecking, notes profile, and mobile. No external model calls.');
 }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

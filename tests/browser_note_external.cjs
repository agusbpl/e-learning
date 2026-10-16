// Edición externa del Markdown original: visible en Glosa, nunca se pisa sin avisar.
// Usa una carpeta temporal (LEARNING_DATA_DIR), jamás los apuntes del estudiante.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
(async()=>{
  const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-note-ext-')),listener=net.createServer();
  await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
  const service=spawn('python3',['-c',`import json,server
server.init_db()
doc={'id':'fixture-ext','title':'PDF de prueba','sha256':'0'*64,'pages':3,'storage':'upload','filename':'fixture-ext.pdf'}
with server.connect() as conn: conn.execute('INSERT INTO documents VALUES(?,?)',(doc['id'],json.dumps(doc)))
server.library().save_note({'title':'externo','folder':'','content':'Texto inicial del archivo','shared':False,'documentId':None,'page':None,'anchors':[]})
server.library().save_note({'title':'con pagina','folder':'','content':'General de la pagina','shared':False,'documentId':doc['id'],'page':1,'writingScope':'page','pageNotes':{doc['id']:{'1':'Nota visible de la pagina uno'}},'anchors':[]})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port)},stdio:['ignore','ignore','pipe']});
  let browser,stderr='';service.stderr.on('data',d=>stderr+=d);const base=`http://127.0.0.1:${port}`;
  const errors=[];
  const snapshot=async()=>await(await fetch(base+'/api/state')).json();
  const notesRoot=path.join(data,'Apuntes');
  try{
    for(let i=0;i<100;i++){try{await snapshot();break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
    // El texto de cada página vive visible en el cuerpo, antes de la estructura auxiliar.
    const pageFile=path.join(notesRoot,'con pagina.md'),pageMarkdown=fs.readFileSync(pageFile,'utf8');
    assert(pageMarkdown.includes('<!-- glosa:page id="fixture-ext" page="1" -->'),pageMarkdown);
    const pageStart=pageMarkdown.indexOf('<!-- glosa:page id="fixture-ext" page="1" -->');
    const pageEnd=pageMarkdown.indexOf('<!-- /glosa:page -->',pageStart);
    assert(pageStart>=0&&pageEnd>pageStart,pageMarkdown);
    assert(pageMarkdown.slice(pageStart,pageEnd).includes('Nota visible de la pagina uno'),'el texto de página es visible en el cuerpo, no JSON');
    browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
    const page=await browser.newPage({viewport:{width:1100,height:850}});page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));await page.goto(base);await page.waitForSelector('#rooms-button');await page.keyboard.type('gn');await page.waitForFunction(()=>document.body.dataset.workspaceView==='notes');await page.evaluate(()=>ClassNotes.openList());await page.locator('.class-note-link').filter({hasText:'externo'}).click();
    const preview=page.locator('#note-markdown-preview'),input=page.locator('#class-note-content');
    await preview.waitFor({state:'visible'});
    const file=path.join(notesRoot,'externo.md'),before=fs.readFileSync(file,'utf8');
    assert(before.includes('Texto inicial del archivo'));
    // 1) Edición externa del archivo. Guardar sin snapshot debe conflictuar, no pisar.
    fs.writeFileSync(file,before.replace('Texto inicial del archivo','Texto editado por fuera'));
    await page.keyboard.press('Control+s');
    await page.waitForFunction(()=>document.getElementById('note-save-error')?.textContent.startsWith('Sin guardar'));
    const afterSave=fs.readFileSync(file,'utf8');
    assert(afterSave.includes('Texto editado por fuera'),'el archivo conserva la edición externa');
    assert(!afterSave.includes('Texto inicial del archivo'),'no se reescribió con la copia vieja');
    // 2) Al refrescar, la edición externa se ve y el apunte activo se recarga.
    await page.evaluate(()=>ClassNotes.refresh());
    await page.waitForFunction(()=>document.getElementById('note-markdown-preview')?.textContent.includes('Texto editado por fuera'));
    // 3) Un guardado fallido nunca destruye el borrador local (ruta de error determinista).
    await page.route('**/api/notes',route=>route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({error:'Fallo temporal de prueba'})}));
    await page.evaluate(()=>{const t=document.getElementById('class-note-content');t.value=t.value+' borrador local';t.dispatchEvent(new Event('input',{bubbles:true}));});
    await page.waitForSelector('#note-save-error',{state:'visible'});
    assert((await input.inputValue()).includes('borrador local'),'el borrador local se conserva');
    assert(fs.readFileSync(file,'utf8').includes('Texto editado por fuera'),'un guardado fallido no toca el archivo');
    await page.unroute('**/api/notes');
    assert.deepEqual(errors,[]);
    console.log('OK: edición externa del .md visible, guardado sin snapshot en conflicto sin sobreescritura, texto de página visible en el cuerpo y borrador local preservado.');
  }catch(error){if(browser)console.error(await browser.contexts()[0]?.pages()[0]?.evaluate(()=>({preview:document.getElementById('note-markdown-preview')?.textContent?.slice(0,120),error:document.getElementById('note-save-error')?.textContent,source:document.getElementById('class-note-content')?.value?.slice(-120),title:document.title,body:document.body?.className})));
    console.error('PAGE ERRORS',errors);console.error('STDERR',stderr.slice(-2000));throw error;}finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1);});

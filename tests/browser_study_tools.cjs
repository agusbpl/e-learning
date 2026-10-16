// StudyTools against the real Glosa app: wikilinks/backlinks in both
// directions, template insertion without losing the draft, note-level study
// properties, filters and reload. Disposable database; no courses, no model
// calls, no real student data. The module loads through index.html and is served
// by server.py, so the test exercises the published integration.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');

(async()=>{
  const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-study-tools-')),listener=net.createServer();
  await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
  const service=spawn('python3',['-c',`import server
server.init_db()
save=server.library().save_note
save({'id':'note-derivadas','title':'Derivadas','folder':'','content':'# Derivadas\\n\\nConcepto base.','contentFormat':'markdown','shared':False,'documentId':None,'page':None,'anchors':[]})
save({'id':'note-integrales','title':'Integrales','folder':'','content':'# Integrales\\n\\nVer [[Derivadas]] para el repaso.','contentFormat':'markdown','shared':False,'documentId':None,'page':None,'anchors':[]})
save({'id':'note-suelta','title':'Suelta','folder':'','content':'# Suelta\\n\\nSin materia ni unidad.','contentFormat':'markdown','shared':False,'documentId':None,'page':None,'anchors':[]})
server.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port),OPENROUTER_API_KEY:'',FREELLMAPI_API_KEY:'',INTERN_API_KEY:''},stdio:['ignore','ignore','pipe']});
  let browser,stderr='';service.stderr.on('data',d=>stderr+=d);
  const base=`http://127.0.0.1:${port}`,snapshot=async()=>await(await fetch(base+'/api/state')).json();
  try{
    for(let i=0;i<100;i++){try{await snapshot();break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
    browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
    const context=await browser.newContext({viewport:{width:1280,height:900}});
    await context.addInitScript(()=>{localStorage.setItem('glosa-active-room','local');localStorage.setItem('class-note-active-draft','note-derivadas');});
    const page=await context.newPage(),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error'&&!/Failed to load resource/.test(m.text()))errors.push(m.text());});

    const enterNotes=async()=>{
      await page.waitForFunction(()=>document.querySelector('#main')&&document.querySelector('#main').textContent.trim().length>0);
      await page.evaluate(()=>window.WorkspaceKeys.go('notes'));
      await page.waitForSelector('.class-notes-layout');
      await page.waitForSelector('#study-tools-panel');
    };
    const openTab=async name=>{
      const panel=page.locator('#study-tools-panel');
      await panel.waitFor({state:'visible'});
      if(!(await panel.evaluate(el=>el.open)))await panel.locator('summary').click();
      await panel.getByRole('button',{name,exact:true}).first().click();
      await page.waitForTimeout(60);
    };
    const clickLink=async name=>{
      const panel=page.locator('#study-tools-panel');
      if(!(await panel.evaluate(el=>el.open)))await panel.locator('summary').click();
      await panel.getByRole('button',{name,exact:true}).first().click();
    };
    const waitFor=async(fn,label)=>{for(let i=0;i<80;i++){if(await fn())return;await page.waitForTimeout(100);}throw Error('timeout esperando: '+label);};
    const note=async id=>(await snapshot()).library.notes.find(n=>n.id===id);

    await page.goto(base);
    const baseline=await snapshot();
    await enterNotes();

    // La navegación real usa `state`/`api` léxicos: window.state no existe.
    assert.equal(await page.evaluate(()=>typeof window.state),'undefined');
    assert.ok(await page.evaluate(()=>typeof window.StudyTools==='object'),'el módulo se carga');

    // 1. Referencias inversas y navegación A -> B.
    await openTab('Referencias');
    const backlink=page.locator('#study-tools-panel').getByRole('button',{name:'Integrales',exact:true});
    assert.equal(await backlink.count(),1,'Derivadas debe ver que Integrales la enlaza');
    await backlink.click();
    await waitFor(async()=>await page.evaluate(()=>document.getElementById('note-name-button')?.textContent==='Integrales'),'abrir Integrales');

    // 2. Editar B y navegar B -> A: el borrador se conserva (flush real).
    await page.evaluate(()=>{const t=document.getElementById('class-note-content');t.value=t.value+'\n\nMARCA-B';t.dispatchEvent(new Event('input',{bubbles:true}));});
    await openTab('Referencias');
    await clickLink('Derivadas');
    await waitFor(async()=>await page.evaluate(()=>document.getElementById('note-name-button')?.textContent==='Derivadas'),'abrir Derivadas');
    await waitFor(async()=>{const b=await note('note-integrales');return b.content.includes('MARCA-B');},'guardar el borrador de Integrales');

    // 3. Volver a B: el borrador conservado reaparece en el editor.
    await openTab('Referencias');
    await clickLink('Integrales');
    await waitFor(async()=>await page.evaluate(()=>document.getElementById('note-name-button')?.textContent==='Integrales'),'volver a Integrales');
    assert.ok((await page.locator('#class-note-content').inputValue()).includes('MARCA-B'),'el borrador conservado se muestra');

    // 4. Propiedades de estudio sobre A (sin curso, con estado booleano correcto).
    await openTab('Referencias');
    await clickLink('Derivadas');
    await waitFor(async()=>await page.evaluate(()=>document.getElementById('note-name-button')?.textContent==='Derivadas'),'volver a Derivadas');
    await openTab('Propiedades');
    assert.equal(await page.locator('input[data-study-field="needsPractice"]').isChecked(),false,'una nota sin marca se muestra sin marcar');
    await page.locator('input[data-study-field="materia"]').fill('Análisis matemático');
    await page.locator('input[data-study-field="materia"]').dispatchEvent('change');
    await waitFor(async()=>(await note('note-derivadas')).study?.materia==='Análisis matemático','guardar materia');
    await page.locator('input[data-study-field="unidad"]').fill('Unidad 3');
    await page.locator('input[data-study-field="unidad"]').dispatchEvent('change');
    await waitFor(async()=>(await note('note-derivadas')).study?.unidad==='Unidad 3','guardar unidad');
    await page.locator('input[data-study-field="parcialDate"]').fill('2026-11-15');
    await page.locator('input[data-study-field="parcialDate"]').dispatchEvent('change');
    await waitFor(async()=>(await note('note-derivadas')).study?.parcialDate==='2026-11-15','guardar fecha');
    await page.locator('input[data-study-field="needsPractice"]').check();
    await waitFor(async()=>(await note('note-derivadas')).study?.needsPractice===true,'guardar repaso');
    assert.equal(await page.locator('input[data-study-field="needsPractice"]').isChecked(),true,'la casilla conserva su estado tras re-render');

    // 5. Insertar ficha sin perder el borrador.
    await page.evaluate(()=>{const t=document.getElementById('class-note-content');t.value=t.value+'\n\nBORRADOR-A';t.dispatchEvent(new Event('input',{bubbles:true}));});
    await openTab('Ficha');
    await page.locator('.study-inline-form input').fill('Regla de la cadena');
    await page.getByRole('button',{name:'Insertar ficha',exact:true}).click();
    await waitFor(async()=>{const n=await note('note-derivadas');return n.content.includes('## Ficha: Regla de la cadena')&&n.content.includes('BORRADOR-A');},'insertar ficha sin perder borrador');

    // 6. Errores de parcial como metadata (no como feedback de curso).
    await openTab('Errores');
    await page.locator('input[aria-label="Concepto o ejercicio"]').fill('Regla de la cadena');
    await page.locator('textarea[aria-label="Descripción del error"]').fill('Olvidé la derivada interna.');
    await page.locator('textarea[aria-label="Corrección"]').fill('Multiplicar por la derivada de la función interna.');
    await page.getByRole('button',{name:'Registrar error',exact:true}).click();
    await waitFor(async()=>(await note('note-derivadas')).study?.errors?.length===1,'registrar error');
    const afterErrors=await snapshot();
    assert.equal(afterErrors.library.notes.find(n=>n.id==='note-derivadas').study.errors[0].errorType,'concepto');
    assert.equal(afterErrors.events.length,baseline.events.length,'no se crea feedback de curso ni evaluación');
    assert.equal(afterErrors.courses.length,baseline.courses.length,'no se inventa un curso');

    // 7. Filtros: vacíos incluyen notas sin propiedades; con materia filtran.
    await openTab('Filtros');
    await page.getByRole('button',{name:'Aplicar filtros',exact:true}).click();
    await page.waitForSelector('.study-filter-results');
    assert.equal(await page.locator('.study-filter-result').count(),3,'filtros vacíos incluyen todas, también sin propiedades');
    await page.locator('select[aria-label="Filtrar por materia"]').selectOption('Análisis matemático');
    await page.getByRole('button',{name:'Aplicar filtros',exact:true}).click();
    await page.waitForFunction(()=>document.querySelectorAll('.study-filter-result').length===1);
    assert.ok((await page.locator('.study-filter-result').first().textContent()).includes('Derivadas'));

    // 7b. Un apunte nuevo, todavía sin texto: elegir una propiedad la persiste
    // de verdad (el adaptador fuerza el guardado del apunte nuevo).
    await page.evaluate(()=>ClassNotes.create());
    await page.waitForSelector('#study-tools-panel');
    await openTab('Propiedades');
    await page.locator('input[data-study-field="materia"]').fill('Física');
    await page.locator('input[data-study-field="materia"]').dispatchEvent('change');
    const nuevoId=await page.evaluate(()=>ClassNotes.currentId());
    await waitFor(async()=>{const n=await note(nuevoId);return n&&n.study?.materia==='Física';},'propiedad de apunte nuevo sin texto');

    // 8. Recargar: la metadata persiste y vuelve a mostrarse/filtrarse.
    const derivativeNote=await note('note-derivadas');
    assert.ok(derivativeNote.revision>1,'la nota conserva su id y avanza de revisión');
    await page.reload();
    await enterNotes();
    await openTab('Propiedades');
    assert.equal(await page.locator('input[data-study-field="materia"]').inputValue(),'Análisis matemático');
    assert.equal(await page.locator('input[data-study-field="unidad"]').inputValue(),'Unidad 3');
    assert.equal(await page.locator('input[data-study-field="parcialDate"]').inputValue(),'2026-11-15');
    assert.equal(await page.locator('input[data-study-field="needsPractice"]').isChecked(),true);
    await openTab('Filtros');
    await page.locator('select[aria-label="Filtrar por materia"]').selectOption('Análisis matemático');
    await page.getByRole('button',{name:'Aplicar filtros',exact:true}).click();
    await page.waitForFunction(()=>document.querySelectorAll('.study-filter-result').length===1);

    assert.deepEqual(errors,[]);
    console.log('OK: referencias en ambos sentidos con navegación que conserva el borrador; plantilla sin perder texto; propiedades de estudio booleanas y persistentes sin curso; errores como metadata; filtros que incluyen notas sin propiedades; recarga.');
  }catch(error){
    if(browser)console.error(await browser.contexts()[0]?.pages()[0]?.evaluate(()=>({notice:document.getElementById('notice')?.textContent,view:document.querySelector('.workspace')?.className,panel:!!document.getElementById('study-tools-panel'),active:document.querySelector('.class-note-link.active')?.textContent})).catch(()=>null));
    throw error;
  }finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exit(1);});

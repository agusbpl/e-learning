// Regresión del bug de usuario: al quitar o recolorear un resaltado la lectura
// no debe saltar arriba. Cubre texto de lección, cuaderno y PDF con una lección
// larga (24 bloques) para que la página sea realmente desplazable. Fixture
// desechable, tutor sintético, sin llamadas a modelos.
const {chromium}=require('playwright');
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict'),{spawn}=require('child_process');
const post=(url,body)=>fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(async r=>{const d=await r.json();if(!r.ok)throw Error(d.error||('HTTP '+r.status));return d;});
(async()=>{
 const root=path.resolve(__dirname,'..'),data=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-hlscroll-')),socket=net.createServer();await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
 const service=spawn('python3',['-c',`import json,server
server.init_db()
with server.connect() as c:
    row=c.execute("SELECT id,body FROM courses").fetchone()
    course=json.loads(row["body"]);lesson=course["lessons"][0]
    for i in range(24):
        lesson["blocks"].append({"id":"scroll-%02d"%i,"title":"Bloque de lectura %02d"%i,"text":("Fragmento %02d de lectura extensa. "%i)*6})
    c.execute("UPDATE courses SET body=? WHERE id=?",(json.dumps(course,ensure_ascii=False),row["id"]))
server.library().save_note({"id":"pdf-scroll","title":"PDF con scroll","folder":"","content":"","shared":False,"documentId":"fixture-pdf","page":1,"writingScope":"page","pageNotes":{"fixture-pdf":{"1":""}},"anchors":[]})
server.ThreadingHTTPServer(("127.0.0.1",server.PORT),server.Handler).serve_forever()
`],{cwd:root,env:{...process.env,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port),OPENROUTER_API_KEY:'',FREELLMAPI_API_KEY:'',INTERN_API_KEY:''},stdio:['ignore','ignore','pipe']});
 let browser,stderr='';service.stderr.on('data',d=>stderr+=d);const base=`http://127.0.0.1:${port}`,snapshot=async()=>await(await fetch(base+'/api/state')).json();
 try{
  for(let i=0;i<100;i++){try{await snapshot();break;}catch{}await new Promise(r=>setTimeout(r,100));if(i===99)throw Error(stderr);}
  // Resaltados creados por API directa: la lección larga necesita muchos para
  // poder desplazar tanto la lectura como el cuaderno.
  const initial=await snapshot(),course=initial.courses[0],lesson=course.lessons[0];
  const blocks=lesson.blocks.filter(b=>/^scroll-/.test(b.id));assert(blocks.length>=24,'the long lesson must be installed');
  for(const block of blocks)await post(base+'/api/event',{kind:'annotation',courseId:course.id,lessonId:lesson.id,data:{type:'highlight',blockId:block.id,start:0,end:18,quote:block.text.slice(0,18),comment:'',shareWithTutor:false}});

  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath()});
  const page=await browser.newPage({viewport:{width:1200,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>localStorage.setItem('glosa-active-room','local'));
  await page.goto(base);await page.waitForSelector('.theory');
  const scrollY=()=>page.evaluate(()=>window.scrollY);
  const scrollBlockIntoView=id=>page.evaluate(id=>{const el=document.querySelector(`[data-block-id="${id}"]`);el.scrollIntoView({block:'center'});window.__probe=el;},id);
  const sameBlockNode=id=>page.evaluate(id=>window.__probe===document.querySelector(`[data-block-id="${id}"]`),id);

  // 1. Quitar un resaltado muy abajo conserva la posición, el foco y no rehace la página.
  await scrollBlockIntoView('scroll-20');
  const textScroll=await scrollY();assert(textScroll>600,`the reading view must be scrolled far down, got ${textScroll}`);
  const mark20='[data-block-id="scroll-20"] mark[data-annotation-id]';await page.waitForSelector(mark20);
  const removedId=await page.locator(mark20).first().getAttribute('data-annotation-id');
  await page.locator(mark20).first().click();await page.getByRole('button',{name:'Quitar resaltado',exact:true}).click();
  await page.waitForFunction(sel=>!document.querySelector(sel),mark20);
  const afterRemoveText=await scrollY();
  assert(Math.abs(afterRemoveText-textScroll)<=4,`removing a highlight moved the reading from ${textScroll} to ${afterRemoveText}`);
  assert(await sameBlockNode('scroll-20'),'removing a highlight must not rebuild the lesson');
  assert((await page.locator('[data-block-id="scroll-20"]').textContent()).includes('Fragmento 20 de lectura extensa'),'the highlighted text must survive as plain text');
  assert.equal(await page.evaluate(()=>document.activeElement?.dataset?.blockId),'scroll-20','focus must stay in the same block, not jump away');
  assert.equal((await snapshot()).events.find(e=>e.id===removedId).data.removed,true,'the removal must persist on the server');

  // 2. Recolorear un resaltado también conserva la posición y el nodo.
  await scrollBlockIntoView('scroll-22');
  const colorScroll=await scrollY();assert(colorScroll>600,'the reading view must still be scrolled down');
  await page.locator('[data-block-id="scroll-22"] mark').first().click();
  await page.getByRole('button',{name:'Color Verde',exact:true}).click();
  await page.waitForSelector('[data-block-id="scroll-22"] mark[data-color=green]');
  const afterColorText=await scrollY();
  assert(Math.abs(afterColorText-colorScroll)<=4,`recolouring moved the reading from ${colorScroll} to ${afterColorText}`);
  assert(await sameBlockNode('scroll-22'),'recolouring must not rebuild the lesson');
  assert.equal((await snapshot()).events.find(e=>e.data.blockId==='scroll-22').data.color,'green','the colour change must persist on the server');

  // 3. Teclado: Enter abre las acciones y Escape devuelve el foco al resaltado.
  await page.locator('[data-block-id="scroll-22"] mark').first().focus();
  await page.keyboard.press('Enter');await page.locator('.reading-highlight-actions').waitFor({state:'visible'});
  await page.keyboard.press('Escape');await page.waitForSelector('.reading-highlight-actions',{state:'detached'});
  assert(await page.evaluate(()=>document.activeElement?.matches?.('mark[data-annotation-id]')),'Escape must return focus to the highlight');

  // 4. Cuaderno: recolorear y quitar en una lista larga conserva la posición y el nodo.
  await page.evaluate(()=>WorkspaceKeys.go('notebook'));await page.waitForSelector('.notebook-item');
  await page.evaluate(()=>{const items=[...document.querySelectorAll('.notebook-item')];items[12].scrollIntoView({block:'center'});window.__probe=items[12];window.__nbId=items[12].dataset.annotationId;});
  const notebookScroll=await scrollY();assert(notebookScroll>200,`the notebook must be scrolled, got ${notebookScroll}`);
  const nbId=await page.evaluate(()=>window.__nbId);
  await page.locator('.notebook-item').nth(12).locator('button[aria-label="Color Azul"]').click();
  await page.waitForFunction(id=>document.querySelector(`.notebook-item[data-annotation-id="${id}"] button[aria-label="Color Azul"][aria-pressed="true"]`),nbId);
  const afterColorNotebook=await scrollY();
  assert(Math.abs(afterColorNotebook-notebookScroll)<=6,`recolouring in the notebook moved the list from ${notebookScroll} to ${afterColorNotebook}`);
  assert(await page.evaluate(id=>window.__probe===document.querySelector(`.notebook-item[data-annotation-id="${id}"]`),nbId),'recolouring must not rebuild the notebook');
  await page.locator('.notebook-item').nth(12).getByRole('button',{name:'Quitar resaltado',exact:true}).click();
  await page.waitForFunction(id=>!document.querySelector(`.notebook-item[data-annotation-id="${id}"]`),nbId);
  const afterRemoveNotebook=await scrollY();
  assert(afterRemoveNotebook>100,`removing in the notebook must not jump to the top, got ${afterRemoveNotebook}`);

  // 5. PDF: quitar un resaltado conserva el desplazamiento y no rehace la página.
  await page.evaluate(()=>WorkspaceKeys.go('notes'));
  await page.waitForFunction(()=>document.querySelector('.notes-sidebar'));
  await page.evaluate(()=>ClassNotes.openList());
  await page.locator('.class-note-link').filter({hasText:'PDF con scroll'}).click();
  await page.waitForFunction(()=>document.getElementById('pdf-loading')?.hidden===true);
  await page.locator('.textLayer').first().evaluate(el=>{const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),node=walker.nextNode(),range=document.createRange();range.setStart(node,0);range.setEnd(node,Math.min(node.length,12));getSelection().removeAllRanges();getSelection().addRange(range);el.dispatchEvent(new MouseEvent('mouseup',{bubbles:true}));});
  await page.waitForSelector('.pdf-highlight');
  // La barra de acciones se cierra ante cualquier scroll: dejar asentar el
  // desplazamiento antes de abrirla, como haría una persona al desplazarse y luego hacer clic.
  await page.evaluate(()=>new Promise(resolve=>{const scroller=document.getElementById('pdf-scroll');scroller.scrollTop=scroller.scrollHeight;window.__pdfNode=document.getElementById('pdf-page-canvas');let frames=0;const step=()=>{if(++frames>=4)resolve();else requestAnimationFrame(step);};requestAnimationFrame(step);}));
  const pdfScroll=await page.evaluate(()=>document.getElementById('pdf-scroll').scrollTop);assert(pdfScroll>0,`the PDF must scroll for this regression, got ${pdfScroll}`);
  await page.locator('.pdf-highlight').first().evaluate(el=>el.click());
  await page.locator('.reading-highlight-actions').waitFor({state:'visible'});
  await page.getByRole('button',{name:'Quitar resaltado',exact:true}).click();
  await page.waitForFunction(()=>!document.querySelector('.pdf-highlight'));
  const afterPdfRemove=await page.evaluate(()=>document.getElementById('pdf-scroll').scrollTop);
  assert(Math.abs(afterPdfRemove-pdfScroll)<=8,`removing a PDF highlight moved the PDF from ${pdfScroll} to ${afterPdfRemove}`);
  assert(await page.evaluate(()=>window.__pdfNode===document.getElementById('pdf-page-canvas')),'removing a PDF highlight must not rebuild the document page');
  assert.equal((await snapshot()).library.notes.find(n=>n.id==='pdf-scroll').anchors.length,0,'the PDF removal must persist on the server');

  assert.deepEqual(errors,[]);
  console.log('OK: quitar o recolorear un resaltado conserva la posición de lectura, el foco y no rehace la página (lección larga, cuaderno y PDF).');
 }catch(error){if(browser)console.error(await browser.contexts()[0]?.pages()[0]?.evaluate(()=>({view,focus:document.activeElement?.outerHTML?.slice(0,150),notice:document.getElementById('notice')?.textContent,dialogs:[...document.querySelectorAll('dialog[open]')].map(d=>d.className||d.id)})).catch(()=>null));throw error;}finally{await browser?.close();service.kill();fs.rmSync(data,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exit(1);});

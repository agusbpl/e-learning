// New-browser onboarding, live folders, isolated notes and the quiet conversation.
let chromium;
try { ({chromium}=require('playwright')); } catch { ({chromium}=require('playwright-core')); }
const fs=require('fs'),os=require('os'),path=require('path'),net=require('net'),assert=require('assert/strict');
const {spawn}=require('child_process');
(async()=>{
 const root=path.resolve(__dirname,'..'),temporary=fs.mkdtempSync(path.join(os.tmpdir(),'glosa-onboarding-')),data=path.join(temporary,'data');
 const listener=net.createServer();await new Promise(resolve=>listener.listen(0,'127.0.0.1',resolve));const port=listener.address().port;await new Promise(resolve=>listener.close(resolve));
 const base=`http://localhost:${port}`;
 const code=`import json,server\nserver.init_db()\nserver.KEY='temporary-test-key'\nserver.openrouter=lambda *args,**kwargs: {'choices':[{'message':{'content':json.dumps({'reply':'Una glosa conserva una duda junto a su texto.','status':'pending','evidence':[],'gaps':[],'reason':'Conversación de prueba.','nextAction':'reinforce'})},'finish_reason':'stop'}]}\nserver.ThreadingHTTPServer(('127.0.0.1',server.PORT),server.Handler).serve_forever()\n`;
 // HOME is temporary and GLOSA_MARGEN_DIR is empty, so the visible Margen default
 // lives inside the fixture and `set_margen` still works. Never the real ~/Margen.
 const service=spawn('python3',['-c',code],{cwd:root,env:{...process.env,HOME:temporary,LEARNING_DATA_DIR:data,LEARNING_PORT:String(port),GLOSA_MARGEN_DIR:'',OPENROUTER_API_KEY:'',FREELLMAPI_API_KEY:'',INTERN_API_KEY:''},stdio:['ignore','ignore','pipe']});
 let browser,stderr='';service.stderr.on('data',chunk=>stderr+=chunk);
 const api=async(path,body,room='local')=>{const response=await fetch(base+path,{headers:{'Content-Type':'application/json','X-Glosa-Room':room},...(body?{method:'POST',body:JSON.stringify(body)}:{})});const result=await response.json();assert(response.ok,JSON.stringify(result));return result;};
 try{
  for(let n=0;n<100;n++){try{if((await fetch(base+'/api/state')).ok)break;}catch{}if(n===99)throw Error(stderr);await new Promise(resolve=>setTimeout(resolve,100));}
  const original=await api('/api/state');
  browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||chromium.executablePath(),args:['--disable-dev-shm-usage']});
  const page=await browser.newPage({viewport:{width:1366,height:860}}),errors=[];page.on('pageerror',error=>errors.push(error.message));
  let embedHeaders;await page.route('https://www.youtube-nocookie.com/embed/**',async route=>{embedHeaders=await route.request().allHeaders();await route.fulfill({contentType:'text/html',body:'<p>Petición del reproductor comprobada</p>'});});
  await page.goto(base);await page.waitForSelector('.activity');
  assert.equal(await page.evaluate(()=>GlosaRoom.id),'primer-trazo');assert.equal(await page.locator('h1').textContent(),'Un lugar para empezar');
  assert.equal((await api('/api/state',null,'primer-trazo')).courses.length,1);
  const embed=page.locator('iframe.video-frame');
  assert.equal(await embed.getAttribute('src'),'https://www.youtube-nocookie.com/embed/cAqEVoiqudI?start=0');
  assert.equal(await embed.getAttribute('referrerpolicy'),'strict-origin-when-cross-origin');
  await embed.scrollIntoViewIfNeeded();await expectHeaders();
  async function expectHeaders(){for(let n=0;n<100&&!embedHeaders;n++)await new Promise(resolve=>setTimeout(resolve,50));assert.equal(embedHeaders?.referer,base+'/');}
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.locator('#main').focus();await page.keyboard.type('gt');await page.waitForSelector('.tutor-open');
  for(const selector of ['.tutor-head','.tutor-intro','.tutor-bottom','#tutor-context-button','#chat-hint'])assert(!(await page.locator(selector).isVisible()),selector);
  await page.locator('#tutor-panel .cm-content').fill('¿Qué conserva una glosa?');await page.getByRole('button',{name:'Conversar ↗',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#tutor-chat').textContent.includes('Una glosa conserva una duda'));
  assert.equal(await page.locator('#send-chat').textContent(),'↑');assert.equal(await page.locator('#tutor-chat .message').count(),2);assert(!(await page.locator('#tutor-chat .message-label').first().isVisible()));
  const height=await page.locator('#tutor-panel .cm-content').evaluate(input=>input.getBoundingClientRect().height);assert(height<100);
  fs.mkdirSync(path.join(root,'output/qa'),{recursive:true});await page.screenshot({path:path.join(root,'output/qa/tutor-hoja-desktop.png')});
  await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const inputRect=await page.locator('#tutor-panel .cm-content').boundingBox();assert(inputRect.y+inputRect.height<=844);await page.screenshot({path:path.join(root,'output/qa/tutor-hoja-mobile.png')});
  await page.setViewportSize({width:1366,height:860});await page.keyboard.press('Escape');await page.locator('#main').focus();await page.keyboard.type('go');await page.waitForSelector('#rooms-dialog[open]');
  await page.locator('#pliego-title').fill('Mi pliego');await page.getByRole('button',{name:'Crear pliego',exact:true}).click();await page.waitForFunction(()=>GlosaRoom.id.startsWith('pliego-'));
  await page.waitForSelector('h1');assert.equal(await page.locator('h1').textContent(),'Mi pliego');const selected=await page.evaluate(()=>GlosaRoom.id);
  assert.deepEqual((await api('/api/state',null,selected)).courses,[]);
  await page.getByRole('button',{name:'Escribir un apunte',exact:true}).click();await page.waitForSelector('.note-editor');await page.evaluate(()=>ClassNotes.create());
  await page.locator('#note-markdown-preview .cm-content').fill('# Comprobación temporal\n\nTexto sintético');await page.keyboard.press('Escape');await page.evaluate(()=>ClassNotes.flush());
  let listing=await api('/api/rooms');const found=listing.pliegos.find(item=>item.id===selected);assert(found);assert(!fs.existsSync(path.join(data,'rooms.json')));
  const elsewhere=path.join(temporary,'otro-margen');fs.mkdirSync(elsewhere);fs.renameSync(found.path,path.join(elsewhere,path.basename(found.path)));
  await api('/api/margen',{folder:elsewhere});await page.reload();await page.waitForSelector('h1');assert.equal(await page.evaluate(()=>GlosaRoom.id),selected);
  const persisted=await api('/api/state',null,selected);assert.equal(persisted.library.notes[0].content,'# Comprobación temporal\n\nTexto sintético');
  await page.getByRole('button',{name:'Volver a Primer trazo',exact:true}).click();await page.waitForSelector('.activity');
  assert.equal((await api('/api/state',null,'primer-trazo')).library.notes.length,0);
  const current=await api('/api/state');for(const key of ['courses','events','library','settings','calendarEvents'])assert.deepEqual(current[key],original[key]);
  const media=await fetch(base+'/media/fixture-demo.mp4',{headers:{Range:'bytes=0-99'}});assert.equal(media.status,206);assert.equal((await media.arrayBuffer()).byteLength,100);assert(media.headers.get('content-range').startsWith('bytes 0-99/'));
  const invalid=await fetch(base+'/media/fixture-demo.mp4',{headers:{Range:'bytes=999999999-'}});assert.equal(invalid.status,416);
  await page.screenshot({path:path.join(root,'output/qa/primer-trazo-desktop.png'),fullPage:true});
  assert.deepEqual(errors,[]);console.log('OK: tutorial default, YouTube demo and Referer, quiet conversation, mobile composer, new empty pliego, notes in-place, moved folder discovered, local history untouched and video ranges. Temporary provider only.');
 }finally{await browser?.close();service.kill();await new Promise(resolve=>service.exitCode!==null?resolve():service.once('exit',resolve));fs.rmSync(temporary,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
